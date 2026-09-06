# Provider Architecture for check_weather v3.0.0

Defines the provider roles and hybrid provider behavior for check_weather v3.0.0.

**Part of:** NMS_Tools Monitoring Suite  
**Document:** Provider Architecture
**Version:** 3.0.0 
**Author:** Leon McClatchey, Linktech Engineering LLC  
**License:** MIT  
**Requires:** Python 3.12+  (development only; not required for frozen binary)
**Last Updated:** 2026-08-16

## Table of Contents
1. [Overview](#1-overview)
2. [Provider Model](#2-provider-model)
    1. [Weather Providers](#21-weather-providers)
    2. [Location Providers](#22-location-providers)
3. [Hybrid Provider Behavior (Current v3.0.0 Model)](#3-hybrid-provider-behavior-current-v300-model)
4. [Provider Selection Flag](#4-provider-selection-flag)
5. [Weather Provider Details](#5-weather-provider-details)
    1. [NWS](#51-nws)
    2. [Open‑Meteo](#52-openmeteo)
6. [Location Provider Details](#6-location-provider-details)
7. [Provider Metadata](#7-provider-metadata)
8. [Deterministic Guarantees](#8-deterministic-guarantees)
9. [Planned Provider Isolation (v3.1+)](#9-planned-provider-isolation-v31)
10. [Examples](#10-examples)
11. [See Also](#11-see-also)

---

## 1. Overview

`check_weather` v3.0.0 uses a multi‑provider weather engine built on `PythonTools.weather`.
The current implementation operates in a **hybrid provider model**, where both NWS and Open‑Meteo may be used depending on mode, field availability, and location type. Provider fallback and strict provider isolation are not yet implemented; these are planned for v3.1+.

All providers feed into a unified normalization layer and produce stable, deterministic output across all modes.

---

## 2. Provider Model

### 2.1 Weather Providers

| Provider | Capabilities | Coverage |
| --- | --- | --- |
| **NWS** | Current, hourly, weekly, station metadata, grid metadata, observations, **alerts** | United States |
| **Open‑Meteo** | Hourly, daily/weekly, dewpoint, humidity, cloudcover, visibility, pressure_msl, precipitation probability | Global |

### 2.2 Location Providers

| Input Type | Provider | Notes |
| --- | --- | --- |
| ZIP code | Zippopotam.us | US ZIP resolution |
| City/state or city/country | Open‑Meteo Geocoding | Global geocoding |
| Latitude/longitude | direct | No provider call |
| NWS station metadata | NWS Points API | Used after initial resolution |

Location resolution always produces latitude, longitude, display name, country code, admin1, and provider metadata.

---

## 3. Hybrid Provider Behavior (Current v3.0.0 Model)

`check_weather` v3.0.0 uses a **hybrid provider model**:

Even when a provider is selected via `--provider`, the engine may pull data from **both NWS and Open‑Meteo** depending on field availability, mode, and location type.

### NWS is used for:
* current conditions
* hourly forecast
* weekly forecast
* station metadata
* grid metadata
* observations
* alerts
* weekly enrichment
* hourly enrichment

### Open‑Meteo is used for:
* geocoding
* ZIP fallback
* dewpoint
* cloudcover
* visibility
* pressure_msl
* precipitation probability

### No provider fallback exists

If NWS fails, the engine does not switch to Open‑Meteo.
If Open‑Meteo fails, the engine does not switch to NWS.
Only cache fallback exists.

**Provider isolation is not yet implemented**

The provider switch is parsed and validated, but does not enforce strict isolation.

---

## 4. Provider Selection Flag
```Code
--provider {nws,open-meteo}
```

### Current behavior (v3.0.0)
* The flag is accepted and validated.
* The selected provider is recorded in metadata.
* The engine may still use both providers depending on field availability.

### Planned behavior (v3.1+)
* Strict provider isolation
* Automatic provider selection based on country
* Optional fallback logic

---

## 5. Weather Provider Details

### 5.1 NWS

#### Base Endpoints
* Points: `https://api.weather.gov/points/<lat>,<lon>`
* Gridpoint forecast: `https://api.weather.gov/gridpoints/<office>/<gridX>,<gridY>/forecast`
* Hourly forecast: `https://api.weather.gov/gridpoints/<office>/<gridX>,<gridY>/forecast/hourly`
* Observations: `https://api.weather.gov/stations/<station>/observations/latest`
* Alerts: `https://api.weather.gov/alerts/active`

#### Metadata Emitted
* nws_office
* grid_x / grid_y
* station_id
* station_name
* observation_url
* forecast_url
* hourly_url
* alerts_url

### 5.2 Open‑Meteo

Base Endpoint:
`https://api.open-meteo.com/v1/forecast`

#### Capabilities
* hourly forecast
* daily/weekly forecast
* dewpoint
* humidity
* cloudcover
* visibility
* pressure_msl
* precipitation probability

#### Metadata Emitted
* openmeteo_url
* hourly_fields
* daily_fields
* timezone
* model metadata

---

## 6. Location Provider Details

### 6.1 ZIP Resolution
Provider: Zippopotam.us
URL: `https://api.zippopotam.us/US/<zip>`

### 6.2 City/Region Resolution
Provider: Open‑Meteo Geocoding
URL: `https://geocoding-api.open-meteo.com/v1/search?name=<query>`

### 6.3 Direct Latitude/Longitude
Provider: direct
Metadata: latitude, longitude

---

## 7. Provider Metadata

All output modes include a provider block containing:

| Field | Description |
| --- | --- |
| provider_selected | Provider chosen via ``--provider`` |
| provider_urls | All URLs used during the run |
| provider_metadata | Provider‑specific metadata |

Removed fields (v2.x only):
`provider_fallback`, `provider_reason`

---

## 8. Deterministic Guarantees

check_weather guarantees:
* deterministic URL construction
* deterministic metadata emission
* deterministic normalization
* deterministic merge logic
* deterministic cache behavior
* no fallback logic
* no silent provider switching
* stable schema across all modes

---

## 9. Planned Provider Isolation (v3.1+)

Future versions will introduce:
* strict provider isolation
* automatic provider selection based on country
* optional fallback logic
* provider‑specific output blocks
* full enforcement of the --provider flag

---

## 10. Examples

### ZIP Input

```Code
Input: 67576
Location Provider: zippopotam.us
Weather Provider (selected): nws
Hybrid Behavior: Open‑Meteo may supply dewpoint/cloudcover/visibility
```

### City Input

```Code
Input: "Saint John, KS"
Location Provider: open-meteo
Weather Provider (selected): nws
Hybrid Behavior: Open‑Meteo supplies geocoding + supplemental fields
```

### Lat/Lon Input

```Code
Input: "38.03,-98.76"
Location Provider: direct
Weather Provider (selected): nws
Hybrid Behavior: Open‑Meteo may supply supplemental fields
```

---

## 11. See Also
* [CHANGELOG](CHANGELOG.md)
* [Architecture](Architecture.md)
* [FLAGS.md](../../../docs/FLAGS.md)
* [Logging.md](Logging.md)
* [Enforcement](Enforcement.md)
* [Installation](Installation.md)
* [Operation](Operation.md)
* [Metadata_schema.md](Metadata_schema.md)
* [Usage](Usage.md)
