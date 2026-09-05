# Icon Classification Pipeline  

**Part of:** NMS_Tools Monitoring Suite  
**Document:** Icon Classification Pipeline
**Version:** 3.0.0 
**Author:** Leon McClatchey, Linktech Engineering LLC  
**License:** MIT  
**Requires:** Python 3.12+  (development only; not required for frozen binary)
**Last Updated:** 2026-08-16

This document describes how Weather Icons SVGs are classified and recolored by the `check_weather` toolchain.  
The classification system uses a **hybrid approach** that merges filename semantics with geometry analysis to produce stable, deterministic groups for recoloring.

---

## 1. Overview

Each icon is assigned one or more **semantic groups**:

sun, moon, cloud, rain, snow, thunder, fog, wind


These groups drive the recoloring engine and determine which palette is applied to each SVG path.

The classification pipeline consists of:

1. **Filename‑based classification**  
2. **Geometry‑based base‑shape detection**  
3. **Merged classification**  
4. **Recoloring**  
5. **Stats summary (audit surface)**

---

## 2. Filename‑Based Classification (Primary Source)

Weather Icons encode most semantics directly in the filename.  
The exporter extracts groups based on substring rules:

| Filename Contains | Group Added |
|------------------|-------------|
| `day`            | `sun`       |
| `night`          | `moon`      |
| `cloud`          | `cloud`     |
| `rain`, `showers`, `sprinkle`, `mix` | `rain` |
| `snow`, `sleet`, `hail` | `snow` |
| `storm`, `thunder`, `lightning` | `thunder` |
| `fog`, `haze`    | `fog`       |
| `wind`           | `wind`      |

Filename classification is authoritative for precipitation and special effects.

---

## 3. Geometry‑Based Classification (Base Shapes Only)

SVG paths are parsed and curves are approximated as line segments.  
Geometry is used **only** to detect the three base shapes:

- **sun**  
- **moon**  
- **cloud**

These shapes are identifiable by their outline geometry.  
All precipitation shapes (rain, snow, thunder, fog, wind) are merged into the cloud path and **cannot** be detected geometrically.

### Night‑Sun Suppression  
If the filename indicates a night icon, any geometric `sun` detection is suppressed and replaced with `moon`.

---

## 4. Merged Classification

The final groups for each icon are:

final_groups = filename_groups ∪ geometry_base_shape


Examples:

wi-day-rain.svg           → ['sun', 'rain']
wi-night-alt-snow.svg     → ['moon', 'snow']
wi-cloudy.svg             → ['cloud']
wi-night-fog.svg          → ['moon', 'fog']


The merged result is stable and deterministic across all 32 icons.

---

## 5. Recoloring

Recoloring is performed by `recolor.py`.

- All `<path>` elements in the SVG are assigned to one or more groups.
- Each group maps to a color palette.
- The recolored SVG is written back to disk.

Recoloring is **entirely driven** by the final merged classification.

---

## 6. Stats Summary (Audit Surface)

After processing all icons, the exporter prints and logs a summary block:

### 6.1 Group Counts
Shows how many icons include each group.

sun     : 15
moon    : 16
cloud   : 4
rain    : 12
snow    : 10
thunder : 6
fog     : 2
wind    : 4


### 6.2 Coverage Percentages
Normalizes counts relative to total icons.

sun     : 15  (46.9%)
moon    : 16  (50.0%)
...

### 6.3 Groups‑Per‑Icon Histogram
Useful for detecting over‑ or under‑classification.

1 groups: 3
2 groups: 21
3 groups: 8


### 6.4 Day/Night Breakdown
Validates filename rules.

day     : 15
night   : 16
unknown : 1


This summary acts as a **regression surface**.  
Any unexpected change in counts indicates a classification drift or filename rule mismatch.

---

## 7. Removed Components

The legacy `classifier.py` (filename‑only classifier) has been removed.  
All classification is now handled by `analyzer.py`.

---

## 8. Pipeline Overview

copy → analyze_svg → recolor → write → stats summary


This is the complete export pipeline used by `export_icons.py`.

---

## 9. Future Enhancements (Optional)

- Color usage statistics  
- Expected vs actual mismatch detection  
- Per‑icon detailed summaries  
- JSON/CSV export of stats  
- Drift detection alerts  

These can be added without modifying the core classifier.

---

## Icon Source Attribution
The base SVG icons are from the Weather Icons project by Erik Flowers  
(https://github.com/erikflowers/weather-icons), used under the MIT License.


**End of Classification.md**
