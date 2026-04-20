# check_weather.py — Flags Reference

This document provides a complete reference for all command‑line flags supported by check_weather.py.
Flags are grouped by purpose for clarity and operator‑grade usability.

## Location & Units

```-l, --location <zip|city|lat,lon>```

Specifies the location to query. Accepts:

- ZIP code (67576)
- City name ("Saint John, KS")
- Latitude/longitude (38.03,-98.76)

```--country <code>```

Country code for ZIP resolution (default: US).

```-u, --units <imperial|metric>```

Selects the output unit system.

## Output Modes

### Default Mode — Nagios Output

Nagios mode is the implicit default when no other output mode is selected.

- Produces a single‑line status message
- Includes perfdata
- No extra whitespace or multi‑line output
- Designed for Nagios, Icinga, Thruk, and PNP4Nagios

There is no --nagios switch.
This is intentional to keep Nagios usage zero‑configuration.

```-v, --verbose```

Enables detailed operator‑grade output including:

- Location resolution details (when combined with --show-location-details)
- Cache source and age
- Expanded weather metrics
- Threshold evaluation
- Weather provider + location provider
- Full weather API URL

```-j, --json```

Outputs structured JSON suitable for automation, dashboards, or logging.

Includes:

- All weather metrics in both unit systems
- source, cache_age, cache_written
- resolved_location block
- runtime_ms

```-q, --quiet```

Exit code only. No output.


```-V, --version```

Shows script version and Python version.

## Provider & Debug Options

```--provider {open-meteo}```

Validated weather provider selection.
Currently only open-meteo is supported.

This flag is logged for operator visibility but does not change execution behavior.

```--show-location-details```

Displays a detailed block describing:

- Input location
- Location provider name
- Location provider URL
- Weather provider name
- Weather provider base URL
- Resolved city/state/country
- Latitude/longitude
- Full weather API URL

```--show-codes```

Show numeric weather condition codes in verbose mode.

```--no-color```

Disable ANSI color output in verbose mode.

## Inclusion Flags

These flags control which fields appear in verbose, JSON, and perfdata output.

```--include-gusts```

Include wind gusts even if no gust thresholds are set.

```--include-precip```

Include precipitation fields.

```--include-clouds```

Include cloud cover fields.

## Cache Control

```--force-cache```

Force reading from cache even if the API is available.

Verbose mode reports: ```Source: forced cache```.

```--ignore-cache```

Bypass the cache entirely and force a fresh API request.

```--ignore-ttl```

Use cached data even if expired.

Verbose mode reports: ```Source: cache (TTL ignored)```.

```--cache-info```

Display cache metadata and exit.

Shows:

-Cache path
- Timestamp
- Age
- TTL
- Size
- Last write status

```--cache-path <path>```

Override the default cache file location.

```--cache-expire <seconds>```

Override the default TTL for this invocation.

```--cache-clear```

Delete the cache file and exit.

## Thresholds

```--warning-temp <value>```
```--critical-temp <value>```
Temperature thresholds.

```--warning-wind <value>```
```--critical-wind <value>```
Wind speed thresholds.

```--warning-gust <value>```
```--critical-gust <value>```
Wind gust thresholds.

```--warning-humidity <value>```
```--critical-humidity <value>```
Humidity thresholds.

```--warning-precip <value>```
```--critical-precip <value>```
Precipitation thresholds.

```--warning-cloud <value>```
```--critical-cloud <value>```
Cloud cover thresholds.

Verbose mode includes threshold evaluation details when thresholds are set.

## Logging

**Logging is disabled in Nagios mode.**
Nagios mode is the default output mode, and plugins must remain side‑effect‑free.
Logging only activates when using --verbose, --json, or --quiet.


```--log-dir <path>```

Enable logging to the specified directory.

```--log-max-mb <size>```

Maximum log size before rotation (default: 50 MB).

Log entries include:

- [START] metadata banner
- [WEATHER] blocks
- [RESULT] final state
- [END] termination marker

## Miscellaneous
```-h, --help```

Display usage information.

## Notes

- Nagios mode is the default and requires no switch.
- Cache age is calculated deterministically and shown in all modes that support it.
- All weather metrics (apparent temperature, dew point, visibility, pressure, etc.) are available in verbose and JSON modes.
- All cache flags behave consistently across verbose, JSON, and Nagios output.
- Provider architecture is fully documented in the README.
