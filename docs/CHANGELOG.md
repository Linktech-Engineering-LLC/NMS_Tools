# Changelog — NMS_Tools

All notable changes to this project will be documented in this file.

The format follows semantic versioning:

- **MAJOR** — breaking changes  
- **MINOR** — new features, backward‑compatible  
- **PATCH** — bug fixes  

---

## [Unreleased]

- Planned enhancements for `check_cert.py` (see `docs/roadmap.md`)
- Documentation improvements
- Verbose output polishers
- Help text refinements

- Planned enhancements for `check_weather.py` v2.1.0 (see `docs/roadmap.md`)
  - NOAA/NWS as a second weather provider
  - Provider registry pattern with `--provider` override
  - `--debug-cache` flag
  - `--debug-location` flag
  - Strict schema validator
  - `--ttl` override
  - `--ignore-ttl` flag
  - `--ignore-cache` flag
  - `--cache-info` flag
  - Full documentation update for v2.1.0

---

## [3.0.0] — Initial Stable Release

### Added
- Deterministic JSON output mode  
- Verbose human‑readable mode  
- Nagios‑compatible output mode  
- TLS version and cipher extraction  
- SAN, issuer, signature algorithm, and key metadata  
- AIA chain reconstruction  
- OCSP reachability detection  
- Expiration thresholds  
- Python‑3.6 compatibility  
- Stable CLI contract  
- Installation, Operation, and Usage documentation  

## check_weather.py [2.0.0] - 2026-04-10
### Added
- Offline cache handling:
  - Support for `--force_cache` to read cached weather data without API access
  - Python 3.6–compatible timestamp parsing using `strptime`
  - Deterministic cache age calculation and reporting across all output modes
- Additional weather parameters exposed in verbose, JSON, and Nagios output:
  - Apparent temperature (°C/°F)
  - Dew point (°C/°F)
  - Visibility (km/mi)
  - Pressure (msl / inHg)
  - Precipitation probability
  - Condition text mapping
- Logging support:
  - Append-only log output to `check_weather.log` in a user-specified directory via `--log-dir`
  - Start banners and structured log entries
  - Warning surface in verbose and JSON modes when log directory is inaccessible

### Improved
- Unified cache source reporting (`forced cache`, `cache`, `api`) across verbose, JSON, and Nagios modes
- Ensured JSON output includes `cache_age`, `cache_written`, and `source` fields consistently

## check_weather.py [2.2.0] - 2026-04-27
### Added
- Rolling 24‑hour hourly forecast. Hourly mode now begins at the next hour ≥ local time instead of midnight.
- Weekly day‑slicing. Weekly mode now always starts at the current local date and returns exactly 7 days.
- Backend enrichment now includes:
  - Normalized condition text (`context`)
  - Deterministic icon filenames (`icon`)
  - Max wind fields for weekly forecasts (`wind_mph_max`, `wind_kph_max`)
- Updated verbose mode to use enriched backend fields for all modes.

### Improved
- Moved slicing logic into the fetch layer to ensure deterministic alignment before flattening.
- Simplified `convert_units_mode_aware()` to operate only on enriched, sliced structures.

### Upcoming Enhancements
- Verbose mode will display icon filenames next to condition text.
- New `--debug` flag will expose backend decision details (slice indices, sunrise/sunset logic, WMO mappings).
- New `--self-test` mode will validate slicing, enrichment, and mapping without hitting the API.
- Minutely precipitation support (`--minutely`) for short‑term rain alerts.
- Alerts mode (`--alerts`) using Open‑Meteo NWS alert feed for US locations.


### Notes
- This release prepares the tool for upcoming provider and cache enhancements planned for v2.1.0.
- The `--force_cache` flag allows users to test cache handling and output formatting without needing API access, making it easier to verify caching behavior and debug issues related to cached data.
