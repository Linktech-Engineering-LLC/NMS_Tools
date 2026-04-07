#!/usr/bin/env python3
"""
Package: NMS_Tools
Author: Leon McClatchey
Company: Linktech Engineering LLC
Created: 2026-04-07
Last Modified: 2026-04-07
File: check_weather.py
Description: Deterministic weather checker with ZIP/city/lat-long support.
"""

import argparse
import json
import requests
import sys
import time
from typing import Any, Dict, Optional, Tuple
import urllib.parse
import urllib.request

# ---------------------------------------------------------------------------
# Nagios Status Codes
# ---------------------------------------------------------------------------
STATUS_OK = 0
STATUS_WARNING = 1
STATUS_CRITICAL = 2
STATUS_UNKNOWN = 3
# Other Global Constants
SCRIPT_VERSION = "1.0.0"
US_STATES = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas",
    "CA": "California", "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware",
    "FL": "Florida", "GA": "Georgia", "HI": "Hawaii", "ID": "Idaho",
    "IL": "Illinois", "IN": "Indiana", "IA": "Iowa", "KS": "Kansas",
    "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine", "MD": "Maryland",
    "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi",
    "MO": "Missouri", "MT": "Montana", "NE": "Nebraska", "NV": "Nevada",
    "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico", "NY": "New York",
    "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio", "OK": "Oklahoma",
    "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island", "SC": "South Carolina",
    "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas", "UT": "Utah",
    "VT": "Vermont", "VA": "Virginia", "WA": "Washington", "WV": "West Virginia",
    "WI": "Wisconsin", "WY": "Wyoming"
}
WEATHER_CODES = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    56: "Freezing drizzle",
    57: "Freezing drizzle (dense)",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    66: "Freezing rain",
    67: "Freezing rain (heavy)",
    71: "Slight snow",
    73: "Moderate snow",
    75: "Heavy snow",
    77: "Snow grains",
    80: "Rain showers",
    81: "Rain showers (moderate)",
    82: "Rain showers (violent)",
    85: "Snow showers",
    86: "Snow showers (heavy)",
    95: "Thunderstorm",
    96: "Thunderstorm with hail",
    99: "Thunderstorm with heavy hail",
}

# -----------------------------
# Custom Formatter
# -----------------------------
class CustomFormatter(
    argparse.ArgumentDefaultsHelpFormatter,
    argparse.RawDescriptionHelpFormatter
):
    def _get_help_string(self, action):
        help_text = action.help or ""
        if "%(default)" in help_text:
            return help_text
        if action.default in (None, False):
            return help_text
        return f"{help_text} (default: {action.default})"
class CheckArgError(Exception):
    pass
class CheckArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        print(f"ERROR: {message}\n")
        self.print_help()
        sys.exit(STATUS_UNKNOWN)
# ----------------------------------------------
# Argument Parser
# -----------------------------------------------
def build_parser() -> argparse.Namespace:
    parser = CheckArgumentParser(
        description="Weather Checking Tool\n\n"
                    "Fetches weather data from Open-Meteo, applies thresholds, "
                    "and outputs Nagios, JSON, verbose, or quiet mode results.",
        formatter_class=CustomFormatter,
        add_help=True,
    )

    # Core options
    core = parser.add_argument_group("Core Options")
    core.add_argument(
        "-l", "--location",
        required=True,
        help='Location to check. Accepts ZIP code (67576), city name ("St John, KS"), '
             'or latitude,longitude (38.00,-98.76).',
    )
    core.add_argument(
        "--country",
        default="US",
        help="Country code for location resolution",
    )
    core.add_argument(
        "-u", "--units",
        choices=["metric", "imperial"],
        default="metric",
        help="Unit system: metric (°C, kph) or imperial (°F, mph).",
    )
    core.add_argument(
        "--timeout",
        type=int,
        default=5,
        help="Connection timeout in seconds",
    )
    core.add_argument(
        "--log-dir",
        dest="log_dir",
        help="Directory to store logs (optional). If omitted, logging is disabled.",
    )
    core.add_argument(
        "--log-max-mb",
        type=int,
        default=50,
        help="Maximum log size in MB before rotation.",
    )

    # Output modes
    out = parser.add_argument_group("Output Options")
    out.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Detailed output",
    )
    out.add_argument(
        "-j", "--json",
        action="store_true",
        help="JSON output for automation",
    )
    out.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Quiet mode: exit code only",
    )
    out.add_argument(
        "-V", "--version",
        action="store_true",
        help="Show script and Python version",
    )

    # Weather thresholds
    weather = parser.add_argument_group("Weather Options")
    weather.add_argument(
        "--warning-temp",
        type=float,
        help="Warning threshold for temperature (°C or °F depending on --units)",
    )
    weather.add_argument(
        "--critical-temp",
        type=float,
        help="Critical threshold for temperature (°C or °F depending on --units)",
    )
    weather.add_argument(
        "--warning-wind",
        type=float,
        help="Warning threshold for wind speed (kph or mph depending on --units)",
    )
    weather.add_argument(
        "--critical-wind",
        type=float,
        help="Critical threshold for wind speed (kph or mph depending on --units)",
    )
    weather.add_argument(
        "--warning-gust",
        type=float,
        help="Warning threshold for wind gust speed (kph or mph depending on --units)",
    )
    weather.add_argument(
        "--critical-gust",
        type=float,
        help="Critical threshold for wind gust speed (kph or mph depending on --units)",
    )
    weather.add_argument(
        "--warning-humidity",
        type=float,
        help="Warning threshold for humidity (%%)",
    )
    weather.add_argument(
        "--critical-humidity",
        type=float,
        help="Critical threshold for humidity (%%)",
    )
    weather.add_argument(
        "--warning-precip",
        type=float,
        help="Warning threshold for precipitation (mm or inches depending on --units)",
    )
    weather.add_argument(
        "--critical-precip",
        type=float,
        help="Critical threshold for precipitation (mm or inches depending on --units)",
    )
    weather.add_argument(
        "--warning-cloud",
        type=float,
        help="Warning threshold for cloud cover (%%)",
    )
    weather.add_argument(
        "--critical-cloud",
        type=float,
        help="Critical threshold for cloud cover (%%)",
    )

    # Provider + debug
    debug = parser.add_argument_group("Debug Options")
    debug.add_argument(
        "--provider",
        choices=["open-meteo"],
        default="open-meteo",
        help="Weather provider to use",
    )
    debug.add_argument(
        "--show-location-details",
        action="store_true",
        help="Show resolved location details and provider URL for debugging",
    )

    args = parser.parse_args()
    return args
# ---------------------------------------------------------------------------
# Location Resolver (ZIP, City, Lat/Long)
# ---------------------------------------------------------------------------
def resolve_location(args):
    """
    Resolve ZIP, city, or lat/long into a structured location object.
    Uses args.location, args.country, args.timeout.
    """

    original = args.location.strip()
    country = (args.country or "US").upper()
    timeout = args.timeout

    # ------------------------------------------------------------
    # Helper: build final structured location object
    # ------------------------------------------------------------
    def make_location(provider, lat, lon, city=None, state=None, zip_code=None):
        return {
            "query": original,
            "provider": provider,
            "latitude": lat,
            "longitude": lon,
            "city": city,
            "state": state,
            "country": country,
            "zip": zip_code
        }

    # ------------------------------------------------------------
    # Case 1: Lat/Long (handles negative values safely)
    # ------------------------------------------------------------
    if "," in original:
        parts = original.split(",", 1)
        try:
            lat = float(parts[0].strip())
            lon = float(parts[1].strip())
            return make_location("direct", lat, lon)
        except ValueError:
            pass  # Not lat/long → fall through

    # ------------------------------------------------------------
    # Case 2: Postal code (digits only)
    # Zippopotam.us supports many countries, not just US
    # ------------------------------------------------------------
    if original.isdigit():
        zip_url = f"https://api.zippopotam.us/{country}/{original}"
        r = requests.get(zip_url, timeout=timeout)

        if r.status_code == 200:
            z = r.json()
            place = z["places"][0]
            return make_location(
                provider="zippopotam.us",
                lat=float(place["latitude"]),
                lon=float(place["longitude"]),
                city=place["place name"],
                state=place.get("state"),
                zip_code=original
            )
        # ZIP failed → fall through to city lookup

    # ------------------------------------------------------------
    # Case 3: City name (strip state if present)
    # ------------------------------------------------------------
    parts = [p.strip() for p in original.split(",")]
    city = parts[0]

    # Expand US state abbreviations → full names
    state_filter = None
    if len(parts) >= 2:
        raw_state = parts[1].strip()
        upper_state = raw_state.upper()
        state_filter = US_STATES.get(upper_state, raw_state)

    # ------------------------------------------------------------
    # 1. First try: global search (no country filter)
    # This is required because Open-Meteo sometimes ignores country=US
    # ------------------------------------------------------------
    geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}"
    r = requests.get(geo_url, timeout=timeout)

    if r.status_code == 200:
        data = r.json()
        results = data.get("results", [])

        # If user provided a state, filter by admin1 FIRST
        if state_filter:
            filtered = [
                r for r in results
                if r.get("admin1", "").upper().startswith(state_filter.upper())
            ]
            if filtered:
                entry = filtered[0]
                return make_location(
                    provider="open-meteo",
                    lat=entry["latitude"],
                    lon=entry["longitude"],
                    city=entry.get("name"),
                    state=entry.get("admin1"),
                    zip_code=None
                )

    # ------------------------------------------------------------
    # 2. Second try: country-filtered search
    # ------------------------------------------------------------
    geo_url = (
        "https://geocoding-api.open-meteo.com/v1/search"
        f"?name={city}&country={country}"
    )
    r = requests.get(geo_url, timeout=timeout)

    if r.status_code == 200:
        data = r.json()
        results = data.get("results", [])

        if results:
            entry = results[0]
            return make_location(
                provider="open-meteo",
                lat=entry["latitude"],
                lon=entry["longitude"],
                city=entry.get("name"),
                state=entry.get("admin1"),
                zip_code=None
            )

    # ------------------------------------------------------------
    # Final fallback: Zippopotam.us city lookup (global)
    # ------------------------------------------------------------
    city_url = f"https://api.zippopotam.us/{country}/{city}"
    r = requests.get(city_url, timeout=timeout)

    if r.status_code == 200:
        z = r.json()
        place = z["places"][0]
        return make_location(
            provider="zippopotam.us",
            lat=float(place["latitude"]),
            lon=float(place["longitude"]),
            city=place["place name"],
            state=place.get("state"),
            zip_code=z.get("post code")
        )

    # ------------------------------------------------------------
    # Nothing worked
    # ------------------------------------------------------------
    raise RuntimeError(f"City not found: {original}")
# -----------------------------
# Open-Meteo fetch
# -----------------------------
def fetch_weather_open_meteo(lat: float, lon: float, timeout: int) -> Tuple[Dict[str, Any], str]:
    base = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current_weather": "true",
        "hourly": ",".join([
            "temperature_2m",
            "relativehumidity_2m",
            "precipitation",
            "cloudcover",
            "windspeed_10m",
            "windgusts_10m",
            "weathercode",
        ]),
        "timezone": "auto",
    }
    url = f"{base}?{urllib.parse.urlencode(params)}"

    with urllib.request.urlopen(url, timeout=timeout) as resp:
        raw = resp.read()
    data = json.loads(raw)

    # Align current_weather time to hourly index
    current = data.get("current_weather", {})
    hourly = data.get("hourly", {})
    times = hourly.get("time", [])

    current_time = current.get("time")
    idx = None
    if current_time in times:
        idx = times.index(current_time)
    elif times:
        idx = len(times) - 1  # fallback: last entry

    if idx is None:
        raise ValueError("Unable to align current weather with hourly data")

    def h(field: str, default=None):
        arr = hourly.get(field)
        if not arr or idx >= len(arr):
            return default
        return arr[idx]
    result = {
        "time": current_time,
        "temperature_c": h("temperature_2m"),
        "wind_kph": h("windspeed_10m"),
        "wind_gust_kph": h("windgusts_10m"),
        "humidity": h("relativehumidity_2m"),
        "precip_mm": h("precipitation"),
        "cloudcover": h("cloudcover"),
        "condition": h("weathercode"),
    }
    return result, url

def fetch_weather(lat: float, lon: float, timeout: int, provider: str) -> Tuple[Dict[str, Any], str]:
    if provider == "open-meteo":
        return fetch_weather_open_meteo(lat, lon, timeout)
    raise ValueError(f"Unsupported provider: {provider}")

# ---------------------------------------------------------------------------
# Evaluation Logic
# ---------------------------------------------------------------------------
def evaluate_simple(value: Optional[float],
                    warn: Optional[float],
                    crit: Optional[float],
                    label: str) -> Optional[Tuple[int, str]]:
    if value is None:
        return None
    if crit is not None and value >= crit:
        return STATUS_CRITICAL, f"{label} {value:.2f} exceeds critical threshold"
    if warn is not None and value >= warn:
        return STATUS_WARNING, f"{label} {value:.2f} exceeds warning threshold"
    return None
def evaluate_temperature(temp, args, unit):
    wt = args.warning_temp
    ct = args.critical_temp

    # No thresholds → no evaluation
    if wt is None and ct is None:
        return None

    # Determine direction:
    # If both thresholds are below current temp → cold thresholds
    # If both thresholds are above current temp → hot thresholds
    # Mixed thresholds → default to hot (most common)
    cold_mode = False
    if wt is not None and ct is not None:
        if wt < temp and ct < temp:
            cold_mode = True
    elif ct is not None:
        if ct < temp:
            cold_mode = True
    elif wt is not None:
        if wt < temp:
            cold_mode = True

    # -----------------------------
    # Cold thresholds (temp <= threshold)
    # -----------------------------
    if cold_mode:
        if ct is not None and temp <= ct:
            return STATUS_CRITICAL, f"Temperature {temp}°F is below critical threshold"
        if wt is not None and temp <= wt:
            return STATUS_WARNING, f"Temperature {temp}°F is below warning threshold"
        return None

    # -----------------------------
    # Hot thresholds (temp >= threshold)
    # -----------------------------
    if ct is not None and temp >= ct:
        return STATUS_CRITICAL, f"Temperature {temp}°F exceeds critical threshold"
    if wt is not None and temp >= wt:
        return STATUS_WARNING, f"Temperature {temp}°F exceeds warning threshold"

    return None
def evaluate_weather(data: Dict[str, Any], args: argparse.Namespace) -> Tuple[int, str]:
    if args.units == "imperial":
        temp = data.get("temperature_f")
        wind = data.get("wind_mph")
        gust = data.get("wind_gust_mph")
        precip = data.get("precip_in")
        unit_temp = "F"
        unit_wind = "mph"
        unit_precip = "in"
    else:
        temp = data.get("temperature_c")
        wind = data.get("wind_kph")
        gust = data.get("wind_gust_kph")
        precip = data.get("precip_mm")
        unit_temp = "C"
        unit_wind = "kph"
        unit_precip = "mm"

    humidity = data.get("humidity")

    # Temperature (hot + cold)
    if temp is not None:
        r = evaluate_temperature(temp, args, unit_temp)
        if r is not None:
            return r

    # Wind
    r = evaluate_simple(wind, args.warning_wind, args.critical_wind, f"Wind ({unit_wind})")
    if r is not None:
        return r

    # Gust
    r = evaluate_simple(gust, args.warning_gust, args.critical_gust, f"Wind gust ({unit_wind})")
    if r is not None:
        return r

    # Humidity
    r = evaluate_simple(humidity, args.warning_humidity, args.critical_humidity, "Humidity (%)")
    if r is not None:
        return r

    # Precipitation
    r = evaluate_simple(precip, args.warning_precip, args.critical_precip, f"Precipitation ({unit_precip})")
    if r is not None:
        return r

    cloud = data.get("cloudcover")

    r = evaluate_simple(cloud, args.warning_cloud, args.critical_cloud, "Cloud cover (%)")
    if r is not None:
        return r

    # Default OK
    msg = build_normal_message(data, args)
    return STATUS_OK, msg
# ---------------------------------------------------------------------------
# Output Helpers
# ---------------------------------------------------------------------------
def build_normal_message(data: Dict[str, Any], args: argparse.Namespace) -> str:
    if args.units == "imperial":
        t = data.get("temperature_f")
        w = data.get("wind_mph")
        return f"Weather normal: {t:.2f}°F, {w:.2f} mph"
    else:
        t = data.get("temperature_c")
        w = data.get("wind_kph")
        return f"Weather normal: {t:.2f}°C, {w:.2f} kph"
def output_and_exit(status: int, payload: Dict[str, Any], args: argparse.Namespace) -> None:
    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    elif args.verbose:
        verbose_output(payload)
    elif not args.quiet:
        perf = build_perfdata(payload["data"], args)
        print(f"{payload['status']}: {payload['message']} | {perf}")
    sys.exit(status)
def verbose_output(payload: Dict[str, Any]) -> None:
    d = payload["data"]
    print(f"Status: {payload['status']}")
    print(f"Message: {payload['message']}")
    print(f"Location: {payload['location']}")
    if "temperature_f" in d or "temperature_c" in d:
        tf = d.get("temperature_f")
        tc = d.get("temperature_c")
        if tf is not None and tc is not None:
            print(f"Temperature: {tf:.2f}°F ({tc:.2f}°C)")
        elif tf is not None:
            print(f"Temperature: {tf:.2f}°F")
        elif tc is not None:
            print(f"Temperature: {tc:.2f}°C")
    if "wind_mph" in d or "wind_kph" in d:
        wm = d.get("wind_mph")
        wk = d.get("wind_kph")
        if wm is not None and wk is not None:
            print(f"Wind Speed: {wm:.2f} mph ({wk:.2f} kph)")
        elif wm is not None:
            print(f"Wind Speed: {wm:.2f} mph")
        elif wk is not None:
            print(f"Wind Speed: {wk:.2f} kph")
    if "wind_gust_mph" in d or "wind_gust_kph" in d:
        gm = d.get("wind_gust_mph")
        gk = d.get("wind_gust_kph")
        if gm is not None and gk is not None:
            print(f"Wind Gust: {gm:.2f} mph ({gk:.2f} kph)")
        elif gm is not None:
            print(f"Wind Gust: {gm:.2f} mph")
        elif gk is not None:
            print(f"Wind Gust: {gk:.2f} kph")
    if "humidity" in d and d["humidity"] is not None:
        print(f"Humidity: {d['humidity']:.2f}%")
    if "precip_mm" in d or "precip_in" in d:
        pm = d.get("precip_mm")
        pi = d.get("precip_in")
        if pm is not None and pi is not None:
            print(f"Precipitation: {pm:.2f} mm ({pi:.2f} in)")
        elif pm is not None:
            print(f"Precipitation: {pm:.2f} mm")
        elif pi is not None:
            print(f"Precipitation: {pi:.2f} in")
    if "cloudcover" in d and d["cloudcover"] is not None:
        print(f"Cloud Cover: {d['cloudcover']:.2f}%")
    print(f"Condition Code: {d.get('condition')}")
    print(f"Runtime: {payload['runtime_ms']} ms")
def convert_units(data: Dict[str, Any], units: str) -> Dict[str, Any]:
    out = dict(data)

    if units == "imperial":
        # Temperature C → F
        if out.get("temperature_c") is not None:
            out["temperature_f"] = round(out["temperature_c"] * 9/5 + 32, 2)

        # Wind kph → mph
        if out.get("wind_kph") is not None:
            out["wind_mph"] = round(out["wind_kph"] * 0.621371, 2)

        # Gust kph → mph
        if out.get("wind_gust_kph") is not None:
            out["wind_gust_mph"] = round(out["wind_gust_kph"] * 0.621371, 2)

        # Precip mm → inches
        if out.get("precip_mm") is not None:
            out["precip_in"] = round(out["precip_mm"] / 25.4, 2)

    # Do NOT overwrite condition here; keep it numeric
    return out
def format_resolved_name(loc):
    city = loc.get("city")
    state = loc.get("state")
    country = loc.get("country")
    zip_code = loc.get("zip")

    if city and state and zip_code:
        return f"{city}, {state} {zip_code}, {country}"
    if city and state:
        return f"{city}, {state}, {country}"
    if city:
        return f"{city}, {country}"
    return f"{loc['latitude']},{loc['longitude']}"
def strip_none(d):
    return {k: v for k, v in d.items() if v is not None}
# -----------------------------
# Perfdata
# -----------------------------
def build_perfdata(data: Dict[str, Any], args: argparse.Namespace) -> str:
    parts = []

    if args.units == "imperial":
        temp = data.get("temperature_f")
        wind = data.get("wind_mph")
        gust = data.get("wind_gust_mph")
        precip = data.get("precip_in")
    else:
        temp = data.get("temperature_c")
        wind = data.get("wind_kph")
        gust = data.get("wind_gust_kph")
        precip = data.get("precip_mm")

    humidity = data.get("humidity")

    if temp is not None:
        w = args.warning_temp if args.warning_temp is not None else ""
        c = args.critical_temp if args.critical_temp is not None else ""
        parts.append(f"temp={temp:.2f};{w};{c}")

    if wind is not None:
        w = args.warning_wind if args.warning_wind is not None else ""
        c = args.critical_wind if args.critical_wind is not None else ""
        parts.append(f"wind={wind:.2f};{w};{c}")

    if gust is not None:
        w = args.warning_gust if args.warning_gust is not None else ""
        c = args.critical_gust if args.critical_gust is not None else ""
        parts.append(f"gust={gust:.2f};{w};{c}")

    if humidity is not None:
        w = args.warning_humidity if args.warning_humidity is not None else ""
        c = args.critical_humidity if args.critical_humidity is not None else ""
        parts.append(f"humidity={humidity:.2f};{w};{c}")

    if precip is not None:
        w = args.warning_precip if args.warning_precip is not None else ""
        c = args.critical_precip if args.critical_precip is not None else ""
        parts.append(f"precip={precip:.2f};{w};{c}")
    cloud = data.get("cloudcover")
    if cloud is not None:
        w = args.warning_cloud if args.warning_cloud is not None else ""
        c = args.critical_cloud if args.critical_cloud is not None else ""
        parts.append(f"cloud={cloud:.2f};{w};{c}")
    
    return " ".join(parts)
# -----------------------------
# Main
# -----------------------------
def main() -> None:
    args = build_parser()

    if args.version:
        print(f"check_weather.py using Python {sys.version.split()[0]}")
        sys.exit(0)

    start = time.time()

    try:
        loc = resolve_location(args)
        data_raw, url = fetch_weather(
            loc.get("latitude",0),
            loc.get("longitude",0),
            args.timeout,
            args.provider,
        )
        data = convert_units(data_raw, args.units)

        if args.show_location_details and not args.quiet:
            print(f"Resolved location: {format_resolved_name(loc)}")
            print(f"Latitude: {loc.get('latitude')}, Longitude: {loc.get('longitude')}")
            print(f"Provider URL: {url}")

        status, message = evaluate_weather(data, args)

    except Exception as e:
        runtime = round((time.time() - start) * 1000, 2)
        payload = {
            "status": "UNKNOWN",
            "message": str(e),
            "location": args.location,
            "data": {},
            "runtime_ms": runtime,
        }
        output_and_exit(STATUS_UNKNOWN, payload, args)

    runtime = round((time.time() - start) * 1000, 2)
    payload = {
        "status": ["OK", "WARNING", "CRITICAL", "UNKNOWN"][status],
        "message": message,
        "location": format_resolved_name(loc),
        "data": strip_none(data),
        "runtime_ms": runtime,
    }
    output_and_exit(status, payload, args)

if __name__ == "__main__":
    main()
