# Provider Architecture
**Part of:** NMS_Tools Monitoring Suite
**Script:** check_weather.py  
**Author:** Leon McClatchey, Linktech Engineering LLC
**License:** MIT
**Last Updated:** 2026‑08‑15

This document defines the provider architecture for the check_weather subsystem in **NMS_Tools v2.0.0**, including provider selection rules, resolver behavior, provider capabilities, metadata guarantees, and fallback logic. It reflects the redesigned multi‑provider engine introduced in the v2 series.

The system is designed for deterministic, operator‑grade monitoring and produces stable, provider‑agnostic output across all modes.

## Table of Contents
1. [Overview](#1-overview)
2. [Provider Model](#2-provider-model)
    * [Weather Providers](#21-weather-providers)
    * [Location Providers](#22-location-providers)
3. [Provider Selection Rules](#3-provider-selection-rules)
4. [Weather Provider Details](#4-weather-provider-details)
    * [NWS](#41-nws)
    * [Open‑Meteo](#42-openmeteo)
5. [Location Provider Details](#5-location-provider-details)
    * [ZIP Resolution](#51-zip-resolution)
    * [City/Region Resolution](#52-cityregion-resolution)
    * [Direct Latitude/Longitude](#53-direct-latitudelongitude)
6. [Provider Metadata](#6-provider-metadata)
7. [Fallback Behavior](#7-fallback-behavior)
8. [Deterministic Guarantees](#8-deterministic-guarantees)
9. [Examples](#9-examples)

## 1. Overview
The v2.0.0 provider architecture separates:
* **weather retrieval**
* **location resolution**
* **provider selection**
* **provider fallback**
* **provider metadata emission**

All providers map into a unified schema through the normalization layer.

The system is fully deterministic and produces stable output across all modes (current, hourly, weekly).

## 2. Provider Model
### 2.1 Weather Providers

| Provider | Capabilities | Coverage |
| --- | --- | --- |
| **NWS** | Current, hourly, weekly, station metadata, observations, alerts (planned) | United States |
| **Open‑Meteo** | Hourly, daily/weekly, dewpoint/humidity, sunrise/sunset, astronomy (planned), alerts (optional) | Global |

Both providers feed into the same normalization and merge layers.

### 2.2 Location Providers

| Input Type | Provider | Notes |
| --- | --- | --- |
| ZIP code | Zippopotam.us | US ZIP resolution |
| City/state or city/country | Open‑Meteo Geocoding | Global geocoding |
| Latitude/longitude | None | Direct coordinates |
| NWS station metadata | NWS Points API | Used after initial resolution |

Location resolution always produces:
* latitude
* longitude
* display name
* country code
* admin1 (state/province)
* provider metadata

## 3. Provider Selection Rules
Provider selection follows deterministic rules:
1. **If NWS coverage exists for the location → prefer NWS.**
2. If NWS fails or is unavailable → fallback to Open‑Meteo.
3. If both providers fail → fallback to cached data.
4. If no cache exists → return error.

Selection is logged in metadata:

```Code
provider_selected
provider_fallback
provider_reason
```

## 4. Weather Provider Details
### 4.1 NWS
**Base Endpoints**
* Points:
  `https://api.weather.gov/points/<lat>,<lon>`
* Gridpoint forecast:
  `https://api.weather.gov/gridpoints/<office>/<gridX>,<gridY>/forecast`
* Hourly forecast:
  `https://api.weather.gov/gridpoints/<office>/<gridX>,<gridY>/forecast/hourly`
* Observations:
  `https://api.weather.gov/stations/<station>/observations/latest`
* Alerts (planned):
  `https://api.weather.gov/alerts/active`

**Metadata Emitted**
* nws_office
* grid_x / grid_y
* station_id
* station_name
* observation_url
* forecast_url
* hourly_url

NWS provides the highest‑resolution US data.

### 4.2 Open‑Meteo
Base Endpoint

```Code
https://api.open-meteo.com/v1/forecast
```

**Capabilities**
* hourly forecast
* daily/weekly forecast
* dewpoint/humidity
* sunrise/sunset
* astronomy (planned)
* alerts (optional)

**Metadata Emitted**
* openmeteo_url
* hourly_fields
* daily_fields
* timezone
* model metadata

Open‑Meteo provides global coverage and consistent physics.

## 5. Location Provider Details
### 5.1 ZIP Resolution
Used when input matches:

```Code
^\d{5}$
```

**Provider:** Zippopotam.us
#### URL:

```Code
https://api.zippopotam.us/US/<zip>
```

**Metadata Emitted**
* location_provider: "zippopotam.us"
* location_provider_url
* city
* state
* country
* latitude
* longitude

### 5.2 City/Region Resolution
Used when input is not a ZIP and not lat/lon.

**Provider:** Open‑Meteo Geocoding
#### URL:

```Code
https://geocoding-api.open-meteo.com/v1/search?name=<query>
```

**Metadata Emitted**
* location_provider: "open-meteo"
* location_provider_url
* city
* admin1
* country_code
* latitude
* longitude

### 5.3 Direct Latitude/Longitude
Used when input matches:

```Code
<lat>,<lon>
```

**Provider:** direct
**Metadata Emitted**
* location_provider: "direct"
* location_provider_url: null
* latitude
* longitude

## 6. Provider Metadata
All output modes include a `provider` block containing:
| Field | Description |
| --- | --- |
| provider_selected | "nws" or "open-meteo" |
| provider_fallback | true/false |
| provider_reason | Why the provider was selected |
| provider_urls | All URLs used |
| provider_capabilities | Capabilities of the selected provider |
| provider_metadata | Provider‑specific metadata |

This block is stable and schema‑aligned.

## 7. Fallback Behavior
Fallback behavior is deterministic:
1. Try NWS
2. If NWS fails → try Open‑Meteo
3. If Open‑Meteo fails → use cached data
4. If cache missing → error

Fallback reasons include:
* provider timeout
* provider HTTP error
* missing fields
* normalization failure
* merge failure
* location outside NWS coverage

Fallback is logged in metadata.

## 8. Deterministic Guarantees
`check_weather` guarantees:
* deterministic provider selection
* deterministic fallback behavior
* deterministic URL construction
* deterministic metadata emission
* no randomization
* no silent provider switching
* no ambiguous provider names
* stable schema across all modes

These guarantees ensure predictable monitoring behavior across all supported platforms.

## 9. Examples
### ZIP Input

```Code
Input: 67576
Location Provider: zippopotam.us
Weather Provider: nws (preferred)
Fallback: open-meteo if NWS fails
```

### City Input

```Code
Input: "Saint John, KS"
Location Provider: open-meteo
Weather Provider: nws (preferred)
```

### Lat/Lon Input
```Code
Input: "38.03,-98.76"
Location Provider: direct
Weather Provider: nws (preferred)
```

**End of Provider_Architecture.md**