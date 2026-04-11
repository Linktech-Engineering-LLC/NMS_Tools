# check_weather.py — Logging Reference

This document describes the logging behavior of check_weather.py, including log structure, rotation, metadata, and operator‑grade guarantees.

Logging is optional and is enabled only when --log-dir is provided.

## Enabling Logging

```bash
./check_weather.py --location 67576 --log-dir /path/to/logs
```

When enabled:

- A log file is created inside the specified directory.
- If the directory **does not exist**, the tool **attempts to create it automatically**.
- Directory creation uses deterministic, operator‑grade behavior:
 - parent directories are created as needed
 - no partial writes
 - failures are cleanly reported

If directory creation fails (permissions, invalid path, read‑only filesystem), the tool:

- Prints a clear error message
- exits with UNKNOWN
- does not produce malformed Nagios output

This ensures logging is safe to enable even on first‑run deployments.

## Log Rotation

Rotation is controlled by:

```--log-max-mb <size>```

Default: 50 MB

When the log file exceeds the configured size:

- The current file is renamed with a .1 suffix
- A new log file is created
- Only one rotation level is maintained (no cascading archives)

Rotation is deterministic and safe for Nagios/Icinga environments.

## Log Structure

Each invocation produces a structured, multi‑section log entry.

### Example Layout

```bash
[START] 2026-04-11T11:45:22Z
  version: 1.4.0
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

Sections
[START]

Contains metadata about the invocation:

- Timestamp
- Script version
- Python version
- Raw arguments
- Weather provider
- Logging directory

[LOCATION]

Includes all resolved location metadata:

- Input
- Location provider name
- Location provider URL
- Resolved city/state/country
- Latitude/longitude

Matches the resolved_location JSON block.

[WEATHER]

Contains the weather metrics used for evaluation:

- Source (Live API, Cache, Forced Cache, Cache (TTL ignored))
- Cache age
- All weather metrics in the selected unit system
- Condition code + text
- Weather API URL

[THRESHOLDS]

Only appears when thresholds are provided.

Includes:

- All thresholds passed on the command line
- Evaluation result (OK, WARNING, CRITICAL)

[RESULT]

Final Nagios‑style result:

- Status
- Message
- Runtime in milliseconds

[END]

Marks the end of the log entry.

## Logging Guarantees

Logging is designed to be:

### Deterministic

- Same inputs → same log structure
- No random fields
- No nondeterministic ordering

### Operator‑Grade

- No multi‑line noise
- No stack traces unless a fatal error occurs
- No partial writes

### Safe for Monitoring Systems

- Logging never interferes with Nagios output
- Logging failures never break monitoring
- Log rotation is atomic

### Consistent Across Modes

Logging works identically in:

- Verbose mode
- JSON mode
- Quiet mode

### When Logging Is Useful

Logging is recommended for:

- Debugging location resolution
- Verifying threshold evaluation
- Tracking cache behavior
- Auditing API usage
- Long‑term monitoring diagnostics

### When Logging Is Not Recommended

Avoid logging when:

- Running inside ephemeral containers
- Running in read‑only environments
- Running on systems with strict I/O limits

## Logging Behavior in Nagios Mode

Logging is automatically disabled when the tool is running in Nagios mode, which is the default output mode when no other mode flags (--verbose, --json, --quiet) are provided.

This behavior is intentional and guarantees:

- **Side‑effect‑free execution**
  Nagios plugins must not write files during normal operation.
- **Deterministic performance**
  No file I/O, no latency variance, no permission failures.
- **Clean monitoring output**
  No risk of stderr noise or partial writes interfering with Nagios.


### When Logging Is Disabled

Logging is disabled when:

- No output mode flags are provided
- The tool is producing a single‑line Nagios status message
- The tool is invoked by Nagios/Icinga/Thruk
- Even if --log-dir is supplied, logging will not activate in Nagios mode.

###When Logging Is Enabled

Logging is enabled only when:

- ```--verbose``` is used
- ```--json``` is used
- ```--quiet``` is used

Any mode other than default Nagios mode is active

This ensures logging is available for diagnostics, development, and operator workflows — but never during monitoring execution.