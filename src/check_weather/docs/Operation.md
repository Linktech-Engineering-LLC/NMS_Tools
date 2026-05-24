markdown
# Operation

`check_weather.py` retrieves current weather conditions using Open‑Meteo and resolves locations using Open‑Meteo Geocoding and Zippopotam.us. The tool is designed for deterministic, operator‑grade monitoring environments and produces clean Nagios/Icinga‑compatible output.

This document describes the internal resolver flow, provider interactions, threshold evaluation, normalization rules, and error handling.

---

## 1. High‑Level Flow

1. Parse CLI arguments  
2. Resolve the location into latitude/longitude  
3. Query Open‑Meteo for current conditions  
4. Normalize all provider fields  
5. Evaluate thresholds  
6. Produce Nagios/Icinga output (default) or verbose/JSON output  
7. Exit with the appropriate status code  

All steps are deterministic and produce consistent output across platforms.

---

## 2. Location Resolution

The resolver accepts four input types:

### **2.1 ZIP Code**
If the location is a 5‑digit numeric string:

- Query `https://api.zippopotam.us/us/<zip>`
- Extract:
  - `latitude`
  - `longitude`
  - `place name`
  - `state abbreviation`
- Pass lat/lon to the weather provider

Failures return **UNKNOWN**.

---

### **2.2 City + State or City + Country**

Examples:
- `"Wichita, KS"`
- `"Berlin, DE"`

Resolution steps:

1. Parse the string into `city` and `region`  
2. Query Open‑Meteo Geocoding:
https://geocoding-api.open-meteo.com/v1/search?name= (geocoding-api.open-meteo.com in Bing)<city>&count=1

Code
3. Extract:
- `latitude`
- `longitude`
- `country_code`
- `admin1` (state/province)
4. Pass lat/lon to the weather provider

Ambiguous or missing results return **UNKNOWN**.

---

### **2.3 Latitude/Longitude Pair**

If the input matches `"<lat>,<lon>"`:

- Use the coordinates directly  
- No external resolver is called  

Invalid coordinates return **UNKNOWN**.

---

### **2.4 Resolver Behavior Summary**

| Input Type | Resolver Used | Failure Mode |
|------------|----------------|--------------|
| ZIP code | Zippopotam.us | UNKNOWN |
| City/state or city/country | Open‑Meteo Geocoding | UNKNOWN |
| Lat/lon | None | UNKNOWN |
| Anything else | Rejected | UNKNOWN |

Verbose mode (`-v`) prints the full resolver path and provider URLs.

---

## 3. Weather Provider Interaction

All weather data is retrieved from:

https://api.open-meteo.com/v1/forecast

Code

The plugin requests:

- Current temperature (°F)
- Wind speed (mph)
- Wind gust (mph)
- Precipitation (mm)
- Cloud cover (%)

The provider returns SI units; the plugin normalizes values to operator‑friendly units.

---

## 4. Normalization Rules

All values are normalized before threshold evaluation and perfdata output.

| Field | Provider Unit | Normalized Unit | Notes |
|-------|----------------|------------------|-------|
| Temperature | °C | °F | Rounded to nearest integer |
| Wind speed | m/s | mph | Rounded |
| Wind gust | m/s | mph | Rounded |
| Precipitation | mm | mm | Rounded to 1 decimal |
| Cloud cover | % | % | Rounded |

Normalization is deterministic and consistent across output modes.

---

## 5. Threshold Evaluation

Thresholds apply to **current** conditions only.

### **5.1 Temperature**

- `--temp-warn <°F>` → WARNING if temp ≥ value  
- `--temp-crit <°F>` → CRITICAL if temp ≥ value  

### **5.2 Wind Speed**

- `--wind-warn <mph>`  
- `--wind-crit <mph>`  

### **5.3 Wind Gust**

- `--gust-warn <mph>`  
- `--gust-crit <mph>`  

### **5.4 Precipitation**

- `--precip-warn <mm>`  
- `--precip-crit <mm>`  

### **5.5 Threshold Precedence**

1. CRITICAL  
2. WARNING  
3. OK  

If multiple thresholds are exceeded, the highest‑severity condition wins.

If no thresholds are provided, the plugin always returns **OK** unless a resolver or provider error occurs.

Verbose mode prints the threshold evaluation chain.

---

## 6. Output Modes

### **6.1 Default (Nagios/Icinga)**

Single line:

OK - Temp 72°F, Wind 8 mph, Gust 12 mph | temp=72 wind=8 gust=12 precip=0 clouds=20

Code

Rules:

- No extra lines  
- No resolver details  
- No provider metadata  
- Always includes perfdata  
- Status text always begins the line  

---

### **6.2 Verbose Mode**

Enabled with `-v`.

Includes:

- Resolver path  
- Provider URLs  
- Raw provider fields  
- Normalized values  
- Threshold evaluation details  
- Final Nagios/Icinga line  

Verbose mode is multi‑line and intended for diagnostics.

---

### **6.3 JSON Mode**

Enabled with `--json`.

Includes:

- Normalized weather fields  
- Resolver metadata  
- Provider metadata  
- Threshold evaluation  
- Perfdata block  
- Final status  

JSON mode is deterministic and schema‑aligned.  
See `Metadata_Schema.md` for full structure.

---

## 7. Perfdata

Perfdata is always included in default mode:

temp=<°F> wind=<mph> gust=<mph> precip=<mm> clouds=<%>

Code

Values are rounded for graph‑friendly ingestion.

---

## 8. Error Handling

The plugin returns **UNKNOWN** for:

- Invalid or ambiguous location  
- Resolver failure  
- Provider timeout or HTTP error  
- Missing required fields  
- Internal parsing or normalization errors  

Verbose mode prints the full error chain.

---

## 9. Exit Codes

| Code | Meaning |
|------|---------|
| **0** | OK |
| **1** | WARNING |
| **2** | CRITICAL |
| **3** | UNKNOWN |

Exit codes follow Nagios/Icinga conventions.

---

## 10. Deterministic Behavior Guarantees

`check_weather.py` guarantees:

- No caching  
- No local writes  
- No GUI dependencies  
- No nondeterministic output  
- Clean, single‑line Nagios/Icinga output  
- Stable JSON schema  
- Stable resolver behavior  
- Stable normalization rules  

This ensures predictable monitoring behavior across all supported platforms.