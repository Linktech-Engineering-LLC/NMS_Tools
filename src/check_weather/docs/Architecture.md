# Architecture — check_weather v2.0.0

**Part of:** NMS_Tools Monitoring Suite  
**Script:** `check_weather.py`  
**Author:** Leon McClatchey, Linktech Engineering LLC  
**License:** MIT  
**Requires:** Python 3.8+  
**Last Updated:** 2026-08-15

---

## Table of Contents

1. [Overview](#overview)
2. [High-Level Data Flow](#high-level-data-flow)
3. [Provider Architecture](#provider-architecture)
4. [Location Resolution](#location-resolution)
5. [Mode Architecture](#mode-architecture)
6. [Normalization](#normalization)
7. [Merge Logic](#merge-logic)
8. [Index Engine](#index-engine)
9. [Unit Conversion](#unit-conversion)
10. [Caching](#caching)
11. [Output Schema](#output-schema)
12. [Logging](#logging)
13. [PythonTools Dependencies](#pythontools-dependencies)
14. [Upcoming Features](#upcoming-features)

---

## Overview

`check_weather` is a deterministic, Nagios-compatible weather monitoring tool that is part of the
NMS_Tools suite. Version 2.2.0 replaces the legacy icon-classification pipeline — which depended on
`analyzer.py`, geometry-based SVG classification, and `recolor.py` — with a pluggable multi-provider
weather engine built on `PythonTools.weather`.

The new architecture:

- Separates weather fetching, normalization, and threshold evaluation into clean, independent layers
- Supports two pluggable providers (`nws`, `open-meteo`) each with per-mode fetch functions
- Introduces three distinct weather modes (`current`, `hourly`, `weekly`) and a combined `full` mode
- Produces dual-unit output (metric **and** imperial) in every mode
- Is fully cache-aware with separate stores and TTLs for weather data and resolved location data

---

## High-Level Data Flow

```
CLI args
    │
    ▼
build_parser()
    │  Validates: location input (exactly one), mode (mutually exclusive),
    │             provider (choices), Nagios-mode constraint
    ▼
resolve_location()
    │  ZIP  → Zippopotam.us
    │  City → Open-Meteo Geocoding API
    │  Lat/Lon → direct (no network call)
    │  Result cached 24 h; key = "{country}:{input.lower()}"
    ▼
get_timezone(lat, lon)          ← populates meta["timezone"]
    │
    ▼
fetch_weather()
    ├── load_weather_cache()          ← check for cached hit
    ├── register_providers()          ← populate WEATHER_PROVIDERS
    ├── [NWS only] resolve_nws_meta() ← grid, zone, office, station metadata
    ├── [NWS weekly/hourly] fetch_valid_nws_observation()
    ├── fetch_{mode}(lat, lon, timeout, meta)
    │       └── [weekly] fetch_hourly() + merge_daily_periods()
    │       └── [hourly] reorder_hourly_current_first()
    └── convert_units_mode_aware()    ← normalize + emit dual-unit fields
    │
    ▼
evaluate_weather()              ← current mode only
    │  bidirectional temperature + sequential simple thresholds
    │  hourly/weekly always return OK
    ▼
build_perfdata()                ← current/Nagios mode only
    │
    ▼
output_and_exit()
       ├── JSON    → serialize_for_json(payload)
       ├── Verbose → verbose_current / verbose_hourly / verbose_weekly
       ├── Quiet   → quiet_current / quiet_forecast
       └── Nagios  → nagios_output (current only)
```

---

## Provider Architecture

Providers are registered at startup by `register_providers()` from
`PythonTools.weather.providers`. After registration they are accessible through the
`WEATHER_PROVIDERS` dict imported from `PythonTools.weather`.

### Registry Contract

Each entry in `WEATHER_PROVIDERS` must supply:

| Key | Type | Description |
|-----|------|-------------|
| `supports` | `list[str]` | Modes served: any combination of `current`, `hourly`, `weekly` |
| `fetch_current` | callable | Fetch current conditions |
| `fetch_hourly` | callable | Fetch hourly forecast array |
| `fetch_weekly` | callable | Fetch 7-day forecast array |

All fetch callables share the same signature:

```python
fetch_fn(lat: float, lon: float, timeout: int, meta: dict) -> tuple[dict, str]
#                                                                    data   url
```

Provider is selected via `--provider {nws,open-meteo}`. Default: `nws`. The choice is validated at
parse time. There is no silent switching or cross-provider fallback.

### NWS (NOAA / National Weather Service)

| Property | Value |
|----------|-------|
| Flag value | `nws` |
| Default | Yes |
| Coverage | United States only |
| API key | Not required |
| Supports | `current`, `hourly`, `weekly` |

**Pre-fetch steps (NWS-specific):**

1. `resolve_nws_meta(lat, lon)` — resolves NWS grid point, forecast zone, office, and nearest
   observation station; result is merged into `meta`.
2. For `weekly` and `hourly` modes only: `fetch_valid_nws_observation(lat, lon, timeout, meta)` —
   retrieves the most recent valid station observation; result stored in `meta["cached_obs"]` and
   `meta["cached_station_id"]`.

### Open-Meteo

| Property | Value |
|----------|-------|
| Flag value | `open-meteo` |
| Default | No |
| Coverage | Global |
| API key | Not required |
| Endpoint | `api.open-meteo.com/v1/forecast` |
| Supports | `current`, `hourly`, `weekly` |

No pre-fetch steps. Open-Meteo requires no station metadata.

---

## Location Resolution

Exactly one location input is required; the parser raises `ValueError` if zero or more than one is
provided.

| Flag | Format | Example |
|------|--------|---------|
| `--zip` | 5-digit US ZIP | `67576` |
| `--city` | City, State | `"St John, KS"` |
| `--lat` / `--lon` | Decimal degrees | `38.003 -98.768` |
| `--location` | Free-form (auto-detected) | any of the above |

`--zip`, `--city`, and `--lat`/`--lon` are convenience aliases: the parser normalizes each into
`args.location` before passing it downstream.

**Resolution chain** inside `resolve_location(args)`:

```
validate_location_input(args.location, args.country)
    │
    ▼
load_location_from_cache(cache_key)  ← 24-hour TTL; return if hit
    │ miss
    ▼
PythonTools.location.resolve_location(original, country, timeout) → LocationInfo
    ├── ZIP code  → Zippopotam.us
    ├── City/State → Open-Meteo Geocoding API
    └── Lat/Lon   → direct (no network call)
    │
    ▼
normalize_city_name()     ← normalizes casing / formatting
format_resolved_name()    ← formats display string for payload["location"]
    │
    ▼
save_location_to_cache(cache_key, result)
```

Cache key format: `"{country}:{original_input.lower()}"`.

After resolution, `get_timezone(lat, lon)` from `PythonTools.datetime` populates
`meta["timezone"]`, which is required by `reorder_hourly_current_first()`.

---

## Mode Architecture

Four weather modes are available, selected by mutually exclusive flags:

| Flag | `weather_mode` value | Description |
|------|----------------------|-------------|
| *(none)* | `current` | Single-point current conditions — default |
| `--hourly` | `hourly` | 24-entry hourly forecast, starting from current hour |
| `--weekly` | `weekly` | 7-day daily forecast, enriched via merge |
| `--full` | `full` | Combined current + hourly + weekly |

The parser raises `ValueError` if more than one mode flag is set simultaneously.

Mode is resolved in `main()`:

```python
weather_mode = (
    "weekly" if weather_flags[WeatherFlagNames.WEEKLY] else
    "hourly" if weather_flags[WeatherFlagNames.HOURLY] else
    "full"   if weather_flags[WeatherFlagNames.FULL]   else
    "current"
)
```

**Constraints:**

- Nagios output (default mode, no `-v` / `--json`) only supports `current`. Using `--hourly`,
  `--weekly`, or `--full` without `-v` or `--json` raises `RuntimeError`.
- The weather cache key is mode-scoped — each mode maintains an independent cache entry.

**Output dispatch table:**

| Output format | `current` | `hourly` | `weekly` |
|---------------|-----------|----------|----------|
| Verbose | `verbose_current()` | `verbose_hourly()` | `verbose_weekly()` |
| JSON | unified payload | unified payload | unified payload |
| Quiet | `quiet_current()` | `quiet_forecast()` | `quiet_forecast()` |
| Nagios | `nagios_output()` | ✗ not supported | ✗ not supported |

---

## Normalization

All raw provider responses pass through `convert_units_mode_aware()` from `PythonTools.weather`
before being cached or returned.

```python
data = convert_units_mode_aware(live, units, mode, meta, logging_enabled, logger)
```

**Key behaviors:**

- Applied to live data immediately after a successful fetch
- Applied again to cached data on retrieval (raw data is what is stored, not pre-converted data)
- Mode-aware: operates on a flat dict for `current`; on `data["hours"][]` for `hourly`; on
  `data["days"][]` for `weekly`
- Always emits **both** metric and imperial variants for every numeric field, regardless of the
  `--units` setting
- `None`-valued fields are stripped from the final payload by `strip_none()` from `PythonTools.utils`
  before serialization

**Dual-unit field pairs produced:**

| Concept | Metric field | Imperial field |
|---------|-------------|----------------|
| Temperature | `temperature_c` | `temperature_f` |
| Apparent temperature | `apparent_temperature_c` | `apparent_temperature_f` |
| Dewpoint | `dewpoint_c` | `dewpoint_f` |
| Wind speed | `wind_kph` | `wind_mph` |
| Wind gust | `wind_gust_kph` | `wind_gust_mph` |
| Precipitation | `precip_mm` | `precip_in` |
| Daily high (weekly) | `temp_max_c` | `temp_max_f` |
| Daily low (weekly) | `temp_min_c` | `temp_min_f` |
| Wind max (weekly) | `wind_kph_max` | `wind_mph_max` |

**Unit-agnostic fields** (no conversion, present in all modes where applicable):
`humidity`, `cloudcover`, `pressure_msl`, `visibility_m`, `context`, `time`, `date`,
`precipitation_probability_max`.

---

## Merge Logic

### Weekly Mode — Daily + Hourly Enrichment

The weekly fetch alone returns only daily aggregate summaries. A second fetch provides the hourly
resolution needed to enrich each day:

```python
# Inside fetch_weather(), weekly branch:
hourly_fn = prov["fetch_hourly"]
hourly_live, _ = hourly_fn(lat, lon, timeout, meta)
live["days"] = merge_daily_periods(live["days"], hourly_live["hours"])
```

`merge_daily_periods(days, hours)` from `PythonTools.weather` correlates each hourly entry to its
parent calendar day and enriches each day dict with merged fields such as wind maximums,
precipitation accumulations, and a representative condition string.

### Hourly Mode — Current-First Reordering

```python
live["hours"] = reorder_hourly_current_first(live["hours"], meta["timezone"])
```

`reorder_hourly_current_first()` rotates the raw hours array — which starts at midnight — so that
index 0 is always the current hour. The result is always exactly 24 entries.

---

## Index Engine

Threshold evaluation runs **only in `current` mode**. `hourly`, `weekly`, and `full` always return
`(OK, "{mode} forecast retrieved")` without inspecting any values.

Entry point: `evaluate_weather(data, args) → (status: int, message: str)`

### Temperature — Bidirectional Evaluation

`evaluate_temperature(temp, args, unit)` auto-detects threshold direction from the relationship
between the supplied thresholds and the current temperature:

```
if both thresholds < current temp  →  cold mode  →  triggers when temp ≤ threshold
otherwise                          →  hot mode   →  triggers when temp ≥ threshold
```

This allows a single `--warning-temp` / `--critical-temp` pair to serve both freeze alerts and heat
alerts without additional flags.

### Simple Threshold Evaluation

`evaluate_simple(value, warn, crit, label) → (status, message) | None`

Applied to the following fields, using the unit variant selected by `--units`:

| Metric (imperial) | Metric (metric) | Threshold flags |
|-------------------|-----------------|-----------------|
| `wind_mph` | `wind_kph` | `--warning-wind` / `--critical-wind` |
| `wind_gust_mph` | `wind_gust_kph` | `--warning-gust` / `--critical-gust` |
| `humidity` | `humidity` | `--warning-humidity` / `--critical-humidity` |
| `precip_in` | `precip_mm` | `--warning-precip` / `--critical-precip` |
| `cloudcover` | `cloudcover` | `--warning-cloud` / `--critical-cloud` |

**Evaluation order (first match wins):**
temperature → wind → gust → humidity → precipitation → cloud cover

If no threshold is exceeded, `evaluate_weather()` falls through to `build_normal_message()` and
returns `OK`.

**Exit codes:**

| Constant | Integer | Meaning |
|----------|---------|---------|
| `OK` | `0` | All thresholds within bounds |
| `WARNING` | `1` | Warning threshold exceeded |
| `CRITICAL` | `2` | Critical threshold exceeded |
| `UNKNOWN` | `3` | Data unavailable or error |

---

## Unit Conversion

Selected by `--units {metric,imperial}` (default: `metric`).

The flag does **not** change which fields appear in the output — both unit variants are always
present in `data`. It controls three things:

1. **Index engine** — which unit field is compared against thresholds
2. **Perfdata** — which unit field supplies the numeric value
3. **Verbose / quiet formatters** — which unit field is displayed

Format helpers from `PythonTools.weather`:

| Helper | Purpose |
|--------|---------|
| `fmt_temp(data, key, units)` | Render temperature with unit suffix |
| `fmt_wind(data, key, units)` | Render wind speed with unit suffix |
| `fmt_precip(data, key, units)` | Render precipitation with unit suffix |
| `fmt_clouds(value)` | Render cloud cover as a percentage |

---

## Caching

Two independent cache stores, both managed via `PythonTools.cache`.

### Weather Cache

| Property | Value |
|----------|-------|
| Directory | `weather/` subdir (via `ensure_subdir("weather")`) |
| TTL | 15 minutes |
| Key format | `"{lat},{lon}:{units}:{provider}:{mode}"` |
| Load | `load_weather_cache(key)` → `(data, timestamp)` |
| Save | `save_weather_cache(key, data)` |

### Location Cache

| Property | Value |
|----------|-------|
| Directory | `location/` subdir (via `ensure_subdir("location")`) |
| TTL | 24 hours |
| Key format | `"{country}:{original_input.lower()}"` |
| Load | `load_location_from_cache(key)` |
| Save | `save_location_to_cache(key, data)` |

### Weather Cache Resolution Order

```
--force-cache set?
├── Yes → return cached data  (RuntimeError if no cache exists)
└── No  → attempt live fetch
            ├── Success → normalize → save cache → return live data
            └── Failure → cached data available?
                            ├── Yes → normalize → return cached data
                            └── No  → raise RuntimeError("Weather API unreachable and no cached data")
```

### Cache Control Flags

| Flag | Effect |
|------|--------|
| `--ignore-cache` | Skip cache read; always attempt live fetch |
| `--ignore-ttl` | Use cached data regardless of age |
| `--cache-info` | Emit `source`, `cache_age`, `cache_written` fields in `data` |
| `--force-cache` | Never call the API; return cached data only |

Cache metadata fields emitted in `data` (visible in all output modes):

| Field | Type | Description |
|-------|------|-------------|
| `source` | string | `"Live API"` \| `"cache"` \| `"cache-forced"` |
| `cache_written` | bool | `true` if cache was written this run |
| `cache_age` | string | Human-readable age via `format_age()` (e.g., `"5 minutes ago"`) |

---

## Output Schema

### Top-Level Payload Structure

```json
{
  "status":       "OK | WARNING | CRITICAL | UNKNOWN",
  "message":      "Weather normal: 89.80°F, 12.43 mph",
  "location":     "St John, KS",
  "data":         { ... },
  "runtime_ms":   142.7,
  "weather_mode": "current | hourly | weekly | full",
  "resolved_location": { ... }
}
```

`resolved_location` is present only when `--show-location-details` is passed.

See [Metadata_Schema.md](Metadata_Schema.md) for the full per-field reference.

### Output Mode Dispatch

| Mode | Trigger | Scope |
|------|---------|-------|
| Nagios | Default (no flags) | `current` only — `STATUS: message\|perfdata` |
| Verbose | `-v` / `--verbose` | All modes — routed to mode-specific formatter |
| JSON | `--json` | All modes — full payload via `serialize_for_json()` |
| Quiet | `-q` / `--quiet` | All modes — single summary line |

### Perfdata

Produced by `build_perfdata()` in Nagios mode only. Format: `metric=value;warn;crit`

| Metric | Always included | Requires flag |
|--------|-----------------|---------------|
| `temp` | ✓ | — |
| `wind` | ✓ | — |
| `humidity` | ✓ | — |
| `gust` | — | `--include-gusts` |
| `precip` | — | `--include-precip` |
| `cloud` | — | `--include-clouds` |

Example: `temp=32.10;35;40 wind=20.00;50;70 humidity=55.00;;`

---

## Logging

Managed by `PythonTools.log_helpers.factory.LoggerFactory`. Logging is **disabled** when running
in Nagios mode or when `--log-dir` is not set.

### Configuration

| Setting | Value |
|---------|-------|
| Log path | `{log_dir}/{script_name}.log` |
| Level | `INFO` |
| Max size | Configurable via `--log-max-mb` |
| Archive mode | `zip` |
| Backup count | `7` |
| Console output | `stderr`; enabled only in verbose, non-Nagios mode |

### Log Event Sequence

| Event | Function | Content |
|-------|----------|---------|
| `[START]` | `start_banner_weather(meta)` | All runtime parameters (location, country, provider, units, cache flags, include flags) |
| Location | `log_weather_data(loc)` | All resolved location fields as `key=value` pairs |
| Weather | `log_weather_data_mode_aware(mode, data)` | `current` → flat `key=value`; `hourly` → `hour[i].key=value`; `weekly` → `day[i].key=value` |
| Result | `log_summary_weather(state, message)` | Final Nagios state and summary message |
| `[END]` | `end_banner()` | Completion marker |

---

## PythonTools Dependencies

| Module | Symbols imported |
|--------|-----------------|
| `PythonTools.cache` | `ensure_subdir`, `cache_path`, `load_json_cache`, `save_json_cache`, `serialize_for_json` |
| `PythonTools.color` | `Color`, `colorize` |
| `PythonTools.datetime` | `format_age`, `get_timezone` |
| `PythonTools.location` | `US_STATES`, `normalize_city_name`, `validate_location_input`, `format_resolved_name`, `resolve_location`, `LocationNotFoundError`, `LocationInfo` |
| `PythonTools.log_helpers.factory` | `LoggerFactory` |
| `PythonTools.nagios` | `OK`, `WARNING`, `CRITICAL`, `UNKNOWN`, `FlagNames`, `Flags`, `BaseNagiosParser`, `should_output`, `nagios_summary` |
| `PythonTools.utils` | `strip_none` |
| `PythonTools.weather` | `WEATHER_PROVIDERS`, `convert_units_mode_aware`, `fmt_temp`, `fmt_clouds`, `fmt_wind`, `fmt_precip`, `merge_daily_periods`, `reorder_hourly_current_first` |
| `PythonTools.weather.providers` | `register_providers`, `resolve_nws_meta`, `fetch_valid_nws_observation` |

---

## Upcoming Features

- **`--full` mode output renderer** — `verbose_full()` combining current + hourly + weekly output in
  a single pass (flag wired; renderer not yet implemented)
- **`--show-codes` passthrough** — WMO weather code exposure in JSON and verbose output (flag exists;
  renderer not yet wired)
- **Forecast threshold evaluation** — extend the index engine to evaluate hourly and weekly data
  against configurable thresholds (e.g., flag days with high precipitation probability or peak wind)
- **Additional providers** — the registry contract supports new providers by implementing the
  standard `fetch_{mode}` signature and registering via `register_providers()`
- **International location defaults** — NWS is US-only; planned logic to auto-select `open-meteo`
  when `--country` is not `US`
