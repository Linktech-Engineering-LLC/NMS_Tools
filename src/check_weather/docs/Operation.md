# check_weather v3.0.0 Operation

This document describes the operational flow of the check_weather subsystem in NMS_Tools v3.0.0.

**Part of:** NMS_Tools Monitoring Suite  
**Document:** Operation
**Version:** 3.0.0 
**Author:** Leon McClatchey, Linktech Engineering LLC  
**License:** MIT  
**Requires:** Python 3.12+  (development only; not required for frozen binary)
**Last Updated:** 2026-08-16

This document describes the operational flow of the check_weather subsystem within NMS_Tools v2.0.0, including provider selection, location resolution, normalization, merge behavior, index computation, caching, and output modes. It reflects the redesigned multi‑provider architecture introduced in the v2 series.

The goal of this subsystem is to provide deterministic, auditable, provider‑agnostic weather output suitable for CLI, CGI, and future web‑demo integrations.

## Table of Contents
1. [Overview](#1-overview)
2. [Deterministic Guarantees](#2-deterministic-guarantees)
3. [High‑Level Pipeline](#3-highlevel-pipeline)
4. [Provider Architecture](#4-provider-architecture)
5. [Location Resolution](#5-location-resolution)
    1. [ZIP Code](#51-zip-code)
    2. [City + Region](#52-city--region)
    3. [Latitude/Longitude](#53-latitudelongitude)
    4. [Resolver Summary](#54-resolver-summary)
6. [Normalization](#6-normalization)
7. [Merge Layer](#7-merge-layer)
8. [Index Engine](#8-index-engine)
9. [Unit Conversion](#9-unit-conversion)
10. [Caching](#10-caching)
11. [Output Modes](#11-output-modes)
12. [Error Handling](#12-error-handling)
13. [See Also](#13-see-also)

---

## 1. Overview

`check_weather` is a deterministic, multi‑provider weather subsystem that resolves locations, fetches provider data, normalizes fields, merges hourly and daily forecasts, computes meteorological indexes, applies unit conversion, manages caching, and produces stable JSON output for monitoring systems and automation pipelines.

Version 3.0.0 introduces:
* **Full Mode** (current + hourly + weekly in one payload)
* **Feels‑like computation** (current, hourly, daily)
* **Moon data** (rise, set, phase, illumination)
* **NWS Alerts** (fully implemented)
* expanded normalization rules
* deterministic merge behavior
* improved provider fallback logic
* stable dual‑unit output
* enriched daily forecasts
* structured error payloads
* consistent timestamp/cardinality guarantees

--- 

## 2. Deterministic Guarantees

`check_weather` v3.0.0 guarantees:
* stable schema across patch releases
* deterministic provider selection
* reproducible normalization
* reproducible merge behavior
* consistent index computation
* consistent unit conversion
* stable cardinality (`hours[] = 24`, `days[] = 7`)
* dual‑unit numeric fields always emitted
* no nondeterministic fields
* logged fallback behavior
* provider‑agnostic results
* timestamps normalized to naive local ISO 8601

These guarantees ensure predictable behavior across all supported platforms and monitoring systems.

---

## 3. High‑Level Pipeline
```Code
provider fetch
→ normalization
→ merge (hourly + daily)
→ index computation
→ unit conversion
→ caching
→ alerts (NWS only, root-level)
→ output (JSON)
```
Alerts are fetched after all mode data is gathered and inserted at the root level of the final payload when active.

---

## 4. Provider Architecture

### 4.1 NWS (National Weather Service)
* Current conditions
* Hourly forecast
* Weekly forecast
* Station metadata
* Observations
* **Alerts (implemented, root level)**
* **Moon data (implemented)**

### 4.2 Open‑Meteo
* Hourly forecast
* Daily/weekly forecast
* Dewpoint/humidity
* Sunrise/sunset
* **Astronomy (moonrise, moonset, phase, illumination)**
* Alerts (not supported)

### 4.3 Provider Selection Rules
* If NWS coverage exists → **prefer NWS**.
* If NWS fails or is unavailable → **fallback to Open‑Meteo**.
* If both fail → **fallback to cached data**.
* If no cache exists → **return structured error**.

Provider selection is logged and included in metadata when `--show-location-details` is used.

---

## 5. Location Resolution

The resolver accepts multiple input formats and produces:
* `latitude`
* `longitude`
* `city`
* `state`
* `country`
* normalized display name
* provider‑specific metadata

### 5.1 ZIP Code

If input is a 5‑digit numeric string:
* Query Zippopotam.us
* Extract lat/lon and place metadata
* Pass coordinates to providers

Failures → resolver error.

### 5.2 City + Region

Examples:
* "Wichita, KS"
* "Berlin, DE"

Steps:
1. Parse city and region
2. Query Open‑Meteo Geocoding
3. Extract lat/lon, country code, admin1
4. Pass coordinates to providers

Ambiguous results → resolver error.

### 5.3 Latitude/Longitude

If input matches `"<lat>,<lon>"`:
* Use coordinates directly
* No external resolver

Invalid coordinates → resolver error.

### 5.4 Resolver Summary

| Input Type | Resolver Used | Failure Mode |
| --- | --- | --- |
| ZIP code | Zippopotam.us | Resolver error |
| City/state or city/country | Open‑Meteo Geocoding | Resolver error |
| Lat/lon | None | Resolver error |
| Anything else | Rejected | Resolver error |

---

## 6. Normalization

All provider responses are normalized into a unified schema.

Normalization ensures:
* consistent field names
* consistent units (pre‑conversion)
* consistent timestamps
* consistent metadata
* consistent array structures
* dual‑unit numeric fields
* provider‑agnostic behavior

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
* **moonrise/moonset**
* **moon phase + illumination**
* weathercode
* provider metadata
* **feels‑like fields**
* **index block**

**Alerts are not part of normalization.**
They are fetched after all mode data is gathered and inserted at the root level of the final payload when active.

---

## 7. Merge Layer

### 7.1 Daily Merge
* dewpoint (hourly‑averaged)
* humidity (hourly‑averaged)
* wind gust (hourly max)
* precipitation (provider‑native)
* sunrise/sunset
* **moonrise/moonset**
* **moon phase + illumination**
* weathercode → icon context
* **feels‑like (computed from daily humidity + temp)**

### 7.2 Hourly Merge
* current conditions inserted at index 0
* sunrise/sunset propagated
* **moon data propagated**
* index fields attached
* gust normalization applied
* **feels‑like computed per hour**

**Alerts are not merged into hourly or daily structures.**
They are attached **only at the root level** after all mode data is collected.

---

## 8. Index Engine

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
Daily feels‑like is computed using humidex or heat‑index depending on conditions.

---

## 9. Unit Conversion

Unit conversion is applied after merge and before caching.

Conversions include:
* °C → °F
* m/s → mph
* mm → inches
* hPa → inHg

Conversion rules are:
* mode‑aware
* deterministic
* consistent across providers
* consistent with perfdata output

---

## 10. Caching

The caching subsystem stores:
* current
* hourly
* weekly
* metadata
* provider info
* **alerts (root‑level)**
* cache_id
* cache_age
* cache_written

Caching guarantees:
* stable output
* reproducible results
* reduced provider load
* deterministic fallback behavior

Alerts are cached independently and restored at the root level when present.

---

## 11. Output Modes

### 11.1 Current Mode
* NWS only
* includes station observations
* includes metadata
* includes dual‑unit fields
* **includes feels‑like**
* **includes moon data**
* includes index block

### 11.2 Hourly Mode
* NWS or Open‑Meteo
* includes indexes
* includes sunrise/sunset
* **includes moon data**
* **includes feels‑like**
* always 24 entries

### 11.3 Weekly Mode
* NWS or Open‑Meteo
* includes daily feels‑like
* includes moon data
* always 7 entries

### 11.4 Full Mode

Full Mode includes:
* current
* hourly
* weekly
* sunrise/sunset
* **moonrise/moonset**
* **moon phase + illumination**
* **alerts (root‑level only)**
* feels‑like
* index block
* provider metadata

Alerts **never** appear inside any mode block.

---

## 12. Error Handling

Errors are categorized as:
* resolver errors
* provider errors
* normalization errors
* merge errors
* index errors
* conversion errors
* caching errors
* alert fetch errors (NWS only)

Structured error payloads include:
* failure type
* failure stage
* provider URLs
* resolver path
* timestamps

All errors produce deterministic JSON.

---

## 13. See Also
* [CHANGELOG](CHANGELOG.md)
* [Architecture](Architecture.md)
* [FLAGS.md](../../../docs/FLAGS.md)
* [Metadata_schema.md](Metadata_schema.md)
* [Enforcement](Enforcement.md)
* [Installation](Installation.md)
* [Logging](Logging.md)
* [Provider_Architecture](Provider_Architecture.md)
* [Usage](Usage.md)
