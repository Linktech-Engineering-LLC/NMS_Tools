# Provider Architecture

Deterministic Provider Model for check_weather.py

[check_weather.py] uses a deterministic, two‑provider architecture:

1. **Weather Provider** — always Open‑Meteo
2. **Location Provider** — Zippopotam.us or Open‑Meteo Geocoding depending on input type

This document defines the provider selection rules, URL construction, metadata guarantees, and resolver behavior.

## 1. Overview

The tool separates weather retrieval from location resolution.

| Function | Provider |	Notes |
| :--- | :--- | :--- |
| Weather data | **Open‑Meteo** | Always used; selected via --provider (validated but not switchable) |
| ZIP → lat/lon | **Zippopotam.us** | Used only when input is a ZIP code |
| City/state → lat/lon | Open‑Meteo Geocoding | Used when input is not a ZIP |
| Direct lat/lon | None | No provider lookup required |

This separation ensures deterministic behavior and clear operator visibility.

## 2. Weather Provider (Always Open‑Meteo)

### Provider Name

```open-meteo```

### Base URL

```https://api.open-meteo.com/v1/forecast```

### Full Forecast URL

Constructed with:

- latitude
- longitude
- hourly fields
- timezone
- unit system

Example:

```https://api.open-meteo.com/v1/forecast?latitude=38.03&longitude=-98.76&current_weather=true&hourly=temperature_2m,...```

### Metadata Emitted

In resolved_location:

- weather_provider
- weather_provider_url
- weather_url (full URL)

Weather provider is **never switchable** today.
```--provider``` is validated and logged but does not change execution.

## 3. Location Providers
### 3.1 ZIP Code Resolution

Used when input matches:

```^\d{5}$```

#### Provider Name

```zippopotam.us```

#### URL Pattern

```https://api.zippopotam.us/<country>/<zip>```

Example:

```https://api.zippopotam.us/US/67576```

#### Metadata Emitted

- location_provider: "zippopotam.us"
- location_provider_url: "https://api.zippopotam.us/US/67576"

### 3.2 City/State Resolution

Used when input is not a ZIP and not lat/lon.

#### Provider Name

```open-meteo```

#### URL Pattern
```https://geocoding-api.open-meteo.com/v1/search?name=<query>```

Example:

```https://geocoding-api.open-meteo.com/v1/search?name=Saint John```

#### Metadata Emitted

- location_provider: "open-meteo"
- location_provider_url: "<full geocoding URL>"

### 3.3 Direct Latitude/Longitude
Used when input matches:

```<lat>,<lon>```

#### Provider Name

```direct```

#### URL

```None``` — no provider lookup is performed.

#### Metadata Emitted

- location_provider: "direct"
- location_provider_url: null

## 4. Provider Metadata in JSON Output

The resolved_location block always includes:

| Field | Description |
| :--- | :--- |
| input | Original user input |
| weather_provider | Always "open-meteo" |
| weather_provider_url | Base forecast URL |
| location_provider | "zippopotam.us", "open-meteo", or "direct" |
| location_provider_url | URL used for resolution (or null) |
| city | Resolved city |
| state | Resolved state |
| zip | ZIP code (if applicable) |
| country | ISO country code |
| latitude | Decimal latitude |
| longitude | Decimal longitude |
| weather_url | Full forecast URL used |

This block is always present and never changes shape.

## 5. Deterministic Behavior Guarantees

check_weather.py guarantees:

- Provider selection is deterministic
- Provider URLs reflect the exact endpoints used
- No fallback providers
- No randomization
- No silent provider switching
- No ambiguous provider names
- All provider metadata is emitted in JSON and verbose modes
- Provider metadata is never emitted in Nagios mode

These guarantees ensure stable monitoring behavior across all platforms.

## 6. Examples

### ZIP Input

Location Provider: zippopotam.us
Location Provider URL: https://api.zippopotam.us/US/67576
Weather Provider: open-meteo
Weather Provider URL: https://api.open-meteo.com/v1/forecast

### City Input

Location Provider: open-meteo
Location Provider URL: https://geocoding-api.open-meteo.com/v1/search?name=Saint John
Weather Provider: open-meteo
Weather Provider URL: https://api.open-meteo.com/v1/forecast

### Lat/Lon Input

Location Provider: direct
Location Provider URL: null
Weather Provider: open-meteo
Weather Provider URL: https://api.open-meteo.com/v1/forecast