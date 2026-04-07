# Usage

`check_weather.py` retrieves current weather conditions and short‑term forecast data using Open‑Meteo and Zippopotam.us. It resolves locations deterministically, evaluates thresholds, and outputs Nagios/Icinga‑compatible status lines with perfdata.

This document describes all CLI flags, output modes, examples, and integration notes.

---

## 1. Basic Invocation

```bash
check_weather.py -l "<location>"
```

The <location> may be:

* City and state: "Wichita, KS"
* City and country: "Berlin, DE"
* ZIP code: "67576"
* Latitude/longitude: "38.0,-98.7"

The resolver automatically determines which provider to use.

## 2. Command‑Line Options

**Required**:

```-l, --location <value>```

Location string to resolve. Required for all checks.

## 3. Threshold Options

Thresholds apply to the current conditions returned by Open‑Meteo.

* --temp-warn <°F> — WARNING if temperature ≥ value
* --temp-crit <°F> — CRITICAL if temperature ≥ value
* --wind-warn <mph> — WARNING if wind speed ≥ value
* --wind-crit <mph> — CRITICAL if wind speed ≥ value
* --gust-warn <mph> — WARNING if wind gust ≥ value
* --gust-crit <mph> — CRITICAL if wind gust ≥ value
* --precip-warn <mm> — WARNING if precipitation ≥ value
* --precip-crit <mm> — CRITICAL if precipitation ≥ value

If no thresholds are provided, the plugin always returns OK unless a resolver or provider error occurs.

## 4. Output Modes

### Default (Nagios/Icinga)

Single‑line output with status, summary, and perfdata:

```Code
OK - Temp 72°F, Wind 8 mph, Gust 12 mph | temp=72 wind=8 gust=12 precip=0
```

### Verbose Mode

-v enables resolver diagnostics, provider metadata, and expanded fields.

```Code
check_weather.py -l "St John, KS" -v
```

Verbose mode includes:

* Resolver path (ZIP → lat/lon, city/state → geocode, etc.)
* Provider URLs used
* Raw provider fields
* Normalized values
* Threshold evaluation details

### JSON Mode

--json outputs structured JSON suitable for ingestion by dashboards or log pipelines.

Example:

```bash
check_weather.py -l "Denver, CO" --json
```

Output includes:

* Normalized weather fields
* Resolver metadata
* Provider metadata
* Threshold evaluation
* Perfdata block

See Metadata_Schema.md for the full schema.

## 5. Exit Codes
| Code | Meaning |
| :---: | :--- |
| 0 |	OK |
| 1 |	WARNING |
| 2 |	CRITICAL |
|3 | UNKNOWN (resolver failure, provider error, invalid input) |

Exit codes follow Nagios/Icinga conventions.

## 6. Examples

### Basic City Lookup

```bash
check_weather.py -l "Wichita, KS"
```

### ZIP Code Lookup

```bash
check_weather.py -l 67576
```

### Latitude/Longitude

```bash
check_weather.py -l "38.0,-98.7"
```

### Temperature Thresholds

```bash
check_weather.py -l "Phoenix, AZ" --temp-warn 95 --temp-crit 105
```

### Wind and Gust Thresholds

```bash
check_weather.py -l "Chicago, IL" --wind-warn 20 --wind-crit 30 --gust-warn 35 --gust-crit 45
```

### Verbose Diagnostic Output

```bash
check_weather.py -l "St John, KS" -v
```

### JSON Output

```bash
check_weather.py -l "Denver, CO" --json
```

## 7. Perfdata Fields
Perfdata is always included in default mode:

```Code
temp=<°F> wind=<mph> gust=<mph> precip=<mm> clouds=<%>
```

Values are normalized and rounded for graph‑friendly ingestion.

## 8. Nagios / Icinga Integration

### Command Definition (Nagios)

```cfgdefine command {
    command_name    check_weather
    command_line    /usr/lib/nagios/plugins/check_weather.py -l "$ARG1$" $ARG2$
}
```

### Service Example

```cfg
define service {
    host_name       weather-host
    service_description  Weather - Wichita
    check_command   check_weather!"Wichita, KS"! --temp-warn 90 --temp-crit 100
}
```

### Icinga 2 CheckCommand

```icinga2
object CheckCommand "check_weather" {
    command = [ "/usr/lib64/nagios/plugins/check_weather.py" ]

    arguments += {
        "-l" = "$location$"
        "--temp-warn" = "$temp_warn$"
        "--temp-crit" = "$temp_crit$"
    }
}
```

## 9. Resolver Behavior Summary

* ZIP codes → Zippopotam.us → lat/lon
* City/state or city/country → Open‑Meteo geocoding
* Lat/lon → used directly
* All paths converge into Open‑Meteo forecast API

Resolver failures return *UNKNOWN* with diagnostic details.

## 10. Error Handling

The plugin returns UNKNOWN for:

* Invalid or ambiguous location
* Provider timeout or HTTP error
* Missing required fields in provider response
* Internal parsing or normalization errors

Verbose mode (-v) includes full diagnostics.