# Logging Reference -- check_weather

**Part of:** NMS_Tools Monitoring Suite  
**Document:** Logging Reference
**Version:** 3.0.0 
**Author:** Leon McClatchey, Linktech Engineering LLC  
**License:** MIT  
**Requires:** Python 3.12+  (development only; not required for frozen binary)
**Last Updated:** 2026-08-16

## Table of Contents
1. [Enabling Logging](#1-enabling-logging)
2. [Log Rotation](#2-log-rotation)
3. [Log Structure](#3-log-structure)
    1. [START](#31-start)
    2. [LOCATION](#32-location)
    3. [WEATHER](33-#weather)
    4. [THRESHOLDS](#34-thresholds)
    5. [RESULT](#35-result)
    6. [END](#36-end)
4. [Logging Guarantees](#4-logging-guarantees)
5. [When Logging Is Useful](#5-when-logging-is-useful)
6. [When Logging Is Not Recommended](#6-when-logging-is-not-recommended)
7. [Logging Behavior in Nagios Mode](#7-logging-behavior-in-nagios-mode)
    1. [When Logging Is Disabled](#71-when-logging-is-disabled)
    2. [When Logging Is Enabled](#72-when-logging-is-enabled)
8. [See Also](#8-see-also)

## 1. Enabling Logging

Logging is optional and enabled only when --log-dir is provided.

```bash
check_weather --location 67576 --log-dir /path/to/logs
```

When enabled:
* A log file is created inside the specified directory.
* If the directory **does not exist**, the tool **creates it automatically**.
* Parent directories are created as needed.
* No partial writes occur.
* Failures (permissions, invalid path, read‑only filesystem) produce:
  * a clear error message
  * an UNKNOWN exit state
  * no malformed Nagios output

This ensures logging is safe even on first‑run deployments.

## 2. Log Rotation

Rotation is controlled by:

```Code
--log-max-mb <size>
```

Default: **50 MB**

When the log file exceeds the configured size:
* The current file is renamed with a .1 suffix
* A new log file is created
* Only one rotation level is maintained (no cascading archives)

Rotation is deterministic and safe for Nagios/Icinga environments.

## 3. Log Structure

Each invocation produces a structured, multi‑section log entry.

**Example Layout**

```Code
[START] 2026-04-11T11:45:22Z
  version: 3.0.0
  python: 3.12.2
  args: --location 67576 --units imperial --show-location-details
  provider: open-meteo
  log_dir: /var/log/check_weather

[LOCATION]
  input: 67576
  location_provider: zippopotam.us
  location_provider_url: https://api.zippopotam.us/US/67576
  resolved_city: Saint John
  resolved_state: Kansas
  resolved_country: US
  latitude: 38.0309
  longitude: -98.7647

[WEATHER]
  source: Live API
  cache_age: 0s
  temperature_f: 56.66
  wind_mph: 20.26
  humidity: 31
  cloudcover: 54
  condition_text: Partly cloudy
  weather_url: https://api.open-meteo.com/v1/forecast?latitude=...

[THRESHOLDS]
  wind_warning: 25
  wind_critical: 35
  gust_warning: 40
  gust_critical: 50
  evaluation: OK

[RESULT]
  status: OK
  message: Weather normal: 56.66°F, 20.26 mph
  runtime_ms: 763.0

[END]
```

### 3.1 START

Contains metadata about the invocation:
* Timestamp
* Script version
* Python version
* Raw arguments
* Weather provider
* Logging directory

### 3.2 LOCATION

Includes all resolved location metadata:
* Input
* Location provider name
* Location provider URL
* Resolved city/state/country
* Latitude/longitude

Matches the `resolved_location` JSON block.

### 3.3 WEATHER

Contains the weather metrics used for evaluation:
* Source (`Live API`, `Cache`, `Forced Cache`, `Cache (TTL ignored)`)
* Cache age
* All weather metrics in the selected unit system
* Condition code + text
* Weather API URL

### 3.4 THRESHOLDS

Appears only when thresholds are provided.

Includes:
* All thresholds passed on the command line
* Evaluation result (OK, WARNING, CRITICAL)

### 3.5 RESULT

Final Nagios‑style result:
* Status
* Message
* Runtime in milliseconds

### 3.6 END

Marks the end of the log entry.

## 4. Logging Guarantees

Logging is designed to be:

### Deterministic
* Same inputs → same log structure
* No random fields
* No nondeterministic ordering

### Operator‑Grade
* No multi‑line noise
* No stack traces unless a fatal error occurs
* No partial writes

### Safe for Monitoring Systems
* Logging never interferes with Nagios output
* Logging failures never break monitoring
* Log rotation is atomic

### Consistent Across Modes

Logging works identically in:
* Verbose mode
* JSON mode
* Quiet mode

## 5. When Logging Is Useful

Logging is recommended for:
* Debugging location resolution
* Verifying threshold evaluation
* Tracking cache behavior
* Auditing API usage
* Long‑term monitoring diagnostics

## 6. When Logging Is Not Recommended

Avoid logging when:
* Running inside ephemeral containers
* Running in read‑only environments
* Running on systems with strict I/O limits

## 7. Logging Behavior in Nagios Mode

Logging is automatically disabled when the tool is running in Nagios mode (default mode when no `--verbose`, `--json`, or `--quiet` flags are provided).

This guarantees:
* **Side‑effect‑free execution**
* **Deterministic performance**
* **Clean monitoring output**

### 7.1 When Logging Is Disabled

Logging is disabled when:
* No output mode flags are provided
* The tool is producing a single‑line Nagios status message
* The tool is invoked by Nagios/Icinga/Thruk
* Even if --log-dir is supplied, logging will not activate in Nagios mode

### 7.2 When Logging Is Enabled

Logging is enabled only when:
* --verbose is used
* --json is used
* --quiet is used

Any mode other than default Nagios mode activates logging.

This ensures logging is available for diagnostics and operator workflows — but never during monitoring execution.

## 8. See Also
* [CHANGELOG](CHANGELOG.md)
* [Architecture](Architecture.md)
* [FLAGS.md](../../../docs/FLAGS.md)
* [Metadata_schema.md](Metadata_schema.md)
* [Enforcement](Enforcement.md)
* [Installation](Installation.md)
* [Operation](Operation.md)
* [Provider_Architecture](Provider_Architecture.md)
* [Usage](Usage.md)
