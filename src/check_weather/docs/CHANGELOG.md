# check_weather — CHANGELOG

All notable changes to the `check_weather` tool are documented here.  
This changelog follows a simple date‑based format.

---

## [2026‑05‑05] Classification Engine Rewrite

### Added
- Attribution for Weather Icons (MIT license) in README, docs, and export directory.
- New hybrid classification engine (`analyzer.py`) combining:
  - filename‑based semantic extraction
  - geometry‑based base‑shape detection (sun, moon, cloud)
- Night‑sun suppression logic to prevent false positives in moon icons.
- Stats summary block in `export_icons.py` including:
  - total icons processed
  - group counts
  - coverage percentages
  - groups‑per‑icon histogram
  - day/night breakdown
- New documentation: `docs/Classification.md` describing the full pipeline.

### Changed
- `export_icons.py` now uses only the new analyzer for classification.
- Recoloring pipeline updated to operate on merged classification groups.
- Log output improved with structured summary, timestamps, and end‑of‑run metadata.
- Updated README.md to reflect the new classification architecture.

### Removed
- Deprecated `classifier.py` (legacy filename‑only classifier).
- All fallback logic referencing the old classifier.
- Old message types (`classifier_only`, `merged`, `fallback`) removed from logs.

---

## [2026‑04‑27] v2.2.0 Enhancements

### Added
- Rolling 24‑hour hourly slicing.
- Weekly forecast normalization (always starts from current local date).
- Backend enrichment fields for weather CGI output.
- Updated JSON and verbose examples in README.
- Initial versioned CHANGELOG entry for check_weather.

---

## [2026‑04‑11] Documentation Overhaul

### Added
- Updated README.md to reflect actual behavior of `check_weather.py`.
- Added missing documentation for flags, logging, provider metadata, and threshold logic.

---

## [2026‑04‑07] Initial Weather Demo Integration

### Added
- Weather demo UI integration.
- Two‑way linking between check_weather docs and the Weather Demo page.
- Initial recolor engine integration.

---

