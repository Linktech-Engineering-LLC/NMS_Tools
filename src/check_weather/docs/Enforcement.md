# Enforcement Model
Deterministic Monitoring Enforcement for NMS_Tools

check_weather.py follows the unified NMS_Tools enforcement model used across all monitoring plugins.
The tool produces deterministic, single‑line Nagios/Icinga output in default mode and supports verbose and JSON modes for diagnostics and ingestion.

This document defines the enforcement rules, output guarantees, severity model, and behavior under monitoring and policy enforcement.

## 1. Enforcement Overview
check_weather.py implements two enforcement layers:

### 1.1. Monitoring Enforcement (always enabled)

- Resolves location
- Retrieves weather data
- Normalizes values
- Evaluates thresholds
- Produces Nagios/Icinga output

### 1.2. Policy Enforcement (threshold‑based, optional)

Activated only when threshold flags are provided.

- Determines WARNING/CRITICAL states
- Ensures deterministic severity selection
- Applies precedence rules

If no thresholds are provided, the plugin returns OK unless a resolver or provider error occurs.

## 2. Output Rules

### 2.1 Default Mode (Nagios/Icinga)

Nagios mode is the default when no other output mode is selected.

- Default mode must produce:
- Exactly one line of output
- No leading or trailing whitespace
- No resolver or provider details
- Status text at the beginning of the line
- Perfdata appended after a pipe (|)
- No additional lines, warnings, or debug text
- Logging is disabled (Nagios plugins must be side‑effect‑free)

Example:

```OK: Weather normal: 72°F, 8 mph | temp=72 wind=8 gust=12 precip=0 clouds=20```

This output is safe for:

- Nagios Core
- Icinga 2
- NRPE

Any monitoring engine expecting single‑line plugin output

## 3. Severity Model
Severity is determined by threshold evaluation.

### 3.1 Severity Levels

| Level |	Meaning |
| :--- | :--- |
| CRITICAL |	One or more critical thresholds exceeded |
| WARNING |	One or more warning thresholds exceeded |
| OK |	No thresholds exceeded |
| UNKNOWN |	Resolver or provider failure |

### 3.2 Precedence

Severity precedence is deterministic:

- CRITICAL
- WARNING
- OK
- UNKNOWN (only for errors)

If multiple thresholds are exceeded, the highest‑severity condition wins.

## 4. Threshold Enforcement

Thresholds apply to normalized values:

- Temperature (°F) -- bi-directional thresholds supported
- Wind speed (mph)
- Wind gust (mph)
- Humidity (%)
- Precipitation (mm)
- Cloud cover (%)

### 4.1 Temperature Thresholds (Bi‑Directional)

Temperature thresholds support both hot and cold evaluation.

The plugin automatically determines whether thresholds represent:

- Hot mode (thresholds above the current temperature)
  → Evaluate using temp ≥ threshold
- Cold mode (thresholds below the current temperature)
  → Evaluate using temp ≤ threshold

This determination is automatic, based on the relative position of the thresholds to the current temperature.

Rules:

- If both thresholds are above the current temperature → hot thresholds
- If both thresholds are below the current temperature → cold thresholds
- If mixed → defaults to hot mode (Nagios‑style convention)

Flags:

| Flag |	Meaning |
| :--- | :--- |
| --warning-temp |	WARNING if temp ≥ value (hot) or temp ≤ value (cold) |
| --critical-temp |	CRITICAL if temp ≥ value (hot or temp ≤ value (cold) |

Example:

- Hot thresholds:
  ```--warning-temp 85 --critical-temp 95```
  → WARNING at 85+, CRITICAL at 95+
- Cold thresholds:
  ```--warning-temp 32 --critical-temp 0```
  → WARNING at 32 or below, CRITICAL at 0 or below

Temperature is the only metric with bi‑directional threshold logic.

### 4.2 Unidirectional Thresholds (≥ Only)

Wind, gust, humidity, precipitation, and cloud cover thresholds are **always evaluated using ≥**.

Flags:

| Metric | Warning |	Critical |
| :--- | :--- | :--- |
| Wind | --warning-wind | --critical-wind |
| Gust | --warning-gust | --critical-gust |
| Humidity | --warning-humidity | --critical-humidity |
| Precipitation | --warning-precip | --critical-precip |
| Cloud Cover | --warning-cloud | --critical-cloud |

These thresholds are not bi‑directional.

Thresholds are optional.
If none are provided, the plugin performs monitoring only.

## 5. UNKNOWN Enforcement

The plugin returns UNKNOWN when:

- Location cannot be resolved
- Provider returns an error or timeout
- Required fields are missing
- Input is invalid
- Internal normalization fails
- [UNKNOWN] always overrides [OK/WARNING/CRITICAL].

Example:

```UNKNOWN: Failed to resolve location "Wichitaz, KS"```

## 6. Perfdata Enforcement

Perfdata is always included in default mode.

Rules:

- All fields must be present
- All values must be normalized and rounded
- No units in perfdata values
- Field order is deterministic

Perfdata fields:

```temp=<°F> wind=<mph> gust=<mph> precip=<mm> clouds=<%>```

Example:

```temp=72 wind=8 gust=12 precip=0 clouds=20```

## 7. Verbose Mode Enforcement

Verbose mode (-v) is diagnostic only.

Rules:

- Multi‑line output is allowed
- Resolver and provider metadata must be included
- Raw provider fields must be shown
- Final line must still contain a valid Nagios/Icinga status line
- Logging is **enabled** in verbose mode

Verbose mode **must never** break default mode behavior.

## 8. JSON Mode Enforcement

JSON mode (--json) produces:

- Deterministic schema
- Fully structured metadata
- Final status included in the JSON
- No human‑readable summary line unless included in the JSON block
- Logging is enabled in JSON mode

[JSON] mode is intended for:

- Dashboards
- Log pipelines
- Automated diagnostics

## 9. Deterministic Behavior Guarantees

check_weather.py guarantees:

- No nondeterministic output
- No GUI dependencies
- Stable field names
- Stable perfdata ordering
- Stable severity evaluation
- Stable resolver behavior
- Stable normalization rules
- Deterministic caching
- Deterministic logging (when enabled)
- No logging in Nagios mode

These guarantees ensure consistent monitoring behavior across all supported platforms.

## 10. Examples

OK

```OK: Temp 68°F, Wind 5 mph | temp=68 wind=5 gust=7 precip=0 clouds=10```

WARNING

```WARNING: Temp 92°F exceeds warning threshold (90°F) | temp=92 wind=8 gust=12 precip=0 clouds=20```

CRITICAL

```CRITICAL: Wind gust 48 mph exceeds critical threshold (45 mph) | temp=70 wind=20 gust=48 precip=0 clouds=30```

UNKNOWN

```UNKNOWN: Provider error: Open‑Meteo returned HTTP 500```