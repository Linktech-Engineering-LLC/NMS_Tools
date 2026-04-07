# Enforcement Model

`check_weather.py` follows the unified NMS_Tools enforcement model used across all monitoring plugins.  
The tool produces deterministic, single‑line Nagios/Icinga output in default mode and supports verbose and JSON modes for diagnostics and ingestion.

This document defines the enforcement rules, output guarantees, severity model, and behavior under monitoring and policy enforcement.

---

## 1. Enforcement Overview

`check_weather.py` implements two enforcement layers:

1. **Monitoring Enforcement (always enabled)**  
   - Retrieves weather data  
   - Normalizes values  
   - Evaluates thresholds  
   - Produces Nagios/Icinga output  

2. **Policy Enforcement (threshold‑based, optional)**  
   - Activated only when the user provides threshold flags  
   - Determines WARNING/CRITICAL states  
   - Ensures deterministic severity selection  

If no thresholds are provided, the plugin always returns **OK** unless a resolver or provider error occurs.

---

## 2. Output Rules

### 2.1 Default Mode (Nagios/Icinga)

Default mode must produce:

- **Exactly one line** of output  
- **No leading or trailing whitespace**  
- **No resolver or provider details**  
- **Status text at the beginning of the line**  
- **Perfdata appended after a pipe (`|`)**  
- **No additional lines, warnings, or debug text**

Example:

OK - Temp 72°F, Wind 8 mph, Gust 12 mph | temp=72 wind=8 gust=12 precip=0 clouds=20

Code

This output is safe for:

- Nagios Core  
- Icinga 2  
- NRPE  
- Any monitoring engine that expects single‑line plugin output  

---

## 3. Severity Model

Severity is determined by threshold evaluation.

### 3.1 Severity Levels

| Level | Meaning |
|-------|---------|
| **CRITICAL** | One or more critical thresholds exceeded |
| **WARNING** | One or more warning thresholds exceeded |
| **OK** | No thresholds exceeded |
| **UNKNOWN** | Resolver or provider failure |

### 3.2 Precedence

Severity precedence is deterministic:

1. **CRITICAL**  
2. **WARNING**  
3. **OK**  
4. **UNKNOWN** (only for errors)

If multiple thresholds are exceeded, the highest‑severity condition wins.

---

## 4. Threshold Enforcement

Thresholds apply to normalized values:

- Temperature (°F)
- Wind speed (mph)
- Wind gust (mph)
- Precipitation (mm)

### 4.1 Threshold Flags

| Flag | Description |
|------|-------------|
| `--temp-warn` | WARNING if temperature ≥ value |
| `--temp-crit` | CRITICAL if temperature ≥ value |
| `--wind-warn` | WARNING if wind speed ≥ value |
| `--wind-crit` | CRITICAL if wind speed ≥ value |
| `--gust-warn` | WARNING if wind gust ≥ value |
| `--gust-crit` | CRITICAL if wind gust ≥ value |
| `--precip-warn` | WARNING if precipitation ≥ value |
| `--precip-crit` | CRITICAL if precipitation ≥ value |

Thresholds are optional.  
If none are provided, the plugin performs monitoring only.

---

## 5. UNKNOWN Enforcement

The plugin returns **UNKNOWN** when:

- Location cannot be resolved  
- Provider returns an error or timeout  
- Required fields are missing  
- Input is invalid  
- Internal normalization fails  

UNKNOWN always overrides OK/WARNING/CRITICAL.

Example:

UNKNOWN - Failed to resolve location "Wichitaz, KS"

Code

---

## 6. Perfdata Enforcement

Perfdata is always included in default mode.

Rules:

- All fields must be present  
- All values must be normalized and rounded  
- No units in perfdata values  
- Field order is deterministic  

Perfdata fields:

temp=<°F> wind=<mph> gust=<mph> precip=<mm> clouds=<%>

Code

Example:

| temp=72 wind=8 gust=12 precip=0 clouds=20

Code

---

## 7. Verbose Mode Enforcement

Verbose mode (`-v`) is diagnostic only.

Rules:

- Multi‑line output is allowed  
- Resolver and provider metadata must be included  
- Raw provider fields must be shown  
- Final line must still contain a valid Nagios/Icinga status line  

Verbose mode **must never** break default mode behavior.

---

## 8. JSON Mode Enforcement

JSON mode (`--json`) produces:

- Deterministic schema  
- Fully structured metadata  
- Final status included in the JSON  
- No human‑readable summary line unless explicitly included in the JSON block  

JSON mode is intended for:

- Dashboards  
- Log pipelines  
- Automated diagnostics  

See `Metadata_Schema.md` for the full schema.

---

## 9. Deterministic Behavior Guarantees

`check_weather.py` guarantees:

- No nondeterministic output  
- No caching or local writes  
- No GUI dependencies  
- Stable field names  
- Stable perfdata ordering  
- Stable severity evaluation  
- Stable resolver behavior  
- Stable normalization rules  

These guarantees ensure consistent monitoring behavior across all supported platforms.

---

## 10. Examples

### OK

OK - Temp 68°F, Wind 5 mph | temp=68 wind=5 gust=7 precip=0 clouds=10

Code

### WARNING

WARNING - Temp 92°F exceeds warning threshold (90°F) | temp=92 wind=8 gust=12 precip=0 clouds=20

Code

### CRITICAL

CRITICAL - Wind gust 48 mph exceeds critical threshold (45 mph) | temp=70 wind=20 gust=48 precip=0 clouds=30

Code

### UNKNOWN

UNKNOWN - Provider error: Open-Meteo returned HTTP 500