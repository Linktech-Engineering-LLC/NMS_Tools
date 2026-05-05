# Architecture Overview  
**check_weather — Updated 2026‑05**

This document describes the internal architecture of the `check_weather` tool, including module responsibilities, data flow, invariants, and integration points with the recolor engine and web demo.

The goal of this architecture is to provide a **deterministic, auditable, backend‑agnostic** weather processing pipeline that produces stable output for both CLI and CGI consumers.

---

## 1. High‑Level Pipeline

The `check_weather` pipeline consists of the following stages:

provider query
→ normalization
→ forecast slicing
→ icon classification
→ recoloring
→ output (JSON / CGI)


Each stage is deterministic and produces structured metadata that flows into the next stage.

---

## 2. Module Responsibilities

### `check_weather.py`
The main entry point.  
Responsible for:

- argument parsing  
- provider selection  
- logging  
- orchestrating the full pipeline  
- writing output (stdout, JSON, CGI)  
- enforcing invariants  

### `providers/*.py`
Each provider module implements:

- raw API fetch  
- provider‑specific parsing  
- mapping to the unified schema  
- error handling and fallback behavior  

Providers must return a normalized structure defined in `Metadata_Schema.md`.

### `slicing.py`
Responsible for:

- hourly slicing  
- rolling 24‑hour windows  
- weekly forecast normalization  
- ensuring forecasts always start from the current local date  

### `analyzer.py`
The classification engine.  
Implements:

- filename‑based semantic extraction  
- geometry‑based base‑shape detection  
- night‑sun suppression  
- merged classification rules  
- group assignment for recoloring  

This module replaces the legacy `classifier.py`.

### `recolor.py`
The recoloring engine.  
Responsible for:

- assigning palettes to groups  
- rewriting SVG `<path>` elements  
- producing recolored icons for the web demo  

### `export_icons.py`
The icon export tool.  
Implements:

- SVG loading  
- classification via `analyzer.py`  
- recoloring via `recolor.py`  
- writing recolored icons  
- stats summary (audit surface)  

### `cgi/` (if present)
Implements the CGI endpoint used by the web demo.

---

## 3. Data Flow

### 3.1 Provider → Normalization
Each provider returns raw data.  
Normalization converts it into a unified structure:

location
current conditions
hourly forecast
daily forecast
metadata


### 3.2 Normalization → Slicing
Slicing produces:

- a rolling 24‑hour hourly window  
- a normalized 7‑day forecast  
- enriched metadata  

### 3.3 Slicing → Classification
Each forecast entry includes a Weather Icons filename.  
Classification produces:

groups = ['sun', 'rain', ...]


### 3.4 Classification → Recoloring
Recoloring uses the final groups to assign colors to SVG paths.

### 3.5 Recoloring → Output
The final output includes:

- JSON for CLI/CGI  
- recolored icons for the web demo  
- logs and stats for auditability  

---

## 4. Classification Architecture

Classification is hybrid:

### 4.1 Filename‑Based Rules
Extracts:

- day/night  
- cloud  
- rain  
- snow  
- thunder  
- fog  
- wind  

### 4.2 Geometry‑Based Rules
Detects only:

- sun  
- moon  
- cloud  

Curves are approximated as line segments for robust detection.

### 4.3 Merging Logic
Final groups are:

filename_groups ∪ geometry_base_shape


Night icons suppress sun geometry.

### 4.4 Determinism
Classification is:

- stable  
- reproducible  
- backend‑agnostic  
- independent of provider quirks  

---

## 5. Recoloring Architecture

Recoloring is driven entirely by classification.

### 5.1 Group → Palette Mapping
Each group maps to a color palette defined in `recolor.py`.

### 5.2 Path Assignment
All `<path>` elements are assigned to one or more groups.

### 5.3 SVG Rewrite
The recolor engine rewrites:

- fill  
- stroke  
- opacity  

while preserving geometry.

---

## 6. Logging & Audit Surface

`export_icons.py` produces a structured summary:

- total icons  
- group counts  
- coverage percentages  
- groups‑per‑icon histogram  
- day/night breakdown  
- run metadata (duration, dry_run, status)  

This acts as a regression surface to detect drift.

---

## 7. Invariants & Guarantees

The system guarantees:

- deterministic output  
- stable classification  
- consistent recoloring  
- no sun in night icons  
- no geometry‑only precipitation detection  
- normalized forecast windows  
- schema‑compliant output  

Violations are logged and treated as errors.

---

## 8. Extension Points

The architecture supports:

- adding new providers  
- adding new palettes  
- adding new icon groups  
- extending geometry detection  
- adding new output formats  
- integrating additional web UI features  

All without breaking existing behavior.

---

## 9. Future Enhancements

Potential improvements:

- color usage statistics  
- drift detection alerts  
- per‑icon debug overlays  
- JSON/CSV export of stats  
- automated test harness for classification  

---

**End of Architecture.md**
