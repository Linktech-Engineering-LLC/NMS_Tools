# Usage for check_weather v3.0.0

Defines all CLI flags, output modes, and usage patterns for check_weather v3.0.0.

**Part of:** NMS_Tools Monitoring Suite  
**Document:** Usage Reference
**Version:** 3.0.0 
**Author:** Leon McClatchey, Linktech Engineering LLC  
**License:** MIT  
**Requires:** Python 3.12+  (development only; not required for frozen binary)
**Last Updated:** 2026-09-06

## Table of Contents
1. [Overview](#1-overview)
2. [Basic Invocation](#2-basic-invocation)
3. [Command‑Line Options](#3-commandline-options)
4. [Output Modes](#4-output-modes)
5. [Location Formats](#5-location-formats)
6. [Examples](#6-examples)
7. [Provider Selection](#7-provider-selection)
8. [Caching Behavior](#8-caching-behavior)
9. [Error Handling](#9-error-handling)
10. [Deterministic Guarantees](#10-deterministic-guarantees)
11. [See Also](#11-see-also)

---

## 1. Overview

`check_weather` v3.0.0 retrieves current, hourly, and weekly weather data using a deterministic multi‑provider engine built on `PythonTools.weather`. The v3 engine operates in a **hybrid provider model**, where both NWS and Open‑Meteo may be used depending on mode, field availability, and location type. Provider fallback and strict provider isolation are not yet implemented; these are planned for v3.1+.

The tool resolves locations, normalizes provider fields, merges hourly/daily data, applies unit conversion, evaluates thresholds, and outputs structured JSON suitable for CLI, CGI, dashboards, and automation.

---

## 2. Basic Invocation
```Bash
check_weather.py -l "<location>"
```

The `<location>` may be:
* `"Wichita, KS"`
* `"Berlin, DE"`
* `"67576"`
* `"38.0,-98.7"`

The resolver uses the `--country` value (default: US) when interpreting the location.

---

## 3. Command‑Line Options

### Required
```Code
-l, --location <value>
```

Primary location input.
Accepts raw or encrypted free‑form strings.
All location resolution begins from this value.

##### Deprecated Location Aliases
```Code
--zip <value>
--city <value>
--lat <value>
--lon <value>
```
These switches normalize into `--location` internally but were **never validated** in v3.0.0 and are now **deprecated**.
They may be removed in future versions.

`--city` accepts either `"City"` or `"City, State"`.

#### Country Selection
```Code
--country <code>
```

Specifies the country for location resolution.
Defaults to **US**.

Examples:
* `--country US`
* `--country DE`
* `--country CA`

This affects **location resolution only**.
It does **not** select weather providers.

### Mode Selection
```Code
--hourly      Output hourly forecast
--weekly      Output weekly forecast
--full        Output full merged structure (planned)
```

Behavior:
* If **no mode flag** is provided, the mode defaults to **current**.
* There is **no** `--current` flag.
* Nagios/Icinga mode only supports current.
* Using `--hourly`, `--weekly`, or `--full` without `--json` or `--verbose` raises an error.

### Output Format
```Code
--json -j        Structured JSON
--verbose -v     Multi-line diagnostic output
--quiet -q       Exit code only (no output)
```

Behavior:
* If none of `--json`, `--verbose`, or `--quiet` is provided, the tool defaults to Nagios/Icinga mode.
* There is no `--nagios` flag.
* Nagios mode is implicit.

### Provider Control (Optional)
```Code
--provider nws
--provider open-meteo
```

Behavior in v3.0.0:
* If no provider is specified, the engine defaults to NWS.
* The selected provider is recorded in metadata.
* **Provider isolation is not yet implemented.**
* The engine may still use both providers depending on field availability.
* No provider fallback exists; only cache fallback applies.

### Caching Options
```Code
--ignore-cache     Skip cache read; always attempt live fetch
--ignore-ttl       Use cached data regardless of age
--cache-info       Show cache metadata in output
--force-cache      Return cached data only; never call provider APIs
```

Caching is enabled by default.

---

## 4. Output Modes

### 4.1 Nagios/Icinga Mode (default)
Triggered when no output mode flag is provided.

Produces:
`OK - Temp 72°F, Wind 8 mph, Gust 12 mph | temp=72 wind=8 gust=12 precip=0 clouds=20`

Characteristics:
* single line
* status text at beginning
* perfdata always included
* thresholds applied
* exit codes follow Nagios/Icinga conventions
* only valid in current mode

### 4.2 JSON Mode

Produces structured JSON including:
* normalized fields
* merged hourly/daily data
* index computation
* provider metadata
* resolver metadata
* cache metadata
* runtime metadata

Recommended for dashboards, CGI, and automation.

### 4.3 Verbose Mode

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

### 4.4 Quiet Mode
```Bash
--quiet
```

Produces no output, only an exit code.

Useful for:
* shell scripting
* automation
* conditional logic
* silent monitoring checks

---

## 5. Location Formats

### ZIP Code
```Bash
check_weather.py -l 67576
```

Uses Zippopotam.us → NWS/Open‑Meteo hybrid.
(`--zip` is deprecated.)

### City + Region
```Bash
check_weather.py -l "Wichita, KS"
```

Uses Open‑Meteo Geocoding → NWS/Open‑Meteo hybrid.
(`--city` is deprecated.)

### Latitude/Longitude
```Bash
check_weather.py -l "38.0,-98.7"
```

Uses coordinates directly.
(`--lat` / `--lon` are deprecated.)

### International City
```Bash
check_weather.py -l "Berlin" --country DE
```

Uses Open‑Meteo Geocoding → Open‑Meteo weather.
NWS is US‑only and cannot serve international locations.

---

## 6. Examples

### Default (Nagios/Icinga)
```Bash
check_weather -l "Wichita, KS"
```

### JSON Output
```Bash
check_weather -l "Berlin" --country DE --json
```

### Verbose Diagnostic Output
```Bash
check_weather -l "Wichita, KS" --hourly --verbose
```

### Quiet Mode
```Bash
check_weather -l "Wichita, KS" --quiet
```

### Weekly Forecast
```Bash
check_weather -l "Wichita, KS" --weekly
```

### Force Open‑Meteo
```Bash
check_weather -l "Berlin" --country DE --provider open-meteo
```

---

## 7. Provider Selection

The v3.0.0 engine uses a **hybrid provider model**:
* Provider selection is explicit via `--provider`.
* Provider isolation is not yet implemented.
* No provider fallback exists.
* Only cache fallback applies.

Provider metadata includes:
* provider_selected
* provider_urls
* provider_metadata

Removed fields (v2.x only):
* provider_fallback
* provider_reason

---

## 8. Caching Behavior

Caching stores:
* current
* hourly
* weekly
* raw provider data
* metadata
* timestamps

Cache is used when:
* provider APIs fail
* `--force-cache` is set
* `--ignore-ttl` is set
* `--cache-info` is requested

Cache TTL:
* weather: 15 minutes
* location: 24 hours

---

## 9. Error Handling

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

---

## 10. Deterministic Guarantees

check_weather guarantees:
* deterministic normalization
* deterministic merge behavior
* deterministic index computation
* deterministic unit conversion
* deterministic cache behavior
* deterministic URL construction
* stable schema
* reproducible output
* no provider fallback
* no silent provider switching

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
* [Provider_Architecture](Provider_Architecture.md)
                                                                                                       