# check_weather.py — README v3.0.0

**Part of:** NMS_Tools Monitoring Suite  
**Script:** `check_weather.py`  
**Author:** Leon McClatchey, Linktech Engineering LLC  
**License:** MIT  
**Requires:** Python 3.10+  
**Last Updated:** 2026-08-17

![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/status-stable-brightgreen)
![NMS_Tools](https://img.shields.io/badge/NMS__Tools-weather-blueviolet)

<!-- Provider badges -->
![Weather Provider](https://img.shields.io/badge/provider-Open--Meteo-orange)
![Location Provider](https://img.shields.io/badge/location-Zippopotam.us-blue)
![Location Provider](https://img.shields.io/badge/location-Open--Meteo%20Geocoding-teal)
![Icon Set](https://img.shields.io/badge/icons-Weather%20Icons-orange)

<!-- Capability badges -->
![Hybrid](https://img.shields.io/badge/model-hybrid-blue)
![NWS](https://img.shields.io/badge/augmentation-NWS-red)
![Export](https://img.shields.io/badge/output-JSON%20export-success)
![Index Engine](https://img.shields.io/badge/index-engine-lightgrey)
![Frozen](https://img.shields.io/badge/frozen-PyInstaller-green)

## Table of Contents
1. [Overview](#1-overview)
2. [Quick Start](#2-quick-start)
3. [Provider Architecture (Open‑Meteo + NWS)](#3-provider-architecture-openmeteo--nws)
4. [Deterministic Behavior Guarantees](#4-deterministic-behavior-guarantees)
5. [Icon System](#5-icon-system)
6. [Icon Mapping Table](#6-icon-mapping-table-wmo--context--icon)
7. [Scientific Index Engine](#7-scientific-index-engine)
8. [Output Modes](#8-output-modes)
9. [Usage Examples (All Modes)](#9-usage-examples-all-modes)
10. [Inclusion Flags](#10-inclusion-options)
11. [Cache & Logging](#11-cache--logging)
12. [Frozen Binary Notes](#12-frozen-binary-notes)
13. [Example JSON Schemas](#13-example-json-schemas)
14. [Troubleshooting](#14-troubleshooting)
15. [Features](#15-features)
16. [Current Status](#16-current-status)
17. [Documents](#17-documents)
18. [Tools in This Suite](#18-tools-in-this-suite)
19. [Notes](#19-notes)
20. [License](#20-license)

---

## 1. Overview
`check_weather.py` is an operator‑grade weather monitoring plugin designed for Nagios, Icinga, Thruk, and the broader NMS_Tools suite.

It provides deterministic, timestamp‑aligned weather data using a **hybrid provider model**:
* **Open‑Meteo** → forecast baseline
* **NWS** → station‑level observations
* **Backend merge** → unified, normalized output

The tool supports:
* ZIP, city, and lat/long resolution
* Metric and imperial units
* Threshold evaluation
* Nagios‑compliant perfdata
* JSON and verbose output modes
* Rolling 24‑hour hourly slicing
* Weekly slicing normalization
* Scientific index engine (heat index, humidex, wet bulb, etc.)
* Deterministic caching and logging
* Frozen binary JSON export (--output FILE)

---

## 2. Quick Start

### Basic
```bash
./check_weather.py --location "Saint John, KS"
```

### Imperial units
```bash
./check_weather.py --location 67576 --units imperial
```

### JSON output
```bash
./check_weather.py --location 67576 -j
```

### Verbose
```bash
./check_weather.py --location "Saint John, KS" -v
```

### Hourly (Rolling 24 Hours)
```bash
./check_weather.py --location 67576 -H -v
```

### Weekly (7 Days Starting Today)
```bash
./check_weather.py --location 67576 -W -v
```

---

## 3. Provider Architecture (Open‑Meteo + NWS)

check_weather v3.0.0 uses **two weather providers**:

### A. Open‑Meteo — Primary Forecast Provider

Used for:
* hourly forecast
* daily/weekly forecast
* sunrise/sunset
* WMO weather codes
* cloud cover
* precipitation
* temperature baseline
* wind baseline

Endpoints:
```Code
https://api.open-meteo.com/v1/forecast
https://geocoding-api.open-meteo.com/v1/search
```

### B. NWS — Live Observation Provider

NWS provides **station‑level real‑time observations**, merged into the unified dataset.

NWS contributes:
* temperature
* dewpoint
* humidity
* wind speed
* wind gust
* barometric pressure
* station metadata
* observation timestamps

#### NWS Endpoints Used

check_weather v3.0.0 uses multiple NWS URLs:

1. Points API (lat/lon → grid + station metadata)
```Code
https://api.weather.gov/points/<lat>,<lon>
```

2. Observation Stations (nearest stations)
```Code
https://api.weather.gov/points/<lat>,<lon>/stations
```

3. Latest Observation (primary NWS data source)
```Code
https://api.weather.gov/stations/<stationId>/observations/latest
```

4. Forecast Grid (optional augmentation)

```Code
https://api.weather.gov/gridpoints/<office>/<gridX>,<gridY>/forecast
```

### C. Hybrid Merge Layer

The backend merges Open‑Meteo + NWS into a single normalized dataset.

#### Merge Rules

NWS overrides Open‑Meteo for:
* temperature
* dewpoint
* humidity
* wind speed
* wind gust
* pressure

Open‑Meteo remains authoritative for:
* WMO weather codes
* sunrise/sunset
* cloud cover
* precipitation
* hourly/daily forecast arrays
* Feels‑like selection uses the merged dataset.

#### D. Provider Selection Flag

`--provider` {open-meteo,nws}

This flag is validated but non-functional in v3.0.0.
The backend always uses both providers.

---

## 4. Deterministic Behavior Guarantees

`check_weather` enforces deterministic output across all modes:
* Timestamp alignment
* Rolling hourly slicing (next hour ≥ local time → +24h)
* Weekly slicing (always 7 days starting today)
* Normalized condition text
* Backend‑selected icons
* Rounded numeric values
* Unified feels‑like selection
* Predictable caching
* Operator‑grade logging

---

## 5. Icon System

`check_weather` uses a deterministic, backend‑driven icon mapping based on a curated SVG icon set derived from the **Weather Icons** project by Erik Flowers.
The icons are fully embedded within NMS_Tools and processed through the v3.0.0 classification and recoloring pipeline.

Icons are selected entirely in the backend using:
1. **WMO weather codes**
2. **Sunrise/sunset timestamps**
3. A deterministic mapping table that resolves each WMO code to:
    * a normalized condition text (`context`)
    * a specific icon filename (`icon`)

The UI does not perform any weather logic. It simply renders the icon filename provided by the backend.

### Example (JSON)
```json
{
  "context": "Clear sky",
  "icon": "wi-day-sunny.svg"
}
```

### Day/Night Behavior

Day/night variants are selected using local sunrise/sunset times returned by Open‑Meteo.
Night icons use expressive “alt” variants (e.g., `wi-night-alt-showers.svg`) for clarity.

### Icon Classification & Recoloring

All icons are processed through the v3.0.0 classification pipeline:
* **Filename semantics** (sun, moon, cloud, rain, snow, thunder, fog, wind)
* **Geometry analysis** (sun/moon/cloud detection)
* **Merged classification groups**
* **Deterministic recoloring** via recolor.py

This ensures consistent visual behavior across all modes (current, hourly, weekly) and across all output formats.

### Credit

The base icon shapes originate from the open‑source **Weather Icons** project by Erik Flowers (MIT/SIL OFL).
NMS_Tools ships its own recolored, reclassified SVG variants embedded directly within the system.

---

## 6. Icon Mapping Table (WMO → Context → Icon)

| WMO | Meaning | Context | Icon |
| --- | --- | --- | --- |
| 0 | Clear sky | Clear sky | wi-day-sunny.svg / wi-night-clear.svg |
| 1 | Mainly clear | Mainly clear | wi-day-sunny.svg / wi-night-clear.svg |
| 2 | Partly cloudy | Partly cloudy | wi-day-cloudy.svg / wi-night-alt-cloudy.svg |
| 3 | Overcast | Overcast | wi-cloudy.svg / wi-night-cloudy.svg |
| 45,48 | Fog | Fog | wi-fog.svg / wi-night-fog.svg |
| 51–55 | Drizzle | Drizzle | wi-sprinkle.svg / wi-night-alt-sprinkle.svg |
| 61–65 | Rain | Rain | wi-rain.svg / wi-night-alt-rain.svg |
| 80–82 | Rain showers | Rain showers | wi-showers.svg / wi-night-alt-showers.svg |
| 71–75 | Snow | Snow | wi-snow.svg / wi-night-alt-snow.svg |
| 85–86 | Snow showers | Snow showers | wi-snow.svg / wi-night-alt-snow.svg |
| 95 | Thunderstorm | Thunderstorm | wi-thunderstorm.svg / wi-night-alt-thunderstorm.svg |
| 96–99 | Thunderstorm w/ hail | Thunderstorm (hail) | wi-hail.svg / wi-night-alt-hail.svg |

---

## 7. Scientific Index Engine

check_weather computes:
* Heat index
* Wind chill
* Humidex
* Wet bulb temperature
* Vapor pressure
* Saturation vapor pressure
* Mixing ratio
* Specific humidity
* Air density
* Pressure altitude

Feels‑like selection uses:
* heat index
* wind chill
* humidex
* temperature (fallback)

Exposed as:
```Code
feels_like_source
```

---

## 8. Output Modes

### Output Modes
* `-v`, `--verbose` — Verbose output
* `-j`, `--json` — JSON output
* `-q`, `--quiet` — Quiet (exit code only)
* `--color` — Colorize verbose
* `--output FILE` — Write output to file

### Weather Modes
* `--weekly` — Weekly forecast
* `--hourly` — Hourly forecast
* `--full` — Current + hourly + weekly

### Implicit Mode
* **Current mode** — Default when no weather mode is specified

### Nagios Mode
* Default output style
* Single-line status + perfdata
* Logging disabled

---

## 9. Usage Examples (All Modes)

### Current Mode
```bash
check_weather --location 67576
check_weather --location 67576 -v
check_weather --location 67576 -j
```

###Hourly Mode
```bash
check_weather --location 67576 --hourly -v
check_weather --location 67576 --hourly -j
```

### Weekly Mode
```bash
check_weather --location 67576 --weekly -v
check_weather --location 67576 --weekly -j
```

### Full Mode
```bash
check_weather --location 67576 --full -j
check_weather --location 67576 --full -j --output weather.json
```

### Nagios Mode
```bash
check_weather --location 67576
check_weather --location 67576 -q
```

### Verbose Mode
```bash
check_weather --location 67576 -v
```

### JSON Mode
```bash
check_weather --location 67576 -j
```

### Quiet Mode
```bash
check_weather --location 67576 -q
```

### Threshold Example
```bash
check_weather --lat 38.00 --lon -98.76 --warning-temp 30
```

### Show Provider Details
```bash
check_weather --location 67576 --show-location-details
```

### Logging
```bash
check_weather --location 67576 --log-dir ~/Logs
```

---

## 10. Inclusion Options
```Code
--include-gusts
--include-precip
--include-clouds
```

---

## 11. Cache & Logging

### Cache Flags
```Code
--ignore-cache
--ignore-ttl
--cache-info
--force-cache
```

### Logging

Disabled in Nagios mode.
Enabled in verbose, JSON, quiet.

---

## 12. Frozen Binary Notes

Frozen binaries:
* bypass stdout
* require --output FILE
* write relative paths into PyInstaller extraction directory
* deterministic behavior across environments

---

## 13. Example JSON Schemas

###  Current
```json
{
  "status": "OK",
  "message": "Weather normal: 56.66°F, 20.26 mph",
  "location": "Saint John, Kansas 67576, US",
  "data": {
    "time": "2026-04-11T09:45",
    "temperature_f": 56.66,
    "wind_mph": 20.26,
    "humidity": 31,
    "cloudcover": 54,
    "condition_text": "Partly cloudy",
    "source": "Live API"
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
    "longitude": -98.7647
  },
  "runtime_ms": 763.0
}
```

### Hourly (Rolling 24 Hours)

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
        "context": "Overcast",
        "icon": "wi-cloudy.svg"
      },
      ...
    ],
    "units": "imperial",
    "source": "Live API"
  }
}
```

### Weekly (7 Days Starting Today)

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
        "context": "Fog",
        "icon": "wi-night-fog.svg"
      },
      ...
    ],
    "units": "imperial",
    "source": "Live API"
  }
}
```

---

## 14. Troubleshooting
* Stale cache → `--ignore-cache`
* Provider outage → clean error messages
* Missing NWS fields → fallback logic
* Pressure MSL TypeError → fixed in v3.0.0

---

## 15. Features

### Dual‑Provider Hybrid Model
* Open‑Meteo for forecast baseline
* NWS for live station‑level observations
* Deterministic merge layer with override rules

### Multiple Weather Modes
* Current
* Hourly
* Weekly
* Full

### Deterministic Output Pipeline
* Timestamp alignment
* Normalized condition text
* Backend‑selected icons
* Unified feels‑like selection
* Rounded numeric values

### Scientific Index Engine
* Heat index
* Wind chill
* Humidex
* Wet bulb
* Vapor pressure
* Air density
* Pressure altitude

### Icon Classification & Recoloring
* Derived from Weather Icons
* Fully embedded SVG set
* Deterministic day/night selection
* Geometry‑based classification

### Robust CLI Modes
* Verbose
* JSON
* Quiet
* Nagios‑compatible
* Colorized verbose output

### Frozen Binary Support
* Deterministic PyInstaller builds
* `--output FILE` JSON export
* Stable across environments

### Debug & Diagnostics
* `--debug`
* `--self-test`
* `--show-location-details`
* Cache inspection flags

### Production‑Ready
* Logging architecture stable
* Threshold evaluation
* Perfdata output
* Fully compatible with PythonTools
* Included in NMS_Tools packaging

---

## 16. Current Status
* ✔ Fully compatible with PythonTools
* ✔ Deterministic dual‑provider routing (Open‑Meteo + NWS)
* ✔ Current / Hourly / Weekly / Full modes finalized
* ✔ Verbose / JSON / Nagios / Quiet modes stable
* ✔ Logging architecture stable
* ✔ Frozen mode enabled via scripts/build.py
* ✔ Included in NMS_Tools packaging
* ✔ Suitable for production monitoring environments

---

## 17. Documents

| Document | Description |
|----------|-------------|
| [Installation.md](docs/Installation.md) | Installation and environment setup |
| [Usage.md](docs/Usage.md)        | Full CLI reference and examples |
| [Operation.md](docs/Operation.md)    | Discovery, normalization, and output pipeline |
| [Enforcement.md](docs/Enforcement.md)  | Status evaluation and filtering logic |
| [Metadata_schema.md](docs/Metadata_schema.md) | Normalized interface schema |

---

## 18. Tools in This Suite
| Tool | Description | Documentation |
|------|-------------|---------------|
| **check_cert** | TLS certificate inspection and expiration validation | [../check_cert/README.md](../check_cert/README.md) |
| **check_html** | HTTP/HTTPS content validation and deterministic HTML checks | [../check_html/README.md](../check_html/README.md) |
| **check_interfaces** | Network interface inspection and operational state reporting | [../check_interfaces/README.md](../check_interfaces/README.md) |
| **check_ports** | Port and service availability inspection | [../check_ports/README.md](../check_ports/README.md) |
| **check_weather** | Deterministic weather client for monitoring pipelines | [../check_weather/README.md](../check_weather/README.md) |
| **check_ticker** | Deterministic market/ticker client using PythonTools finance providers | - |

---

## 19. Notes
* All numeric values rounded to 2 decimals
* Designed for graphing (PNP4Nagios, Grafana)
* Logging, caching, and condition‑text support fully implemented

A standalone HTML/JS/CSS weather demo is included in the weather_demo/ directory.
It is not part of NMS_Tools and is not used by any monitoring scripts.
It is provided only as a visual demonstration of how the JSON output can be rendered.

---

## 20. License
* Source code: MIT [LICENSE](../../LICENSE) for details.
* Frozen binary: Proprietary [LICENSE_BINARY](../../LICENSE_BINARY.txt)
