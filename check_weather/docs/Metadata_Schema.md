# Metadata Schema

This document defines the canonical JSON metadata schema emitted by `check_weather.py` when using `--json` or verbose mode (`-v`). The schema is deterministic, stable, and designed for ingestion by dashboards, log pipelines, and automated diagnostics.

All fields are guaranteed to exist unless explicitly marked as optional.

---

## 1. Top‑Level Structure

The JSON output contains four primary objects:

- `status` — final Nagios/Icinga evaluation
- `location` — resolved location metadata
- `weather` — normalized weather fields
- `provider` — provider URLs, timing, and raw fields

Example structure:

```json
{
  "status": { ... },
  "location": { ... },
  "weather": { ... },
  "provider": { ... }
}
```

## 2. status Object
Represents the final monitoring result.

| Field | Type | Description |
| :--- | :--- | :--- |
| state | string |	One of: "OK", "WARNING", "CRITICAL", "UNKNOWN" |
| code | integer | Nagios/Icinga exit code (0–3) |
| message |	string | Human‑readable summary line | 
| perfdata | object | Normalized perfdata fields |

### 2.1 Perfdata Schema
| Field | Type | Unit |	Description |
| :--- | :--- | :--- | :--- |
| temp | number | °F | Rounded temperature |
| wind | number | mph | Wind speed |
| gust | number | mph | Wind gust |
| precip | number | mm | Precipitation |
| clouds | number | % | Cloud cover |

## 3. location Object
Contains resolver output and normalized geographic metadata.

| Field | Type | Description |
| :--- | :--- | :--- |
| input | string | Original user‑provided location string |
| type | string | "zip", "city", "latlon" |
| latitude | number | Decimal latitude |
| longitude | number | Decimal longitude |
| city | string | Resolved city name (if available) |
| state | string | State/region abbreviation (if available) |
| country | string | ISO country code |
| resolver | string | "zippopotam", "openmeteo-geocode", "direct" |

## 4. weather Object
Normalized weather fields used for threshold evaluation and perfdata.

| Field | Type | Unit | Description |
| :--- | :--- | :--- | :--- |
| temperature_f | number | °F | Current temperature |
| wind_mph | number | mph | Wind speed |
| gust_mph | number | mph | Wind gust |
| precip_mm | number | mm | Precipitation |
| cloud_cover | number | % | Cloud cover |
| timestamp | string | ISO‑8601 | Provider timestamp |

All values are normalized and rounded for deterministic output.

## 5. provider Object
Contains provider metadata, raw fields, and timing.

| Field | Type | Description |
| :--- | :--- | :--- |
| forecast_url | string | Full Open‑Meteo forecast URL used |
| geocode_url | string or null | Geocoding URL (if used) |
| zip_url | string or null | Zippopotam.us URL (if used) |
| response_time_ms | integer | Total provider round‑trip time |
| raw | object | Raw provider fields before normalization |

### 5.1 raw Sub‑Object
Raw fields vary by provider but typically include:

| Field | Type | Description |
| :--- | :--- | :--- |
| temperature_c | number | Provider temperature in °C |
| wind_speed_ms | number | Provider wind speed in m/s |
| wind_gust_ms | number | Provider gust in m/s |
| precip_mm | number | Provider precipitation |
| cloud_cover | number | Provider cloud cover |
| provider_timestamp | string | Provider timestamp |

Raw fields are never modified.

## 6. Threshold Evaluation Metadata
Verbose/JSON mode includes threshold evaluation details.

| Field | Type | Description |
| :--- | :--- | :--- |
| temp_warn | number or null | Warning threshold |
| temp_crit | number or null | Critical threshold |
| wind_warn | number or null | Warning threshold |
| wind_crit | number or null | Critical threshold |
| gust_warn | number or null | Warning threshold |
| gust_crit | number or null | Critical threshold |
| precip_warn | number or null | Warning threshold |
| precip_crit | number or null | Critical threshold |
| triggered | string or null | "temp", "wind", "gust", "precip", or null |
| severity | string | "OK", "WARNING", "CRITICAL" |

This block is deterministic and always present.

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

* Field names never change without a schema version bump
* All numeric fields are normalized and rounded deterministically
* All URLs reflect the exact provider endpoints used
* All timestamps are ISO‑8601
* All objects exist even when values are null (except error)

This ensures compatibility with dashboards, log pipelines, and long‑term monitoring.