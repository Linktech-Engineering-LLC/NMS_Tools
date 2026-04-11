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

This ensures compatibility with dashboards, log pipelines, and long‑term monitoring.