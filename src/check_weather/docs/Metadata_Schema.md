# Metadata Schema — check_weather v2.0.0

**Part of:** NMS_Tools Monitoring Suite  
**Script:** `check_weather.py`  
**Author:** Leon McClatchey, Linktech Engineering LLC  
**License:** MIT  
**Last Updated:** 2026-08-15

---

## Table of Contents

1. [Overview](#overview)
2. [Stability Guarantees](#stability-guarantees)
3. [Top-Level Payload](#top-level-payload)
4. [data — Current Mode](#data--current-mode)
5. [data — Hourly Mode](#data--hourly-mode)
6. [data — Weekly Mode](#data--weekly-mode)
7. [resolved_location Block](#resolved_location-block)
8. [Error Schema](#error-schema)
9. [Nagios Perfdata Format](#nagios-perfdata-format)
10. [Field Type Reference](#field-type-reference)

---

## Overview

This document is the authoritative field-level reference for all JSON output produced by
`check_weather --json`. It covers every mode (`current`, `hourly`, `weekly`, `full`), the optional
`resolved_location` block, the error schema, and the Nagios perfdata string format.

The JSON payload is produced by `output_and_exit()` when `--json` is passed and serialized via
`PythonTools.cache.serialize_for_json()`. Fields whose value is `None` after normalization are
stripped by `strip_none()` before serialization and will **not** appear in the output at all.

---

## Stability Guarantees

| Guarantee | Detail |
|-----------|--------|
| No silent field renames | Field names are stable across patch releases. Renames require a schema version bump. |
| Absent = null | A field that is absent from the response should be treated as `null`. Fields are omitted rather than emitted as `null`. |
| Dual-unit always present | Both metric and imperial variants of every numeric weather field are always emitted, regardless of `--units`. |
| `hours[]` cardinality | Always exactly 24 entries, starting from the current hour in the location's local timezone. |
| `days[]` cardinality | Always exactly 7 entries, starting from today (local date at query time). |
| Numeric precision | All float fields are IEEE 754 double precision. Perfdata values are formatted to 2 decimal places. |
| Timestamps | `time` fields are naive ISO 8601 local datetime strings (`YYYY-MM-DDTHH:MM:SS`). `date` fields are `YYYY-MM-DD`. |

---

## Top-Level Payload

Produced in all modes and output formats.

```json
{
  "status":            "OK",
  "message":           "Weather normal: 89.80°F, 12.43 mph",
  "location":          "St John, KS",
  "data":              { ... },
  "runtime_ms":        142.7,
  "weather_mode":      "current",
  "resolved_location": { ... }
}
```

### Field Reference

| Field | Type | Always present | Description |
|-------|------|:--------------:|-------------|
| `status` | string | ✓ | Nagios exit state: `"OK"` \| `"WARNING"` \| `"CRITICAL"` \| `"UNKNOWN"` |
| `message` | string | ✓ | One-line summary. In `current` mode: threshold result or normal weather summary. In `hourly`/`weekly`: `"{Mode} forecast retrieved"`. |
| `location` | string | ✓ | Human-readable resolved location name via `format_resolved_name()`. Example: `"St John, KS"`. |
| `data` | object | ✓ | Mode-specific weather data block. See per-mode sections below. |
| `runtime_ms` | float | ✓ | Wall-clock execution time in milliseconds, rounded to 2 decimal places. |
| `weather_mode` | string | ✓ | Active weather mode: `"current"` \| `"hourly"` \| `"weekly"` \| `"full"`. |
| `resolved_location` | object | Only with `--show-location-details` | Provider and coordinate detail. See [resolved_location Block](#resolved_location-block). |

---

## data — Current Mode

Returned when `weather_mode` is `"current"` (default, no mode flag).

```json
{
  "time":                    "2026-08-15T12:00:00",
  "temperature_c":           32.1,
  "temperature_f":           89.8,
  "apparent_temperature_c":  34.5,
  "apparent_temperature_f":  94.1,
  "dewpoint_c":              20.0,
  "dewpoint_f":              68.0,
  "humidity":                55.0,
  "wind_kph":                20.0,
  "wind_mph":                12.4,
  "wind_gust_kph":           35.0,
  "wind_gust_mph":           21.7,
  "cloudcover":              40.0,
  "precip_mm":               0.0,
  "precip_in":               0.0,
  "pressure_msl":            1013.2,
  "visibility_m":            10000,
  "context":                 "Partly Cloudy",
  "source":                  "Live API",
  "cache_written":           true,
  "cache_age":               "0 seconds ago",
  "units":                   "metric"
}
```

### Field Reference

| Field | Type | Nullable | Description |
|-------|------|:--------:|-------------|
| `time` | string | No | Observation time as naive local ISO 8601 datetime (`YYYY-MM-DDTHH:MM:SS`). |
| `temperature_c` | float | No | Air temperature in degrees Celsius. |
| `temperature_f` | float | No | Air temperature in degrees Fahrenheit. |
| `apparent_temperature_c` | float | Yes | Feels-like temperature in °C (heat index or wind chill, whichever applies). |
| `apparent_temperature_f` | float | Yes | Feels-like temperature in °F. |
| `dewpoint_c` | float | Yes | Dewpoint temperature in °C. |
| `dewpoint_f` | float | Yes | Dewpoint temperature in °F. |
| `humidity` | float | Yes | Relative humidity as a percentage (0–100). Unit-agnostic. |
| `wind_kph` | float | Yes | Sustained wind speed in kilometres per hour. |
| `wind_mph` | float | Yes | Sustained wind speed in miles per hour. |
| `wind_gust_kph` | float | Yes | Wind gust speed in kph. Absent if the provider reports no gust data. |
| `wind_gust_mph` | float | Yes | Wind gust speed in mph. Absent if the provider reports no gust data. |
| `cloudcover` | float | Yes | Total cloud cover as a percentage (0–100). Unit-agnostic. |
| `precip_mm` | float | Yes | Precipitation accumulation in millimetres. |
| `precip_in` | float | Yes | Precipitation accumulation in inches. |
| `pressure_msl` | float | Yes | Mean sea-level atmospheric pressure in hPa. Unit-agnostic. |
| `visibility_m` | int | Yes | Horizontal visibility in metres. Unit-agnostic. |
| `context` | string | Yes | Human-readable condition label derived from provider condition code (e.g., `"Partly Cloudy"`, `"Thunderstorm"`). |
| `source` | string | No | Data origin: `"Live API"` — fetched live this run; `"cache"` — served from cache; `"cache-forced"` — `--force-cache` was set. |
| `cache_written` | bool | No | `true` if the cache was written during this run; `false` if cache was already current or `--force-cache` was used. |
| `cache_age` | string | Yes | Human-readable cache age string (e.g., `"5 minutes ago"`). Present only when cache was used and `--cache-info` was passed, or when `source` is `"cache"`. |
| `units` | string | No | Active unit system passed via `--units`: `"metric"` or `"imperial"`. Does not affect which fields are emitted; affects threshold evaluation, perfdata values, and verbose display. |

---

## data — Hourly Mode

Returned when `weather_mode` is `"hourly"` (`--hourly` flag).

```json
{
  "units":         "metric",
  "source":        "Live API",
  "cache_written": true,
  "hours": [
    {
      "time":           "2026-08-15T12:00:00",
      "temperature_c":  32.1,
      "temperature_f":  89.8,
      "wind_kph":       20.0,
      "wind_mph":       12.4,
      "cloudcover":     40.0,
      "precip_mm":      0.0,
      "precip_in":      0.0,
      "context":        "Partly Cloudy"
    },
    ...
  ]
}
```

`hours[]` always contains **exactly 24 entries**. Index 0 is the current hour in the location's
local timezone (reordered by `reorder_hourly_current_first()`).

### Top-Level Fields (hourly data block)

| Field | Type | Nullable | Description |
|-------|------|:--------:|-------------|
| `units` | string | No | Active unit system: `"metric"` or `"imperial"`. |
| `source` | string | No | Data origin: `"Live API"` \| `"cache"` \| `"cache-forced"`. |
| `cache_written` | bool | No | `true` if cache was written this run. |
| `cache_age` | string | Yes | Human-readable cache age. Present when `source` is `"cache"`. |
| `hours` | array | No | Array of exactly 24 hour objects. |

### Hour Object Fields

| Field | Type | Nullable | Description |
|-------|------|:--------:|-------------|
| `time` | string | No | Hour start time as naive local ISO 8601 datetime (`YYYY-MM-DDTHH:MM:SS`). |
| `temperature_c` | float | No | Air temperature in °C for this hour. |
| `temperature_f` | float | No | Air temperature in °F for this hour. |
| `wind_kph` | float | Yes | Sustained wind speed in kph for this hour. |
| `wind_mph` | float | Yes | Sustained wind speed in mph for this hour. |
| `cloudcover` | float | Yes | Cloud cover percentage for this hour (0–100). |
| `precip_mm` | float | Yes | Precipitation in mm for this hour. |
| `precip_in` | float | Yes | Precipitation in inches for this hour. |
| `context` | string | Yes | Human-readable condition label for this hour. |

---

## data — Weekly Mode

Returned when `weather_mode` is `"weekly"` (`--weekly` flag).

```json
{
  "units":         "metric",
  "source":        "Live API",
  "cache_written": true,
  "days": [
    {
      "date":                          "2026-08-15",
      "temp_max_c":                    34.0,
      "temp_max_f":                    93.2,
      "temp_min_c":                    22.0,
      "temp_min_f":                    71.6,
      "wind_kph":                      25.0,
      "wind_mph":                      15.5,
      "wind_kph_max":                  56.3,
      "wind_mph_max":                  35.0,
      "precip_mm":                     2.5,
      "precip_in":                     0.1,
      "precipitation_probability_max": 40,
      "context":                       "Partly Cloudy"
    },
    ...
  ]
}
```

`days[]` always contains **exactly 7 entries**. Index 0 is today (local date at query time). Days
are enriched with hourly sub-data by `merge_daily_periods()`.

### Top-Level Fields (weekly data block)

| Field | Type | Nullable | Description |
|-------|------|:--------:|-------------|
| `units` | string | No | Active unit system: `"metric"` or `"imperial"`. |
| `source` | string | No | Data origin: `"Live API"` \| `"cache"` \| `"cache-forced"`. |
| `cache_written` | bool | No | `true` if cache was written this run. |
| `cache_age` | string | Yes | Human-readable cache age. Present when `source` is `"cache"`. |
| `days` | array | No | Array of exactly 7 day objects. |

### Day Object Fields

| Field | Type | Nullable | Description |
|-------|------|:--------:|-------------|
| `date` | string | No | Calendar date in local timezone as `YYYY-MM-DD`. |
| `temp_max_c` | float | No | Forecast high temperature in °C. |
| `temp_max_f` | float | No | Forecast high temperature in °F. |
| `temp_min_c` | float | No | Forecast low temperature in °C. |
| `temp_min_f` | float | No | Forecast low temperature in °F. |
| `wind_kph` | float | Yes | Representative wind speed for the day in kph (typically afternoon peak). |
| `wind_mph` | float | Yes | Representative wind speed for the day in mph. |
| `wind_kph_max` | float | Yes | Maximum wind speed across all hourly entries for the day, in kph. Populated by `merge_daily_periods()`. |
| `wind_mph_max` | float | Yes | Maximum wind speed across all hourly entries for the day, in mph. Populated by `merge_daily_periods()`. |
| `precip_mm` | float | Yes | Total precipitation for the day in mm. |
| `precip_in` | float | Yes | Total precipitation for the day in inches. |
| `precipitation_probability_max` | int | Yes | Maximum precipitation probability for the day as a percentage (0–100). Unit-agnostic. |
| `context` | string | Yes | Representative condition label for the day, derived from the dominant hourly condition. |

---

## resolved_location Block

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

### Field Reference

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

## Error Schema

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

### Common Error Messages

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

## Nagios Perfdata Format

Produced only in Nagios output mode (default, no `-v` or `--json`) and only for `current` mode.
The perfdata string is appended to the Nagios status line after a pipe character:

```
STATUS: message|metric=value;warn;crit ...
```

### Perfdata Metrics

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

### Perfdata Examples

```
# metric units, no optional flags, no thresholds set:
temp=32.10;; wind=20.00;; humidity=55.00;;

# imperial units, all optionals, with thresholds:
temp=89.80;95;105 wind=12.43;50;70 humidity=55.00;; gust=21.74;60;80 precip=0.00;0.5;1.0 cloud=40.00;;
```

Values are always formatted to **2 decimal places**. The `gust`, `precip`, and `cloud` metrics are
omitted entirely (not emitted as empty) when their flags are not set.

---

## Field Type Reference

| Type token | Python type | JSON type | Notes |
|------------|-------------|-----------|-------|
| `string` | `str` | `string` | UTF-8 |
| `float` | `float` | `number` | IEEE 754 double; may be integral (e.g., `40.0`) |
| `int` | `int` | `number` | Always integral |
| `bool` | `bool` | `true` / `false` | |
| `object` | `dict` | `object` | |
| `array` | `list` | `array` | |
| Nullable | Optional | absent or `null` | `strip_none()` removes `None` values; absent fields should be treated as `null` |
