# Flags Reference — check_weather

**Part of:** NMS_Tools Monitoring Suite  
**Script:** export_icons.py  
**Version:** 3.0.0  
**Author:** Leon McClatchey, Linktech Engineering LLC  
**License:** MIT  
**Last Updated:** 2026‑08‑16

## Table of Contents
1. [Location & Units](#1-location--units)
2. [Output Modes](#2-output-modes)
    * [Default Nagios Mode](#default-mode--nagios-output)
    * [Verbose](#verbose)
    * [JSON](#json)
    * [Quiet](#quiet)
    * [Version](#version)
3. [Provider & Debug Options](#3-provider--debug-options)
4. [Inclusion Flags](#4-inclusion-flags)
5. [Cache Control](#5-cache-control)
6. [Thresholds](#6-thresholds)
7. [Logging](#7-logging)
8. [Miscellaneous](#8-miscellaneous)
9. [Notes](#9-notes)

## 1. Location & Units

```Code
-l, --location <zip|city|lat,lon>
```

Specifies the location to query. Accepts:
* ZIP code (`67576`)
* City name (`"Saint John, KS"`)
* Latitude/longitude (`38.03,-98.76`)

```Code
--country <code>
```

Country code for ZIP resolution (default: `US`).

```Code
-u, --units <imperial|metric>
```

Selects the output unit system.

## 2. Output Modes

### Default Mode — Nagios Output

Nagios mode is the implicit default when no other output mode is selected.
* Single‑line status message
* Includes perfdata
* No extra whitespace
* No multi‑line output
* Designed for Nagios, Icinga, Thruk, PNP4Nagios

There is no `--nagios` **switch** — Nagios mode is automatic.

### Verbose

```Code
-v, --verbose
```

Enables detailed operator‑grade output:
* Location resolution details (with `--show-location-details`)
* Cache source and age
* Expanded weather metrics
* Threshold evaluation
* Weather + location provider metadata
* Full weather API URL

### JSON

```Code
-j, --json
```

Outputs structured JSON suitable for automation:
* All weather metrics (both unit systems)
* source, cache_age, cache_written
* resolved_location block
* runtime_ms

### Quiet

```Code
-q, --quiet
```

Exit code only.
No output.

### Version

```Code
-V, --version
```

Shows script version and Python version.

## 3. Provider & Debug Options

```Code
--provider {open-meteo|nws}
```
Selects the weather provider.

Supported providers:
* **open‑meteo**
    * current
    * hourly
    * weekly
    * deterministic WMO weather codes
    * stable geometry‑based icon mapping

* **nws**
    * current
    * hourly
    * weekly
    * **alerts**
    * full NWS metadata chain
    * deterministic shortForecast + icon mapping

If omitted, the provider is selected automatically based on:
* location
* availability
* resolver metadata

```Code
--show-location-details
```

Displays a detailed block describing:
* Input location
* Location provider name + URL
* Weather provider name + base URL
* Resolved city/state/country
* Latitude/longitude
* Full weather API URL

```Code
--show-codes
```

Show numeric weather condition codes in verbose mode.

```Code
--no-color
```

Disable ANSI color output in verbose mode.

## 4. Inclusion Flags

Control which fields appear in verbose, JSON, and perfdata output.

```Code
--include-gusts
```

Include wind gusts even if no gust thresholds are set.

```Code
--include-precip
```

Include precipitation fields.

```Code
--include-clouds
```

Include cloud cover fields.

## 5. Cache Control

```Code
--force-cache
```

Force reading from cache even if the API is available.
Verbose mode reports: `Source: forced cache`.

```Code
--ignore-cache
```

Bypass the cache entirely and force a fresh API request.

```Code
--ignore-ttl
```

Use cached data even if expired.
Verbose mode reports: `Source: cache (TTL ignored)`.

```Code
--cache-info
```

Display cache metadata and exit:
* Cache path
* Timestamp
* Age
* TTL
* Size
* Last write status

```Code
--cache-path <path>
```

Override the default cache file location.

```Code
--cache-expire <seconds>
```

Override the default TTL for this invocation.

```Code
--cache-clear
```

Delete the cache file and exit.

## 6. Thresholds

```Code
--warning-temp <value>
--critical-temp <value>
```
Temperature thresholds (bi‑directional).

```Code
--warning-wind <value>
--critical-wind <value>
```
Wind speed thresholds.

```Code
--warning-gust <value>
--critical-gust <value>
```
Wind gust thresholds.

```Code
--warning-humidity <value>
--critical-humidity <value>
```
Humidity thresholds.

```Code
--warning-precip <value>
--critical-precip <value>
```
Precipitation thresholds.

```Code
--warning-cloud <value>
--critical-cloud <value>
```
Cloud cover thresholds.

Verbose mode includes threshold evaluation details when thresholds are set.

## 7. Logging

Logging is **disabled in Nagios mode**.
Nagios mode is the default output mode, and plugins must remain side‑effect‑free.

Logging activates only when using:
* `--verbose`
* `--json`
* `--quiet`

```Code
--log-dir <path>
```
Enable logging to the specified directory.

```Code
--log-max-mb <size>
```
Maximum log size before rotation (default: 50 MB).

Log entries include:

* `[START]` metadata banner
* `[LOCATION]` block
* `[WEATHER]` block
* `[THRESHOLDS]` block
* `[RESULT]` final state
* `[END]` termination marker

## 8. Miscellaneous

```Code
-h, --help
```
Display usage information.

## 9. Notes
* Nagios mode is the default and requires no switch.
* Cache age is calculated deterministically and shown in all modes that support it.
* All weather metrics (apparent temperature, dew point, visibility, pressure, etc.) are available in verbose and JSON modes.
* All cache flags behave consistently across verbose, JSON, and Nagios output.
* Provider architecture is fully documented in Provider_Architecture.md.