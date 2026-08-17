# Usage for check_weather v3.0.0

**Part of:** NMS_Tools Monitoring Suite  
**Script:** export_icons.py  
**Version:** 3.0.0  
**Author:** Leon McClatchey, Linktech Engineering LLC  
**License:** MIT  
**Last Updated:** 2026‑08‑16

`check_weather` retrieves current, hourly, and weekly weather data using a deterministic multi‑provider engine (NWS + Open‑Meteo). It resolves locations, normalizes provider fields, merges hourly/daily data, computes meteorological indexes, applies unit conversion, and outputs structured JSON suitable for CLI, CGI, dashboards, and automation.

This document describes all CLI flags, output modes, examples, and integration notes for **NMS_Tools v2.0.0.**

## Table of Contents
1. [Basic Invocation](#1-basic-invocation)
2. [Command‑Line Options](#2-commandline-options)
3. [Output Modes](#3-output-modes)
4. [Location Formats](#4-location-formats)
5. [Examples](#5-examples)
6. [Provider Selection](#6-provider-selection)
7. [Caching Behavior](#7-caching-behavior)
8. [Error Handling](#8-error-handling)
9. [Deterministic Guarantees](#9-deterministic-guarantees)

## 1. Basic Invocation
```bash
check_weather.py -l "<location>"
```
The <location> may be:
* `"Wichita, KS"`
* `"Berlin, DE"`
* `"67576"`
* `"38.0,-98.7"`

The resolver determines the correct provider and emits full metadata.

## 2. Command‑Line Options
### Required
```Code
-l, --location <value>
```
Location string to resolve.

### Mode Selection
```Code
--current     Output current conditions
--hourly      Output hourly forecast
--weekly      Output weekly forecast
--full        Output full merged structure (planned)
```
If no mode is provided, --current is used.

### Output Format
```Code
--nagios      Nagios/Icinga single-line output (default)
--json -j        Structured JSON
--verbose -v     Multi-line diagnostic output
--quiet -q      Exit code only (no output)
```
If no mode is provided, **Nagios/Icinga mode is used.**

### Provider Control (Optional)
```Code
--provider nws
--provider open-meteo
```
Behavior:
* If no provider is specified, the engine defaults to NWS.
* If NWS is unavailable or fails, the engine falls back to Open‑Meteo.
* If both providers fail, the engine falls back to cache.
* If no cache exists, the engine returns an error (or UNKNOWN in Nagios mode).

This matches the actual v2.0.0 provider architecture.

Caching Options
```Code
--no-cache        Disable cache read/write
--cache-info      Show cache metadata only
```
Caching is enabled by default.

## 3. Output Modes
### 3.1 Nagios/Icinga Mode (default)
Produces:

```Code
OK - Temp 72°F, Wind 8 mph, Gust 12 mph | temp=72 wind=8 gust=12 precip=0 clouds=20
```
Characteristics:
* single line
* status text at beginning
* perfdata always included
* thresholds applied
* exit codes follow Nagios/Icinga conventions

### 3.2 JSON Mode
Produces structured JSON including:
* normalized fields
* merged hourly/daily data
* index computation
* provider metadata
* resolver metadata
* cache metadata

Recommended for dashboards, CGI, and automation.

### 3.3 Verbose Mode
Adds:
* resolver path
* provider URLs
* raw provider fields
* normalized fields
* merge behavior
* index computation
* threshold evaluation
* cache metadata

Verbose mode is multi‑line and intended for diagnostics.

### 3.4 Quiet Mode
```Code
--quiet
```

Produces no output, only an exit code.

Useful for:
* shell scripting
* automation
* conditional logic
* silent monitoring checks

## 4. Location Formats
### ZIP Code
```Code
check_weather.py -l 67576
```
Uses Zippopotam.us → NWS/Open‑Meteo.

### City + Region
```Code
check_weather.py -l "Wichita, KS"
```
Uses Open‑Meteo Geocoding → NWS/Open‑Meteo.

### Latitude/Longitude
```Code
check_weather.py -l "38.0,-98.7"
```
Uses coordinates directly.

## 5. Examples
### Default (Nagios/Icinga)
```bash
check_weather -l "Wichita, KS"
```
### JSON Output
```bash
check_weather -l "Berlin, DE" --json
```
### Verbose Diagnostic Output
```bash
check_weather -l "Wichita, KS" --hourly --verbose
```
### Quiet Mode
```bash
check_weather -l "Wichita, KS" --quiet
```
### Weekly Forecast
```bash
check_weather -l "Wichita, KS" --weekly
```
### Force Open‑Meteo
```bash
check_weather -l "Berlin, DE" --provider open-meteo
```

## 6. Provider Selection
The engine selects providers deterministically:
1. Prefer NWS when coverage exists
2. Fallback to Open‑Meteo
3. Fallback to cache
4. Error if no cache exists

Provider metadata includes:
* provider_selected
* provider_fallback
* provider_reason
* provider_urls

## 7. Caching Behavior
Caching stores:
* current
* hourly
* weekly
* metadata
* provider info
* cache_id
* cache_age

Cache is used when:
* provider fails
* provider is unreachable
* user requests cache info

## 8. Error Handling
Errors include:
* resolver errors
* provider errors
* normalization errors
* merge errors
* index errors
* conversion errors
* caching errors

All errors produce deterministic JSON with:
* error_type
* error_stage
* provider URLs
* resolver path
* timestamps

Verbose mode prints full diagnostics.

## 9. Deterministic Guarantees
`check_weather` guarantees:
*  deterministic provider selection
* deterministic fallback behavior
* deterministic normalization
* deterministic merge behavior
* deterministic index computation
* deterministic unit conversion
* stable schema
* reproducible output
* logged fallback behavior

These guarantees ensure predictable monitoring behavior across all supported platforms.

End of Usage.md