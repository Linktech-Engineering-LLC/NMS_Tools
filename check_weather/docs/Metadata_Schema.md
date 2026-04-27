# Metadata Schema
Deterministic JSON Schema for check_weather.py

This document defines the canonical JSON metadata schema emitted by check_weather.py when using --json or verbose mode (-v).
The schema is deterministic, stable, and designed for ingestion by dashboards, log pipelines, and automated diagnostics.

All fields are guaranteed to exist unless explicitly marked optional.

## 1. Top‑Level Structure
The JSON output contains five primary objects:

- status — final Nagios/Icinga state
- message — human‑readable summary
- location — resolved human‑readable location string
- data — normalized weather metrics
- resolved_location — provider + resolver metadata
- runtime_ms — execution time

Example:

```json
{
  "status": "OK",
  "message": "Weather normal: 56.48°F, 20.26 mph",
  "location": "Saint John, Kansas, US",
  "data": { ... },
  "resolved_location": { ... },
  "runtime_ms": 1169.18
}
```

## 2. status Field

| Field |	Type |	Description |
| :--- | :--- | :--- |
| status |	string |	One of: "OK", "WARNING", "CRITICAL", "UNKNOWN" |
This is the final Nagios/Icinga evaluation.

## 3. message Field
| Field |	Type |	Description |
| :--- | :--- | :--- |
| message |	string |	Human‑readable summary identical to Nagios output |

Example:

```"Weather normal: 56.48°F, 20.26 mph"```

## 4. location Field
| Field |	Type |	Description |
| :--- | :--- | :--- |
| location |	string |	Human‑readable resolved location string |

Example:

```"Saint John, Kansas, US"```

## 5. data Object

Normalized weather metrics used for threshold evaluation and perfdata.

| Field | Type | Unit |	Description |
| :--- | :--- | :--- | :--- |
| time |	string | ISO‑8601	| Provider timestamp |
| temperature_c |	number |	°C |	Temperature |
| apparent_temperature_c |	number |	°C |	Feels‑like temperature |
| dewpoint_c |	number |	°C |	Dew point |
| wind_kph |	number |	kph |	Wind speed |
| wind_gust_kph |	number |	kph |	Wind gust |
| humidity |	number |	% |	Relative humidity |
| precip_mm |	number |	mm |	Precipitation |
| precipitation_probability |	number |	% |	Precip probability |
| cloudcover |	number |	% |	Cloud cover |
| visibility_m |	number |	m	| Visibility |
| pressure_msl |	number |	hPa |	Pressure |
| temperature_f |	number |	°F |	Temperature (imperial) |
| apparent_temperature_f |	number |	°F |	Feels‑like (imperial) |
| dewpoint_f |	number |	°F |	Dew point (imperial) |
| wind_mph |	number |	mph |	Wind speed |
| wind_gust_mph |	number |	mph |	Wind gust |
| precip_in |	number |	in |	Precipitation |
| visibility_km |	number |	km |	Visibility |
| visibility_mi |	number |	mi |	Visibility |
| pressure_inhg |	number |	inHg |	Pressure |
| condition |	number |	code |	Open‑Meteo weather code |
| condition_text |	string |	text |	Human‑readable condition |
| source |	string |	"Live API" or "Cache" | |
| cache_written |	boolean |	|	Whether cache was updated |
| cache_age |	string | |		Age string (e.g., "45s") |

All values are normalized and rounded deterministically.

### New Fields in v2.2.0

| Field | Type | Description |
|-------|------|-------------|
| mode | string | One of: `"current"`, `"hourly"`, `"weekly"` |
| context | string | Normalized human‑readable condition text (backend‑derived) |
| icon | string | Deterministic icon filename selected by backend |
| wind_mph_max | number | Max wind speed for weekly mode (imperial) |
| wind_kph_max | number | Max wind speed for weekly mode (metric) |
| hours | array<object> | Rolling 24‑hour forecast entries (hourly mode only) |
| days | array<object> | 7‑day forecast entries starting today (weekly mode only) |
| source | string | `"Live API"` or `"Cache"` |
| cache_written | boolean | Whether cache was updated during this run |
| cache_age | string | Age string (e.g., `"0s"`, `"45s"`) |

### Hourly Mode (`mode = "hourly"`)

Hourly mode returns a rolling 24‑hour forecast beginning at the next hour ≥ local time.

| Field | Type | Description |
|-------|------|-------------|
| hours | array<object> | Exactly 24 entries, each representing one hour |

Each hourly entry contains:

- time (ISO‑8601)
- temperature_c / temperature_f
- apparent_temperature_c / apparent_temperature_f
- dewpoint_c / dewpoint_f
- wind_kph / wind_mph
- wind_gust_kph / wind_gust_mph
- humidity
- precip_mm / precip_in
- precipitation_probability
- cloudcover
- visibility_m / visibility_km / visibility_mi
- pressure_msl / pressure_inhg
- condition (WMO code)
- context (normalized text)
- icon (filename)
- sunrise / sunset (ISO‑8601)

### Weekly Mode (`mode = "weekly"`)

Weekly mode returns exactly 7 days beginning at the current local date.

| Field | Type | Description |
|-------|------|-------------|
| days | array<object> | Exactly 7 entries, one per day |

Each day entry contains:

- date (YYYY‑MM‑DD)
- sunrise / sunset (ISO‑8601)
- temp_max_c / temp_max_f
- temp_min_c / temp_min_f
- wind_kph_max / wind_mph_max
- precip_mm / precip_in
- precipitation_probability_max
- condition (WMO code)
- context (normalized text)
- icon (filename)
### Weekly Mode (`mode = "weekly"`)

Weekly mode returns exactly 7 days beginning at the current local date.

| Field | Type | Description |
|-------|------|-------------|
| days | array<object> | Exactly 7 entries, one per day |

Each day entry contains:

- date (YYYY‑MM‑DD)
- sunrise / sunset (ISO‑8601)
- temp_max_c / temp_max_f
- temp_min_c / temp_min_f
- wind_kph_max / wind_mph_max
- precip_mm / precip_in
- precipitation_probability_max
- condition (WMO code)
- context (normalized text)
- icon (filename)

### Current Mode (`mode = "current"`)

Current mode includes:

- context (normalized condition text)
- icon (deterministic icon filename)

## 6. resolved_location Object

Contains resolver metadata, provider URLs, and normalized geographic fields.

| Field |	Type |	Description |
| :--- | :--- | :--- |
| input |	string |	Original user input |
| weather_provider |	string |	"open-meteo" |
| weather_provider_url |	string |	Base forecast URL |
| location_provider |	string |	"zippopotam.us" or "open-meteo" |
| location_provider_url |	string |	URL used for geocoding |
| city |	string or null |	Resolved city |
| state |	string or null |	Resolved state |
| zip |	string or null |	ZIP code (if applicable) |
| country |	string |	ISO country code |
| latitude |	number |	Decimal latitude |
| longitude |	number |	Decimal longitude |
| weather_url |	string |	Full forecast URL used |

This block is always present.

## 7. Error Schema (When Status = UNKNOWN)

If the plugin encounters a resolver or provider error, the JSON includes:

```json
"error": {
  "type": "resolver" | "provider" | "input" | "internal",
  "message": "Human-readable error",
  "details": "Optional diagnostic information"
}
```

The error object is omitted when the check succeeds.

## 8. Stability Guarantees

check_weather.py guarantees:

- Field names never change without a schema version bump
- All numeric fields are normalized and rounded deterministically
- All URLs reflect the exact provider endpoints used
- All timestamps are ISO‑8601
- resolved_location is always present
- data always contains the full normalized weather block
- status, message, and runtime_ms always exist
- `hours[]` always contains exactly 24 entries in hourly mode
- `days[]` always contains exactly 7 entries in weekly mode
- `context` and `icon` are always present for all modes
- `mode` is always present and validated
- Day/night icon selection is deterministic based on sunrise/sunset timestamps

This ensures compatibility with dashboards, log pipelines, and long‑term monitoring.

## 9. JSON Examples (v2.2.0)

### 9.1 Current Mode Example

```json
{
  "status": "OK",
  "message": "Weather normal: 56.48°F, 20.26 mph",
  "location": "Saint John, Kansas 67576, US",
  "data": {
    "mode": "current",
    "time": "2026-04-27T11:00",
    "temperature_f": 56.48,
    "temperature_c": 13.6,
    "wind_mph": 20.26,
    "wind_kph": 32.6,
    "humidity": 31,
    "cloudcover": 54,
    "precip_in": 0.0,
    "precip_mm": 0.0,
    "condition": 2,
    "context": "Partly cloudy",
    "icon": "wi-day-cloudy.svg",
    "source": "Live API",
    "cache_written": true,
    "cache_age": "0s"
  },
  "resolved_location": {
    "input": "67576",
    "weather_provider": "open-meteo",
    "weather_provider_url": "https://api.open-meteo.com/v1/forecast",
    "location_provider": "zippopotam.us",
    "location_provider_url": "https://api.zippopotam.us/US/67576",
    "city": "Saint John",
    "state": "Kansas",
    "country": "US",
    "latitude": 38.0309,
    "longitude": -98.7647,
    "weather_url": "https://api.open-meteo.com/v1/forecast?latitude=..."
  },
  "runtime_ms": 763.0
}
```

### 9.2 Hourly Mode Example (Rolling 24 Hours)

```json
{
  "status": "OK",
  "message": "Hourly forecast retrieved",
  "location": "Saint John, Kansas 67576, US",
  "data": {
    "mode": "hourly",
    "hours": [
      {
        "time": "2026-04-27T11:00",
        "temperature_f": 54.68,
        "wind_mph": 14.42,
        "humidity": 84,
        "cloudcover": 100,
        "precip_in": 0.0,
        "condition": 3,
        "context": "Overcast",
        "icon": "wi-cloudy.svg",
        "sunrise": "2026-04-27T06:43",
        "sunset": "2026-04-27T20:22"
      },
      {
        "time": "2026-04-27T12:00",
        "temperature_f": 55.94,
        "wind_mph": 14.79,
        "humidity": 79,
        "cloudcover": 87,
        "precip_in": 0.0,
        "condition": 3,
        "context": "Overcast",
        "icon": "wi-cloudy.svg",
        "sunrise": "2026-04-27T06:43",
        "sunset": "2026-04-27T20:22"
      }
      // ... 22 more entries (always 24 total)
    ],
    "units": "imperial",
    "source": "Live API",
    "cache_written": true,
    "cache_age": "0s"
  },
  "runtime_ms": 645.06
}
```

### 9.3 Weekly Mode Example (7 Days Starting Today)

```json
{
  "status": "OK",
  "message": "Weekly forecast retrieved",
  "location": "Saint John, Kansas 67576, US",
  "data": {
    "mode": "weekly",
    "days": [
      {
        "date": "2026-04-27",
        "temp_max_f": 66.02,
        "temp_min_f": 53.06,
        "wind_mph_max": 17.15,
        "precip_in": 0.0,
        "precipitation_probability_max": 26,
        "condition": 45,
        "context": "Fog",
        "icon": "wi-night-fog.svg",
        "sunrise": "2026-04-27T06:43",
        "sunset": "2026-04-27T20:22"
      },
      {
        "date": "2026-04-28",
        "temp_max_f": 63.5,
        "temp_min_f": 42.98,
        "wind_mph_max": 14.6,
        "precip_in": 0.0,
        "precipitation_probability_max": 3,
        "condition": 3,
        "context": "Overcast",
        "icon": "wi-night-cloudy.svg",
        "sunrise": "2026-04-28T06:41",
        "sunset": "2026-04-28T20:23"
      }
      // ... 5 more entries (always 7 total)
    ],
    "units": "imperial",
    "source": "Live API",
    "cache_written": true,
    "cache_age": "0s"
  },
  "runtime_ms": 527.41
}
```
