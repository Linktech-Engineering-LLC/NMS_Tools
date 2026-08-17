# check_weather v3.0.0 Operation

**Part of:** NMS_Tools Monitoring Suite  
**Script:** export_icons.py  
**Version:** 3.0.0  
**Author:** Leon McClatchey, Linktech Engineering LLC  
**License:** MIT  
**Last Updated:** 2026‑08‑16

This document describes the operational flow of the check_weather subsystem within NMS_Tools v2.0.0, including provider selection, location resolution, normalization, merge behavior, index computation, caching, and output modes. It reflects the redesigned multi‑provider architecture introduced in the v2 series.

The goal of this subsystem is to provide deterministic, auditable, provider‑agnostic weather output suitable for CLI, CGI, and future web‑demo integrations.

## Table of Contents
1. [High‑Level Pipeline](#1-highlevel-pipeline)
2. [Provider Selection](#2-provider-selection)
3. [Location Resolution](#3-location-resolution)
  * [ZIP Code](#31-zip-code)
  * [City + Region](#32-city--region)
  * [Latitude/Longitude](#33-latitudelongitude)
  * [Resolver Summary](#34-resolver-summary)
4. [Normalization](#4-normalization)
5. [Merge Behavior](#5-merge-behavior)
6. [Index Computation](#6-index-computation)
7. [Unit Conversion](#7-unit-conversion)
8. [Caching](#8-caching)
9. [Output Modes](#9-output-modes)
10. [Error Handling](#10-error-handling)
11. [Deterministic Guarantees](#11-deterministic-guarantees)

## 1. High‑Level Pipeline
The operational pipeline is:

```Code
provider fetch
→ normalization
→ merge (hourly + daily)
→ index computation
→ unit conversion
→ caching
→ output (JSON)
```

All stages are deterministic and produce stable, reproducible results.

## 2. Provider Selection
`check_weather` supports multiple providers:

### NWS
* Current conditions
* Hourly forecast
* Weekly forecast
* Station metadata
* Observations
* Alerts (planned)

### Open‑Meteo
* Hourly forecast
* Daily/weekly forecast
* Dewpoint/humidity
* Sunrise/sunset
* Astronomy (planned)
* Alerts (optional)

### Selection Rules
1. If NWS coverage exists for the location → prefer NWS.
2. If NWS fails or is unavailable → fallback to Open‑Meteo.
3. If both fail → fallback to cached data.
4. If no cache exists → return error.

Provider selection is logged in metadata.

## 3. Location Resolution
The resolver accepts multiple input formats and produces:
* `latitude`
* `longitude`
* `display_name`
* `country_code`
* `admin1` (state/province)
* provider‑specific metadata

### 3.1 ZIP Code
If the input is a 5‑digit numeric string:
* Query Zippopotam.us
* Extract lat/lon and place metadata
* Pass coordinates to providers

Failures → resolver error.

### 3.2 City + Region
Examples:
* `"Wichita, KS"`
* `"Berlin, DE"`

Steps:
1. Parse city and region
2. Query Open‑Meteo Geocoding
3. Extract lat/lon, country code, admin1
4. Pass coordinates to providers

Ambiguous results → resolver error.

### 3.3 Latitude/Longitude
If the input matches `"<lat>,<lon>"`:
* Use coordinates directly
* No external resolver

Invalid coordinates → resolver error.

### 3.4 Resolver Summary

| Input Type | Resolver Used | Failure Mode |
| --- | --- | --- |
| ZIP code | Zippopotam.us | Resolver error |
| City/state or city/country | Open‑Meteo Geocoding | Resolver error |
| Lat/lon | None | Resolver error |
| Anything else | Rejected | Resolver error |

## 4. Normalization
All provider responses are normalized into a unified schema.
Normalization ensures:
* consistent field names
* consistent units (pre‑conversion)
* consistent timestamps
* consistent metadata
* consistent array structures

Normalized fields include:
* temperature
* dewpoint
* humidity
* wind speed
* wind gust
* pressure
* precipitation
* cloud cover
* sunrise/sunset
* weathercode
* provider metadata

Normalization is deterministic and provider‑agnostic.

## 5. Merge Behavior
The merge layer enriches daily and hourly forecasts using normalized provider data.

### Daily Merge
* dewpoint (hourly‑averaged)
* humidity (hourly‑averaged)
* wind gust (hourly max)
* precipitation (provider‑native)
* sunrise/sunset
* weathercode → icon context
* feels‑like (planned)

### Hourly Merge
* current conditions inserted at index 0
* sunrise/sunset propagated
* index fields attached
* gust normalization applied

Merge behavior is deterministic and logged.

## 6. Index Computation
The index engine computes derived meteorological values:
* heat index
* humidex
* wind chill
* wet bulb
* vapor pressure
* saturation vapor pressure
* mixing ratio
* specific humidity
* air density
* pressure altitude

Indexes are computed for every hourly entry.
Daily feels‑like is planned for v2.1.0.

## 7. Unit Conversion
Unit conversion is applied after merge and before caching.

Conversions include:
* °C → °F
* m/s → mph
* mm → inches (planned)
* hPa → inHg (planned)

Conversion rules are mode‑aware and deterministic.

## 8. Caching
The caching subsystem stores:
* current
* hourly
* weekly
* metadata
* provider info
* cache_id
* cache_age
* cache_written

Caching guarantees:
* stable output
* reproducible results
* reduced provider load

Cache metadata is included in all output modes.

## 9. Output Modes
### 9.1 Current Mode
* NWS only
* includes station observations
* includes metadata

### 9.2 Hourly Mode
* NWS or Open‑Meteo
* includes indexes
* includes sunrise/sunset

### 9.3 Weekly Mode
* NWS or Open‑Meteo
* enriched using hourly data

### 9.4 Full Mode (Planned)
* current + hourly + weekly + alerts + astronomy + metadata

All modes produce deterministic JSON output.

## 10. Error Handling
Errors are categorized as:
* resolver errors
* provider errors
* normalization errors
* merge errors
* index errors
* conversion errors
* caching errors

Errors include structured metadata describing:
* failure type
* failure stage
* provider URLs
* resolver path
* timestamps

All errors produce deterministic JSON.

## 11. Deterministic Guarantees
`check_weather` guarantees:
* deterministic output
* stable schema
* reproducible merge behavior
* consistent normalization
* consistent index computation
* consistent unit conversion
* logged fallback behavior
* provider‑agnostic results
* no nondeterministic fields

These guarantees ensure predictable behavior across all supported platforms.

End of Operation.md