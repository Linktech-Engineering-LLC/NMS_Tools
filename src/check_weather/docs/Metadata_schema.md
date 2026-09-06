# Metadata Schema — check_weather v3.0.0

This document defines the complete JSON schema emitted by check_weather v3.0.0.

**Part of:** NMS_Tools Monitoring Suite  
**Document:** Metadata Schema
**Version:** 3.0.0 
**Author:** Leon McClatchey, Linktech Engineering LLC  
**License:** MIT  
**Requires:** Python 3.12+  (development only; not required for frozen binary)
**Last Updated:** 2026-08-16

---

## Table of Contents
1. [Overview](#1-overview)
2. [Stability Guarantees](#2-stability-guarantees)
3. [Top‑Level Payload](#3-top-level-payload)
4. [Alerts Block](#4-alerts-block)
5. [data — Current Mode](#5-data--current-mode)
6. [data — Hourly Mode](#6-data--hourly-mode)
7. [data — Weekly Mode](#7-data--weekly-mode)
8. [data — Full Mode](#8-data--full-mode)
9. [resolved_location Block](#9-resolved_location-block)
10. [Error Schema](#10-error-schema)
11. [Nagios Perfdata Format](#11-nagios-perfdata-format)
12. [Field Type Reference](#12-field-type-reference)
13. [See Also](#13-see-also)

---

## 1. Overview

This document is the authoritative field‑level reference for all JSON output produced by `check_weather --json`. It covers:
* all weather modes (`current`, `hourly`, `weekly`, `full`)
* the optional `resolved_location` block
* the root‑level `alerts` block (NWS only)
* the error schema
* the Nagios perfdata string format

The JSON payload is produced by `output_and_exit()` and serialized via `PythonTools.cache.serialize_for_json()`. Fields whose value is None after normalization are removed by `strip_none()` and will not appear in the output.

---

## 2. Stability Guarantees

| Guarantee | Detail |
| --- | --- |
| No silent field renames | Field names are stable across patch releases. Renames require a schema version bump. |
| Absent = null | Fields are omitted rather than emitted as ``null``. Treat absent fields as ``null``. |
| Dual‑unit always present | All numeric weather fields emit both metric and imperial variants. |
| ``hours[]`` cardinality | Always exactly 24 entries. |
| ``days[]`` cardinality | Always exactly 7 entries. |
| Moon fields | Always present when provider supports astronomy. |
| Feels‑like fields | Always present when computable. |
| Index block | Always present in current and hourly modes. |
| Alerts | Appear **only** at the root level and **only** when active. |
| Timestamps | All ``time`` fields are naive ISO 8601 local datetime strings. |

---

## 3. Top-Level Payload

Produced in all modes.

```json
{
  "status": "OK",
  "message": "Full forecast retrieved",
  "location": "34.333,-118.007",
  "alerts": [ ... ],               // only when active
  "data": { ... },                 // mode-specific block
  "runtime_ms": 142.7,
  "weather_mode": "full",
  "resolved_location": { ... }     // only with --show-location-details
}
```

### 3.1 Field Reference

| Field | Type | Always present | Description |
| --- | --- | --- | --- |
| ``status`` | string | ✓ | ``"OK"`` \\ | ``"WARNING"`` \\ | ``"CRITICAL"`` \\ | ``"UNKNOWN"`` |
| ``message`` | string | ✓ | One-line summary or mode retrieval message. |
| ``location`` | string | ✓ | Human-readable resolved location name. |
| ``alerts`` | array | No | Array of active NWS alerts. Root‑level only. |
| ``data`` | object | ✓ | Mode-specific weather data block. |
| ``runtime_ms`` | float | ✓ | Execution time in milliseconds. |
| ``weather_mode`` | string | ✓ | ``"current"`` \\ | ``"hourly"`` \\ | ``"weekly"`` \\ | ``"full"`` |
| ``resolved_location`` | object | No | Present only with ``--show-location-details``. |

---

## 4. Alerts Block
Alerts appear only at the root level and only when active. They are never part of any mode block.

```json
"alerts": [
  {
    "event": "Red Flag Warning",
    "severity": "Severe",
    "certainty": "Likely",
    "effective": "2026-08-28T14:00:00-07:00",
    "expires": "2026-08-28T20:00:00-07:00",
    "headline": "...",
    "description": "...",
    "instruction": "..."
  }
]
```

### Field Reference

| Field | Type | Description |
| --- | --- | --- |
| ``event`` | string | Alert name. |
| ``severity`` | string | Severity classification. |
| ``certainty`` | string | Likelihood classification. |
| ``effective`` | string | Start time. |
| ``expires`` | string | End time. |
| ``headline`` | string | Short summary. |
| ``description`` | string | Full alert text. |
| ``instruction`` | string | Recommended actions. |

---

## 5. data — Current Mode

Returned when `weather_mode` is `"current"` (default, no mode flag).

### Fields

Includes:
* temperature
* dewpoint
* humidity
* wind
* precipitation
* cloud cover
* pressure
* visibility
* sunrise/sunset
* moon data
* feels‑like
* index block
* cache metadata

Example

```json
{
  "time": "2026-08-28T07:00:00",
  "temperature_c": 22.8,
  "temperature_f": 73.0,
  "dewpoint_c": 9.2,
  "dewpoint_f": 48.6,
  "humidity": 42.0,
  "wind_kph": 11.6,
  "wind_mph": 7.2,
  "sunrise": "2026-08-28T06:22",
  "sunset": "2026-08-28T19:22",
  "moon_phase": "full_moon",
  "moon_phase_code": 4,
  "moon_illumination": 99.5,
  "moonrise": "2026-08-28T01:49",
  "moonset": "2026-08-28T13:46",
  "feels_like_c": 23.7,
  "feels_like_f": 74.7,
  "feels_like_source": "humidex",
  "index": {
    "heat_index": null,
    "wind_chill": null,
    "humidex": 23.7,
    "wet_bulb": 14.9,
    "vapor_pressure": 11.7,
    "saturation_vapor_pressure": 28.2,
    "mixing_ratio": null,
    "specific_humidity": null,
    "air_density": null,
    "pressure_altitude": null
  },
  "station_id": "CHOC1",
  "source": "Live API",
  "cache_written": true,
  "cache_age": "0 seconds ago"
}
```

---

## 6. data — Hourly Mode

Returned when `weather_mode` is `"hourly"` (`--hourly` flag).

Hourly entries include:
* temperature
* dewpoint
* humidity
* wind
* precipitation
* sunrise/sunset
* moon data
* feels‑like
* index block
* condition/context/icon

### Example Hour Object

```json
{
  "time": "2026-08-28T08:00:00",
  "temperature_c": 23.4,
  "temperature_f": 74.2,
  "dewpoint_c": 8.9,
  "dewpoint_f": 48.1,
  "humidity": 39.0,
  "wind_kph": 8.1,
  "wind_mph": 5.0,
  "sunrise": "2026-08-28T06:22",
  "sunset": "2026-08-28T19:22",
  "moon_phase": "full_moon",
  "moon_phase_code": 4,
  "moon_illumination": 99.5,
  "moonrise": "2026-08-28T01:49",
  "moonset": "2026-08-28T13:46",
  "feels_like_c": 24.2,
  "feels_like_f": 75.6,
  "feels_like_source": "humidex",
  "index": { ... },
  "context": "Overcast",
  "icon": "wi-cloudy.svg"
}
```

`hours[]` always contains **exactly 24 entries**. Index 0 is the current hour in the location's
local timezone (reordered by `reorder_hourly_current_first()`).

---

## 7. data — Weekly Mode

Returned when `weather_mode` is `"weekly"` (`--weekly` flag).

Weekly entries include:
* temp_min / temp_max
* wind / wind_max
* precipitation
* precipitation probability
* context
* moon data
* daily feels‑like

### Example Day Object
```json
{
  "date": "2026-08-28",
  "temp_max_c": 26.2,
  "temp_max_f": 79.2,
  "temp_min_c": 18.4,
  "temp_min_f": 65.2,
  "wind_kph": 16.1,
  "wind_mph": 10.0,
  "wind_kph_max": 24.2,
  "wind_mph_max": 15.0,
  "precip_mm": 0.0,
  "precip_in": 0.0,
  "precipitation_probability_max": 14,
  "context": "Clear sky",
  "moon_phase": "full_moon",
  "moon_phase_code": 4,
  "moon_illumination": 99.5,
  "moonrise": "2026-08-28T01:49",
  "moonset": "2026-08-28T13:46",
  "feels_like_c": 27.5,
  "feels_like_f": 81.5,
  "feels_like_source": "humidex"
}
```

`days[]` always contains **exactly 7 entries**. Index 0 is today (local date at query time). Days
are enriched with hourly sub-data by `merge_daily_periods()`.

---

## 8. data — Full Mode

Returned when `weather_mode = "full"`.

Structure
```json
{
  "provider": "nws",
  "source": "Live API",
  "current": { ... },
  "hourly": { ... },
  "weekly": { ... }
}
```

### Notes
* Full Mode is a **combined mode**, not a wrapper.
* Alerts remain **root-level only**, never inside data.
* All moon, feels‑like, and index fields appear inside their respective mode blocks.

---

## 9. resolved_location Block

Present in the top-level payload **only** when `--show-location-details` is passed. The
`weather_provider_url` field has query parameters stripped (base URL only); `weather_url` retains
the full URL including query parameters.

```json
{
  "input":                "67576",
  "weather_provider":     "nws",
  "weather_provider_url": "https://api.weather.gov/gridpoints/ICT/42,57/forecast",
  "location_provider":    "zippopotam.us",
  "location_provider_url":"https://api.zippopotam.us/us/67576",
  "city":                 "St John",
  "state":                "KS",
  "zip":                  "67576",
  "country":              "US",
  "latitude":             38.003,
  "longitude":            -98.768,
  "weather_url":          "https://api.weather.gov/gridpoints/ICT/42,57/forecast?units=us"
}
```

### 9.1 Field Reference

| Field | Type | Nullable | Description |
|-------|------|:--------:|-------------|
| `input` | string | No | Original location input string as supplied by the user. |
| `weather_provider` | string | No | Weather provider used: `"nws"` or `"open-meteo"`. Matches `--provider`. |
| `weather_provider_url` | string | Yes | Base URL of the weather provider endpoint (query string stripped). `null` if data came from cache only. |
| `location_provider` | string | Yes | Geocoding service used: `"zippopotam.us"` (ZIP input), Open-Meteo Geocoding API identifier (city input), or `null` for direct lat/lon input. |
| `location_provider_url` | string | Yes | Full URL used for location resolution. `null` for direct lat/lon input. |
| `city` | string | Yes | Normalized city name from `normalize_city_name()`. |
| `state` | string | Yes | State or province abbreviation. `null` for non-US locations. |
| `zip` | string | Yes | ZIP or postal code. `null` if input was city or lat/lon. |
| `country` | string | No | ISO 3166-1 alpha-2 country code (e.g., `"US"`). Matches `--country`. |
| `latitude` | float | No | Resolved latitude in decimal degrees. |
| `longitude` | float | No | Resolved longitude in decimal degrees. |
| `weather_url` | string | Yes | Full weather API URL including query parameters. `null` if data came from cache only. |

---

## 10. Error Schema

When an unrecoverable error occurs (provider unreachable and no cache, invalid location, etc.),
the tool exits with status `UNKNOWN` (code `3`). In JSON mode the payload takes this shape:

```json
{
  "status":       "UNKNOWN",
  "message":      "Weather API unreachable and no cached data",
  "location":     "St John, KS",
  "data":         {},
  "runtime_ms":   312.4,
  "weather_mode": "current"
}
```

`data` is an empty object `{}` on error — it is never `null`. `resolved_location` is omitted
unless `--show-location-details` was passed and location resolution succeeded before the error.

### 9.1 Common Error Messages

| Message | Cause |
|---------|-------|
| `"Weather API unreachable and no cached data"` | Live fetch failed and no cached entry exists. |
| `"Forced cache read but no cache exists"` | `--force-cache` was set but no cached entry exists for this key. |
| `"City not found: {input}"` | `PythonTools.location.resolve_location` raised `LocationNotFoundError`. |
| `"Unsupported provider: {name}"` | `--provider` value not present in `WEATHER_PROVIDERS`. |
| `"Provider '{name}' does not support mode '{mode}'"` | Provider's `supports` list does not include the requested mode. |
| `"Nagios mode only supports current weather."` | `--hourly`, `--weekly`, or `--full` used without `-v` or `--json`. |
| `"Only one mode may be selected: --weekly, --hourly, or --full."` | More than one mode flag was supplied. |
| `"Invalid Location Specified: {input}"` | `validate_location_input()` rejected the input. |
| `"Failed to initialize LoggerFactory: {detail}"` | Logger setup failed; output continues, logging is disabled. |

---

## 11. Nagios Perfdata Format

Produced only in Nagios output mode (default, no `-v` or `--json`) and only for `current` mode.
The perfdata string is appended to the Nagios status line after a pipe character:

```
STATUS: message|metric=value;warn;crit ...
```

### 11.1 Perfdata Metrics

| Metric key | Source field (metric) | Source field (imperial) | Always emitted | Flag required |
|------------|----------------------|------------------------|:--------------:|:-------------:|
| `temp` | `temperature_c` | `temperature_f` | ✓ | — |
| `wind` | `wind_kph` | `wind_mph` | ✓ | — |
| `humidity` | `humidity` | `humidity` | ✓ | — |
| `gust` | `wind_gust_kph` | `wind_gust_mph` | — | `--include-gusts` |
| `precip` | `precip_mm` | `precip_in` | — | `--include-precip` |
| `cloud` | `cloudcover` | `cloudcover` | — | `--include-clouds` |

The `--units` flag determines which source field is used for the value. Thresholds (`warn`, `crit`)
are taken from the corresponding `--warning-*` and `--critical-*` arguments; omitted thresholds
appear as empty strings.

### 11.2 Perfdata Examples

```
# metric units, no optional flags, no thresholds set:
temp=32.10;; wind=20.00;; humidity=55.00;;

# imperial units, all optionals, with thresholds:
temp=89.80;95;105 wind=12.43;50;70 humidity=55.00;; gust=21.74;60;80 precip=0.00;0.5;1.0 cloud=40.00;;
```

Values are always formatted to **2 decimal places**. The `gust`, `precip`, and `cloud` metrics are
omitted entirely (not emitted as empty) when their flags are not set.

---

## 12. Field Type Reference

| Type token | Python type | JSON type | Notes |
|------------|-------------|-----------|-------|
| `string` | `str` | `string` | UTF-8 |
| `float` | `float` | `number` | IEEE 754 double; may be integral (e.g., `40.0`) |
| `int` | `int` | `number` | Always integral |
| `bool` | `bool` | `true` / `false` | |
| `object` | `dict` | `object` | |
| `array` | `list` | `array` | |
| Nullable | Optional | absent or `null` | `strip_none()` removes `None` values; absent fields should be treated as `null` |

## 13. See Also
* [CHANGELOG](CHANGELOG.md)
* [Architecture](Architecture.md)
* [FLAGS.md](../../../docs/FLAGS.md)
* [Logging.md](Logging.md)
* [Enforcement](Enforcement.md)
* [Installation](Installation.md)
* [Operation](Operation.md)
* [Provider_Architecture](Provider_Architecture.md)
* [Usage](Usage.md)
