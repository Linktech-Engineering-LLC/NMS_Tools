# check_weather.py — Flags Reference

This document provides a complete reference for all command‑line flags supported by `check_weather.py`.  
Flags are grouped by purpose for clarity and operator‑grade usability.

---

## Location & Units

### `-l, --location <zip|city>`
Specifies the location to query. Accepts ZIP codes or city names.

### `-u, --units <imperial|metric>`
Selects the output unit system.

---

## Output Modes

### `-v, --verbose`
Enables detailed output including:
- cache source and age  
- expanded weather metrics  
- API vs cache decision path  
- threshold evaluation details when thresholds are set  

Verbose mode is intended for diagnostics, operator workflows, and development.

### `-j, --json`
Outputs structured JSON suitable for automation, dashboards, or logging.  
Includes:
- `source`  
- `cache_age`  
- `cache_written`  
- all weather metrics in both unit systems  

### `-n, --nagios`
Outputs a single‑line Nagios‑compatible status message with perfdata.  
No extra whitespace or multi‑line output is permitted.

---

## Cache Control

### `--force_cache`
Forces the tool to read from the local cache without contacting the API.  
Useful for:
- testing cache behavior  
- verifying output formatting  
- debugging cached data  
- offline operation  

Verbose mode reports: `Source: forced cache`.

### `--ignore-ttl` *(planned)*
Uses cached data even if expired.  
Verbose mode will report: `Source: cache (TTL ignored)`.

### `--ignore-cache` *(planned)*
Bypasses the cache entirely and forces a fresh API request.

### `--cache-info` *(planned)*
Displays diagnostic information about the cache file:
- path  
- timestamp  
- age  
- TTL  
- size  
- last write status  

No weather output is produced when this flag is used.

### `--cache-path <path>` *(planned)*
Overrides the default cache file location.  
The directory must exist or the tool will fail cleanly.

### `--cache-expire <seconds>` *(planned)*
Overrides the default TTL for this invocation.

### `--cache-clear` *(planned)*
Deletes the cache file and reports the action in verbose mode.  
Does not fetch weather unless combined with a normal run.

---

## Thresholds

### `--warn <expr>` *(future expansion)*
Defines warning thresholds for Nagios mode.

### `--crit <expr>` *(future expansion)*
Defines critical thresholds for Nagios mode.

Verbose mode includes threshold evaluation details when thresholds are set.

---

## Miscellaneous

### `-h, --help`
Displays usage information.

---

## Notes

- Timestamp parsing uses `datetime.strptime` for full Python 3.6 compatibility.
- Cache age is calculated deterministically and shown in all modes that support it.
- Additional weather metrics (apparent temperature, dew point, visibility, pressure, etc.) are available in verbose and JSON modes.
- All cache flags are designed to behave consistently across verbose, JSON, and Nagios output.
