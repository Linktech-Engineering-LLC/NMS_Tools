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

check_weather.py is an operator‑grade weather monitoring plugin designed for Nagios, Icinga, Thruk, and the broader NMS_Tools suite.
It provides deterministic, timestamp‑aligned weather data using the Open‑Meteo hourly API, with full support for:

* ZIP, city, and lat/long resolution
* Metric and imperial units
* Threshold evaluation
* Nagios‑compliant perfdata
* JSON and verbose output modes
* Wind, gusts, humidity, precipitation, cloud cover
* Condition codes (with human‑readable mapping coming next session)

This tool is built for reliability, clarity, and long‑term maintainability.

## Features

* *Full hourly weather data*

 * Temperature
 * Wind speed
 * Wind gusts
 * Humidity
 * Precipitation
 * Cloud cover
 * Weather condition codes

* *Flexible location resolution*

 * ZIP code
 * City + optional state
 * Latitude/longitude

* *Threshold support*

 * Temperature (hot + cold)
 * Wind
 * Gust
 * Humidity
 * Precipitation
 * Cloud cover

* *Multiple output modes*

 * Nagios
 * JSON
 * Verbose
 * Quiet

* *Deterministic behavior*

 * Timestamp alignment
 * Rounded numeric values
* Clean error handling

---

## Dependencies

This tool requires:

- **Python 3.6+**
- **requests** (for Zippopotam.us + Open‑Meteo Geocoding)

Install:

```bash
pip install requests

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
./check_weather.py --location "Saint John, KS" --show-location-details
```

## Example Outputs

### Nagios

```Code
OK: Weather normal: 70.52°F, 16.59 mph | temp=70.52;; wind=16.59;; gust=21.00;; humidity=26.00;; precip=0.00;; cloud=100.00;;
```

### Verbose

```Code
Temperature: 70.52°F (21.40°C)
Wind Speed: 16.59 mph (26.70 kph)
Wind Gust: 21.00 mph (33.80 kph)
Humidity: 26.00%
Precipitation: 0.00 mm (0.00 in)
Cloud Cover: 100.00%
Condition Code: 3
```
### JSON

```jso{
  "temperature_f": 70.52,
  "wind_mph": 16.59,
  "wind_gust_mph": 21.00,
  "precip_in": 0.00,
  "cloudcover": 100,
  "humidity": 26,
  "condition": 3
}
```

## Notes

* Uses *Open‑Meteo hourly API* for deterministic, timestamp‑aligned data
* Uses Zippopotam.us for ZIP resolution
* Uses Open‑Meteo Geocoding for city/state resolution
* All numeric values rounded to 2 decimals
* Designed for graphing (PNP4Nagios, Grafana, etc.)
* Logging and condition‑text enhancements scheduled for next session