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
![Icon Set](https://img.shields.io/badge/icons-Weather%20Icons-orange)

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

## Icon System

check_weather.py uses a deterministic, backend‑driven icon mapping based on the
**Weather Icons** project by Erik Flowers:

- Project: https://erikflowers.github.io/weather-icons/
- License: SIL OFL 1.1 (fonts), MIT (CSS)
- Icon files used: SVG variants (e.g., `wi-day-sunny.svg`, `wi-night-cloudy.svg`)

### How Icons Are Selected

Icons are selected entirely in the backend using:

1. **WMO weather codes** from Open‑Meteo  
2. **Sunrise/sunset timestamps** to determine day vs. night  
3. A deterministic mapping table that resolves each WMO code to:
   - a normalized condition text (`context`)
   - a specific icon filename (`icon`)

### Why This Matters

- The UI does not perform any weather logic.
- The UI only renders the icon filename provided by the backend.
- All modes (current, hourly, weekly) use the same mapping.
- Icons are guaranteed to be consistent across all output formats.

### Example (JSON)

```json
{
  "context": "Clear sky",
  "icon": "wi-day-sunny.svg"
}
```

### Night Icon Behavior
Nighttime icons are selected using the local sunrise/sunset times returned by Open‑Meteo.
The backend supports expressive “alt” night icons (e.g., wi-night-alt-showers.svg)
for improved clarity.

## Icon Mapping Table (WMO → Context → Icon)

check_weather.py uses a deterministic mapping from **WMO weather codes** to:

- a normalized condition text (`context`)
- a specific icon filename (`icon`)

This ensures consistent behavior across current, hourly, and weekly modes.

### Core WMO Mappings

| WMO Code | Meaning                         | Context Text               | Icon Filename               |
|----------|----------------------------------|-----------------------------|------------------------------|
| 0        | Clear sky                        | Clear sky                  | wi-day-sunny.svg / wi-night-clear.svg |
| 1        | Mainly clear                     | Mainly clear               | wi-day-sunny.svg / wi-night-clear.svg |
| 2        | Partly cloudy                    | Partly cloudy              | wi-day-cloudy.svg / wi-night-alt-cloudy.svg |
| 3        | Overcast                         | Overcast                   | wi-cloudy.svg / wi-night-cloudy.svg |
| 45, 48   | Fog / Depositing rime fog        | Fog                        | wi-fog.svg / wi-night-fog.svg |
| 51–55    | Drizzle (light–dense)            | Drizzle                    | wi-sprinkle.svg / wi-night-alt-sprinkle.svg |
| 61–65    | Rain (light–heavy)               | Rain                       | wi-rain.svg / wi-night-alt-rain.svg |
| 80–82    | Rain showers (light–violent)     | Rain showers               | wi-showers.svg / wi-night-alt-showers.svg |
| 71–75    | Snow (light–heavy)               | Snow                       | wi-snow.svg / wi-night-alt-snow.svg |
| 85–86    | Snow showers                     | Snow showers               | wi-snow.svg / wi-night-alt-snow.svg |
| 95       | Thunderstorm                     | Thunderstorm               | wi-thunderstorm.svg / wi-night-alt-thunderstorm.svg |
| 96–99    | Thunderstorm w/ hail             | Thunderstorm (hail)        | wi-hail.svg / wi-night-alt-hail.svg |

### Day vs. Night Icons

The backend determines day/night using:

- `sunrise`
- `sunset`
- the timestamp of the forecast entry

This ensures correct icon selection even for:

- hourly forecasts crossing midnight  
- weekly forecasts with sunrise/sunset per day  
- verbose and JSON modes  

### Why Only These Icons?

The Weather Icons project includes hundreds of icons, but check_weather uses a **minimal, deterministic subset** to avoid ambiguity and ensure consistent UI rendering.

## Design Rationale: Backend‑Driven Icon Selection

### Why the Backend Selects Icons

Weather icons are not a UI concern — they are a **data normalization concern**.

The backend selects icons because:

1. **WMO codes require interpretation**  
   The UI should not need to understand meteorology or WMO classification.

2. **Day/night logic requires sunrise/sunset timestamps**  
   Only the backend has access to:
   - the location’s timezone  
   - the day’s sunrise/sunset  
   - the forecast timestamp  

3. **Consistency across modes**  
   Current, hourly, and weekly modes all use the same mapping table.

4. **Deterministic output**  
   The UI receives:
   ```json
   { "context": "Clear sky", "icon": "wi-day-sunny.svg" }
   ```

5. Separation of concerns
  * Backend: meteorology, normalization, mapping
  * UI: display only

### Why Weather Icons?

The Weather Icons project was chosen because:

* It is open‑source (MIT + SIL OFL 1.1)
* It provides a complete set of day/night variants
* It is widely used and stable
* It matches the operator‑grade aesthetic of NMS_Tools
* SVG format ensures crisp rendering at any size

### Why Not Use Provider Icons?

Open‑Meteo does not provide icons.

Other providers (e.g., OpenWeatherMap) do, but:

* They are raster PNGs
* They are low‑resolution
* They are provider‑specific
* They do not include night variants
* They cannot be redistributed freely

Weather Icons solves all of these problems.

### Why Not Let the UI Choose Icons?

Because that leads to:

* duplicated logic
* inconsistent behavior
* mismatched day/night handling
* drift between UI and backend
* increased maintenance burden

The backend is the single source of truth.

--- 

## What’s New in v2.2.0 (2026‑04‑27)

### Rolling 24‑Hour Hourly Forecast
Hourly mode now begins at the **next hour ≥ local time**, not at midnight.  
The backend slices the raw Open‑Meteo hourly arrays before flattening, ensuring:

- Always 24 hours of future data  
- No stale hours  
- No midnight anchoring  
- Deterministic alignment across all hourly fields  

### Weekly Forecast Normalization
Weekly mode now always begins at **today**, even if the provider returns yesterday.  
The backend slices the raw daily arrays before enrichment.

- Always 7 days  
- Never includes yesterday  
- Fully enriched (context, icon, wind max, units)

### Backend Enrichment
All modes now include normalized, deterministic fields:

- `context` — human‑readable condition text  
- `icon` — backend‑selected icon filename  
- `wind_mph_max` / `wind_kph_max` — weekly max wind  
- Unit‑converted fields for temperature, wind, visibility, pressure, precipitation  

Verbose mode uses these enriched fields directly.

## Features

### Full hourly weather data

- Temperature
- Wind speed
- Wind gusts
- Humidity
- Precipitation
- Cloud cover
- Weather condition codes + text
- Rolling 24‑hour forecast window (next hour → +24h)

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
- Rolling hourly slicing and weekly day‑slicing performed in fetch layer
- Backend‑normalized condition text and icon filenames

### Dependencies

Requires:

- **Python 3.8+**
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
### Hourly Mode (Rolling 24 Hours)

Hourly mode now returns the next 24 hours starting from the next hour ≥ local time.

```bash
./check_weather.py --location 67576 -v -H
```

### Weekly Mode (7 Days Starting Today)
Weekly mode now always returns 7 days beginning at the current local date.

```bash
./check_weather.py --location 67576 -W -v
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

## Upcoming Enhancements

The following features are planned for the next release:

- Verbose mode will display icon filenames next to condition text.
- New `--debug` flag will expose backend decision details (slice indices, sunrise/sunset logic, WMO mappings).
- New `--self-test` mode will validate slicing, enrichment, and mapping without hitting the API.
- Minutely precipitation support (`--minutely`) for short‑term rain alerts.
- Alerts mode (`--alerts`) using Open‑Meteo NWS alert feed for US locations.

---

## Notes

- Uses Open‑Meteo hourly API for deterministic, timestamp‑aligned data
- Uses Zippopotam.us + Open‑Meteo Geocoding for location resolution
- All numeric values rounded to 2 decimals
- Designed for graphing (PNP4Nagios, Grafana, etc.)
- Logging, caching, and condition‑text support fully implemented