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

## [2.1.0] - 2026-04-10
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

### Improved
- Unified cache source reporting (`forced cache`, `cache`, `api`) across verbose, JSON, and Nagios modes
- Ensured JSON output includes `cache_age`, `cache_written`, and `source` fields consistently

### Notes
- This release prepares the tool for upcoming cache‑control flags (`--ignore-ttl`, `--ignore-cache`, `--cache-info`, etc.) tracked in the NMS_Tools checklist.
- The `--force_cache` flag allows users to test cache handling and output formatting without needing API access, making it easier to verify caching behavior and debug issues related to cached data.