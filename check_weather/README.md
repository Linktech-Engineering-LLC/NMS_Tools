# check_weather.py
Deterministic Weather Monitoring Plugin for *NMS_Tools*

![Python](https://img.shields.io/badge/python-3.6%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/status-stable-brightgreen)
![NMS_Tools](https://img.shields.io/badge/NMS__Tools-weather-blueviolet)

<!-- Provider badges -->
![Weather Provider](https://img.shields.io/badge/provider-Open--Meteo-orange)
![Location Provider](https://img.shields.io/badge/location-Zippopotam.us-blue)
![Location Provider](https://img.shields.io/badge/location-Open--Meteo%20Geocoding-teal)

## Overview

**check_weather.py** is an operator‑grade weather monitoring plugin designed for Nagios, Icinga, Thruk, and the broader NMS_Tools suite.

It provides deterministic, timestamp‑aligned weather data using the Open‑Meteo hourly API, with full support for:

- ZIP, city, and lat/long resolution
- Metric and imperial units
- Threshold evaluation
- Nagios‑compliant perfdata
- JSON and verbose output modes
- Wind, gusts, humidity, precipitation, cloud cover
- Condition codes + human‑readable condition text
- Deterministic caching and logging

This tool is built for reliability, clarity, and long‑term maintainability.

## Features

### Full hourly weather data

- Temperature
- Wind speed
- Wind gusts
- Humidity
- Precipitation
- Cloud cover
- Weather condition codes + text

### Flexible location resolution

- ZIP code
- City + optional state
- Latitude/longitude

### Threshold support

- Temperature (hot/cold)
- Wind
- Gust
- Humidity
- Precipitation
- Cloud cover

### Multiple output modes

- Nagios
- JSON
- Verbose
- Quiet

### Deterministic behavior

- Timestamp alignment
- Rounded numeric values
- Clean error handling
- Predictable caching
- Operator‑grade logging

### Dependencies

Requires:

- **Python 3.6+**
- **requests**

Install:

```bash
pip install requests
```

## Usage

### Basic
```bash
./check_weather.py --location "Saint John, KS"
```

### Imperial units

```bash
./check_weather.py --location "Saint John, KS" --units imperial
```

### JSON output

```bash
./check_weather.py --location 67576 -j
```

### Verbose output

```bash
./check_weather.py --location "Saint John, KS" -v
```

### Threshold example

```bash
./check_weather.py --location 67576 \
  --warning-wind 25 \
  --critical-wind 35 \
  --warning-gust 40 \
  --critical-gust 50
```

### Show provider URL + resolved location

```bash
./check_weather.py --location 67576 --show-location-details
```

### Logging

```bash
./check_weather.py --location 67576 --log-dir ~/Logs
```

## Provider Architecture

check_weather.py uses **three distinct provider components**:

### Weather Provider

- **Open‑Meteo**
- Selected via --provider (validated enum)
- Base URL:
   [https://api.open-meteo.com/v1/forecast]
- Used for all weather data retrieval.

### Location Provider (ZIP)

- **Zippopotam.us**
- URL pattern:
   [https://api.zippopotam.us/<country>/<zip>]

### Location Provider (City/State)

- **Open‑Meteo Geocoding**
- URL pattern:
   [https://geocoding-api.open-meteo.com/v1/search?name=<city>]

The resolved location block includes:

- Provider name
- Provider URL
- Latitude / longitude
- Resolved city, state, country

These appear in both JSON (resolved_location) and verbose (--show-location-details) output.

### Provider Selection

```bash
--provider {open-meteo}
```

The provider flag is validated but currently non‑functional.

check_weather always uses:
- **Zippopotam.us** for ZIP → lat/lon
- **Open‑Meteo Geocoding** for city/state
- **Open‑Meteo** for weather data

The [--provider] value is logged for operator visibility but does not change execution behavior.
Reserved for future multi‑provider support.

## Inclusion Flags

```bash
--include-gusts     Include wind gusts even without thresholds  
--include-precip    Include precipitation fields  
--include-clouds    Include cloud cover fields  
```

These flags control which fields appear in:

- Verbose output
- JSON output
- Perfdata

## Cache Flags

```bash
--force-cache       Force reading from cache even if API is available  
--ignore-cache      Ignore cache entirely  
--ignore-ttl        Ignore TTL when reading cache  
--cache-info        Display cache metadata  
```

## Logging

**Logging is disabled in Nagios mode.**
Nagios mode is the default output mode, and plugins must remain side‑effect‑free.
Logging only activates when using --verbose, --json, or --quiet.

Enable logging:

```bash
--log-dir /path/to/logs
```

Log entries include:

- [START] metadata banner
- [WEATHER] location + weather blocks
- [RESULT] final Nagios state + message
- [END] termination marker

Rotation controlled by:

```bash
--log-max-mb <size>
```

## Example Outputs

### Nagios

```bash
OK: Weather normal: 56.66°F, 20.26 mph | temp=56.66;; wind=20.26;; humidity=31.00;; cloud=54.00;;
```

### Verbose

```bash
Location Resolution Details:
  Input: 67576
  Location Provider: zippopotam.us
  Location Provider URL: https://api.zippopotam.us/US/67576
  Weather Provider: open-meteo
  Weather Provider URL: https://api.open-meteo.com/v1/forecast
  Resolved Name: Saint John, Kansas, US
  Latitude: 38.0309
  Longitude: -98.7647
  Weather API URL: https://api.open-meteo.com/v1/forecast?latitude=...

Status: OK
Message: Weather normal: 56.66°F, 20.26 mph
Location: Saint John, Kansas 67576, US
Temperature: 56.66°F (13.70°C)
Wind Speed: 20.26 mph (32.60 kph)
Humidity: 31.00%
Condition: Partly cloudy
Source: Live API
```

### JSON

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

## Notes

- Uses Open‑Meteo hourly API for deterministic, timestamp‑aligned data
- Uses Zippopotam.us + Open‑Meteo Geocoding for location resolution
- All numeric values rounded to 2 decimals
- Designed for graphing (PNP4Nagios, Grafana, etc.)
- Logging, caching, and condition‑text support fully implemented