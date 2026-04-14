#!/usr/bin/env python3
"""
Package: NMS_Tools
Author: Leon McClatchey
Company: Linktech Engineering LLC
Created: 2026-04-07
Last Modified: 2026-04-14
File: check_weather.py
Description: Deterministic weather checker with ZIP/city/lat-long support.
"""

import argparse
import hashlib
import json
import os
import pwd
import re
import requests
import shutil
import sys
import time
import urllib.parse
import urllib.request
import zipfile
from typing import Any, Dict, Optional, Tuple
from pathlib import Path
from datetime import datetime, timedelta
from enum import IntEnum, auto

# ---------------------------------------------------------------------------
# Nagios Status Codes
# ---------------------------------------------------------------------------
STATUS_OK = 0
STATUS_WARNING = 1
STATUS_CRITICAL = 2
STATUS_UNKNOWN = 3
# Other Global Constants
SCRIPT_VERSION = "2.0.0"
DEFAULT_PROVIDER = "open-meteo"
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
STATE_NAME_TO_CODE = {v.lower(): k for k, v in US_STATES.items()}
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
# Flag Classes
class FlagNames(IntEnum):
    VERBOSE = auto()
    JSON = auto()
    QUIET = auto()
    VERSION = auto()

    INCLUDE_GUSTS = auto()
    INCLUDE_PRECIP = auto()
    INCLUDE_CLOUDS = auto()

    IGNORE_CACHE = auto()
    IGNORE_TTL = auto()
    CACHE_INFO = auto()
    FORCE_CACHE = auto()

    SHOW_LOCATION_DETAILS = auto()
    SHOW_CODES = auto()
    NO_COLOR = auto()

    # Provider override is not a boolean flag, so no bit here.
class Flags:
    """
    Operator-grade flag engine for check_weather.
    Backed by a deterministic bitmask.
    """

    def __init__(self):
        self._mask = 0

    # -----------------------------
    # Core bit operations
    # -----------------------------
    def set(self, flag: FlagNames, value: bool = True):
        if value:
            self._mask |= (1 << flag.value)
        else:
            self._mask &= ~(1 << flag.value)

    def get(self, flag: FlagNames) -> bool:
        return bool(self._mask & (1 << flag.value))

    # -----------------------------
    # Convenience accessors
    # -----------------------------
    def __getitem__(self, flag: FlagNames) -> bool:
        return self.get(flag)

    def __setitem__(self, flag: FlagNames, value: bool):
        self.set(flag, value)

    # -----------------------------
    # Introspection
    # -----------------------------
    def active_names(self):
        return [
            name.name
            for name in FlagNames
            if self.get(name)
        ]

    def to_hex(self):
        return f"0x{self._mask:08X}"

    # -----------------------------
    # Build from argparse args
    # -----------------------------
    @classmethod
    def from_args(cls, args):
        f = cls()

        # Output modes
        f[FlagNames.VERBOSE] = args.verbose
        f[FlagNames.JSON] = args.json
        f[FlagNames.QUIET] = args.quiet
        f[FlagNames.VERSION] = args.version

        # Inclusion flags
        f[FlagNames.INCLUDE_GUSTS] = args.include_gusts
        f[FlagNames.INCLUDE_PRECIP] = args.include_precip
        f[FlagNames.INCLUDE_CLOUDS] = args.include_clouds

        # Cache flags
        f[FlagNames.IGNORE_CACHE] = args.ignore_cache
        f[FlagNames.IGNORE_TTL] = args.ignore_ttl
        f[FlagNames.CACHE_INFO] = args.cache_info
        f[FlagNames.FORCE_CACHE] = args.force_cache

        # Debug flags
        f[FlagNames.SHOW_LOCATION_DETAILS] = args.show_location_details
        f[FlagNames.SHOW_CODES] = args.show_codes
        f[FlagNames.NO_COLOR] = args.no_color

        return f
# Color Class with helper
class Color:
    RESET = "\x1b[0m"
    RED = "\x1b[31m"
    YELLOW = "\x1b[33m"
    GREEN = "\x1b[32m"
    BLUE = "\x1b[34m"
    CYAN = "\x1b[36m"
    GRAY = "\x1b[90m"
def colorize(text: str, color: str, enabled: bool) -> str:
    if not enabled:
        return text
    return f"{color}{text}{Color.RESET}"
# ------------------------------------------------------------
# Cache Directory Resolution
# ------------------------------------------------------------
def get_cache_dir():
    # 1. Respect XDG_CACHE_HOME if set
    xdg = os.environ.get("XDG_CACHE_HOME")
    if xdg:
        return Path(xdg) / "nms_tools"

    # 2. Detect Nagios user
    try:
        user = pwd.getpwuid(os.geteuid()).pw_name
    except Exception:
        user = None

    if user in ("nagios", "nrpe"):
        return Path("/var/tmp/nms_tools")

    # 3. Normal user fallback
    return Path.home() / ".cache" / "nms_tools"
# ------------------------------------------------------------
# Cache Directories + TTLs
# ------------------------------------------------------------
CACHE_DIR = get_cache_dir()
WEATHER_CACHE_DIR = CACHE_DIR / "weather"
LOCATION_CACHE_DIR = CACHE_DIR / "location"
WEATHER_CACHE_DIR.mkdir(parents=True, exist_ok=True)
LOCATION_CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_TTL = timedelta(minutes=15)       # Weather TTL
LOCATION_TTL = timedelta(hours=24)      # Location TTL
# ------------------------------------------------------------
# Weather Cache Functions
# ------------------------------------------------------------
def cache_path(key: str) -> Path:
    digest = hashlib.sha256(key.encode()).hexdigest()
    return WEATHER_CACHE_DIR / f"{digest}.json"
def load_cache(key: str):
    path = cache_path(key)
    if not path.exists():
        return None, None

    try:
        with open(path, "r") as f:
            cached = json.load(f)

        ts = datetime.strptime(cached["timestamp"], "%Y-%m-%dT%H:%M:%S.%f")

        if datetime.now() - ts > CACHE_TTL:
            return None, None

        return cached["data"], ts

    except Exception as e:
        print("CACHE ERROR:", e)
        return None, None
def save_cache(key: str, data: dict):
    path = cache_path(key)
    payload = {
        "timestamp": datetime.now().isoformat(),
        "data": data
    }
    with open(path, "w") as f:
        json.dump(payload, f)
    return True
# ------------------------------------------------------------
# Location Cache Functions
# ------------------------------------------------------------
def location_cache_path(key: str) -> Path:
    digest = hashlib.sha256(key.encode()).hexdigest()
    return LOCATION_CACHE_DIR / f"{digest}.json"
def load_location_from_cache(key: str):
    path = location_cache_path(key)

    if not path.exists():
        return None

    try:
        with open(path, "r") as f:
            cached = json.load(f)

        ts = datetime.fromisoformat(cached["timestamp"])

        if datetime.now() - ts > LOCATION_TTL:
            return None

        return cached["data"]

    except Exception:
        return None
def save_location_to_cache(key: str, data: dict):
    path = location_cache_path(key)

    payload = {
        "timestamp": datetime.now().isoformat(),
        "data": data
    }

    try:
        with open(path, "w") as f:
            json.dump(payload, f)
        return True
    except Exception:
        return False
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
        dest="log_max_mb",
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
        dest="warning_temp",
        type=float,
        help="Warning threshold for temperature (°C or °F depending on --units)",
    )
    weather.add_argument(
        "--critical-temp",
        dest="critical_temp",
        type=float,
        help="Critical threshold for temperature (°C or °F depending on --units)",
    )
    weather.add_argument(
        "--warning-wind",
        dest="warning_wind",
        type=float,
        help="Warning threshold for wind speed (kph or mph depending on --units)",
    )
    weather.add_argument(
        "--critical-wind",
        dest="critical_wind",
        type=float,
        help="Critical threshold for wind speed (kph or mph depending on --units)",
    )
    weather.add_argument(
        "--warning-gust",
        dest="warning_gust",
        type=float,
        help="Warning threshold for wind gust speed (kph or mph depending on --units)",
    )
    weather.add_argument(
        "--critical-gust",
        dest="critical_gust",
        type=float,
        help="Critical threshold for wind gust speed (kph or mph depending on --units)",
    )
    weather.add_argument(
        "--warning-humidity",
        dest="warning_humidity",
        type=float,
        help="Warning threshold for humidity (%%)",
    )
    weather.add_argument(
        "--critical-humidity",
        dest="critical_humidity",
        type=float,
        help="Critical threshold for humidity (%%)",
    )
    weather.add_argument(
        "--warning-precip",
        dest="warning_precip",
        type=float,
        help="Warning threshold for precipitation (mm or inches depending on --units)",
    )
    weather.add_argument(
        "--critical-precip",
        dest="critical_precip",
        type=float,
        help="Critical threshold for precipitation (mm or inches depending on --units)",
    )
    weather.add_argument(
        "--warning-cloud",
        dest="warning_cloud",
        type=float,
        help="Warning threshold for cloud cover (%%)",
    )
    weather.add_argument(
        "--critical-cloud",
        dest="critical_cloud",
        type=float,
        help="Critical threshold for cloud cover (%%)",
    )
    # Inclusion Options
    include = parser.add_argument_group("Inclusion Options")
    include.add_argument(
        "--include-gusts",
        dest="include_gusts",
        action="store_true",
        help="Include wind gusts in output and perfdata even if no thresholds are set."
    )
    include.add_argument(
        "--include-precip",
        dest="include_precip",
        action="store_true",
        help="Include precipitation fields in output and perfdata."
    )
    include.add_argument(
        "--include-clouds",
        dest="include_clouds",
        action="store_true",
        help="Include cloud cover fields in output and perfdata."
    )

    # Debug
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
        dest="show_location_details",
        help="Show resolved location details and provider URL for debugging",
    )
    debug.add_argument("--show-codes", action="store_true",
                        help="Show numeric condition codes in verbose mode")
    debug.add_argument("--no-color", action="store_true",
                        help="Disable ANSI color output in verbose mode")
    debug.add_argument("--force-cache", dest="force_cache", action="store_true",
                        help="Force reading from cache even if API is available")
    debug.add_argument("--ignore-cache", action="store_true", dest="ignore_cache",
                        help="ignore reading from cache even if API is unavailable")
    debug.add_argument("--ignore-ttl", action="store_true", dest="ignore_ttl",
                        help="ignore the TTL reading in the cache even if API is available")
    debug.add_argument("--cache-info", action="store_true", dest="cache_info",
                        help="Display the cache info")

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
    # NEW: Normalize key for cache
    # ------------------------------------------------------------
    cache_key = f"{country}:{original.lower().strip()}"

    # ------------------------------------------------------------
    # NEW: Check cache before doing anything
    # ------------------------------------------------------------
    cached = load_location_from_cache(cache_key)
    if cached:
        return cached

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
            result = make_location("direct", lat, lon)

            # NEW: Write to cache
            save_location_to_cache(cache_key, result)
            return result

        except ValueError:
            pass  # Not lat/long → fall through

    # ------------------------------------------------------------
    # Case 2: Postal code (digits only)
    # ------------------------------------------------------------
    if original.isdigit():
        zip_url = f"https://api.zippopotam.us/{country}/{original}"
        r = requests.get(zip_url, timeout=timeout)

        if r.status_code == 200:
            z = r.json()
            place = z["places"][0]
            result = make_location(
                provider="zippopotam.us",
                lat=float(place["latitude"]),
                lon=float(place["longitude"]),
                city=place["place name"],
                state=place.get("state"),
                zip_code=original
            )
            result["url"] = zip_url

            # NEW: Write to cache
            save_location_to_cache(cache_key, result)
            return result

    # ------------------------------------------------------------
    # Case 3: City name (strip state if present)
    # ------------------------------------------------------------
    parts = [p.strip() for p in original.split(",")]
    city = normalize_city_name(parts[0])

    # Expand US state abbreviations → full names
    state_filter = None
    if len(parts) >= 2:
        raw_state = parts[1].strip()
        upper_state = raw_state.upper()
        state_filter = US_STATES.get(upper_state, raw_state)

    # ------------------------------------------------------------
    # 1. First try: global search
    # ------------------------------------------------------------
    geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}"
    r = requests.get(geo_url, timeout=timeout)

    if r.status_code == 200:
        data = r.json()
        results = data.get("results", [])

        if state_filter:
            filtered = [
                r for r in results
                if r.get("admin1", "").upper().startswith(state_filter.upper())
            ]
            if filtered:
                entry = filtered[0]
                result = make_location(
                    provider="open-meteo",
                    lat=entry["latitude"],
                    lon=entry["longitude"],
                    city=entry.get("name"),
                    state=entry.get("admin1"),
                    zip_code=None
                )
                result["url"] = geo_url

                # NEW: Write to cache
                save_location_to_cache(cache_key, result)
                return result

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
            result = make_location(
                provider="open-meteo",
                lat=entry["latitude"],
                lon=entry["longitude"],
                city=entry.get("name"),
                state=entry.get("admin1"),
                zip_code=None
            )
            result["url"] = geo_url

            # NEW: Write to cache
            save_location_to_cache(cache_key, result)
            return result

    # ------------------------------------------------------------
    # Final fallback: Zippopotam.us city lookup
    # ------------------------------------------------------------
    city_url = f"https://api.zippopotam.us/{country}/{city}"
    r = requests.get(city_url, timeout=timeout)

    if r.status_code == 200:
        z = r.json()
        place = z["places"][0]
        result = make_location(
            provider="zippopotam.us",
            lat=float(place["latitude"]),
            lon=float(place["longitude"]),
            city=place["place name"],
            state=place.get("state"),
            zip_code=z.get("post code")
        )
        result["url"] = city_url

        # NEW: Write to cache
        save_location_to_cache(cache_key, result)
        return result

    # ------------------------------------------------------------
    # Nothing worked
    # ------------------------------------------------------------
    raise RuntimeError(f"City not found: {original}")
def validate_location_input(location: str, country: str):
    """
    Validates location input in a globally safe, deterministic way.

    Rules:
      - US ZIP codes must be numeric (5-digit or ZIP+4).
      - Non-US postal codes may be alphanumeric.
      - US city lookups require a state (City, ST).
      - Non-US city lookups may omit region.
    """

    loc = location.strip()
    ctry = (country or "").strip().upper()

    # -------------------------
    # 1. Detect US ZIP codes
    # -------------------------
    if ctry == "US":
        # Valid US ZIP (5-digit) or ZIP+4
        if re.fullmatch(r"\d{5}(-\d{4})?", loc):
            return True  # valid US ZIP
        # Otherwise treat as city/state and validate below

    # -------------------------
    # 2. Detect non-US postal codes
    # -------------------------
    # Postal codes outside the US are usually a single token with no commas.
    if ctry != "US" and "," not in loc:
        # Accept any alphanumeric postal code
        # (e.g., "K1A 0B1", "SW1A 1AA", "1012 WX")
        return True

    # -------------------------
    # 3. City/state parsing
    # -------------------------
    parts = [p.strip() for p in loc.split(",")]

    # US-specific rule: city-only is invalid
    if ctry == "US":
        if len(parts) == 1:
            raise ValueError(
                "U.S. city lookups require a state abbreviation "
                "(e.g., 'Wichita, KS')."
            )

        if len(parts) == 2:
            city = parts[0].strip()
            state = parts[1].strip()

            # Normalize city (St → Saint)
            city = normalize_city_name(city)

            # Normalize state
            state_upper = state.upper()
            state_lower = state.lower()

            # 1. Check if it's a valid 2-letter code (case-insensitive)
            if state_upper in US_STATES:
                return True # valid

            # 2. Check if it's a full state name
            STATE_NAME_TO_CODE = {v.lower(): k for k, v in US_STATES.items()}
            if state_lower in STATE_NAME_TO_CODE:
                return True # valid

            raise ValueError(
                f"Invalid U.S. state '{state}'. Expected a 2-letter code "
                "or full state name (e.g., 'KS' or 'Kansas')."
            )

        raise ValueError(
            "Invalid U.S. location format. Expected 'City, ST' or a ZIP code."
        )

    # -------------------------
    # 4. Non-US city lookups
    # -------------------------
    # Allow city-only or city+region
    return True
def normalize_city_name(city: str) -> str:
    city = city.strip()
    # Replace "St" or "St." at the beginning with "Saint"
    if city.lower().startswith("st "):
        return "Saint " + city[3:].strip()
    if city.lower().startswith("st. "):
        return "Saint " + city[4:].strip()
    return city
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
            "apparent_temperature",
            "dewpoint_2m",
            "relativehumidity_2m",
            "pressure_msl",
            "visibility",
            "precipitation",
            "precipitation_probability",
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
    if current_time and times:
        ct = parse_iso(current_time)
        hourly_dt = [parse_iso(t) for t in times]
        idx = min(range(len(hourly_dt)), key=lambda i: abs(hourly_dt[i] - ct))
    else:
        idx = 0
    
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
        "apparent_temperature_c": h("apparent_temperature"),
        "dewpoint_c": h("dewpoint_2m"),
        "visibility_m": h("visibility"),
        "pressure_msl": h("pressure_msl"),
        "precipitation_probability": h("precipitation_probability"),
    }
    return result, url
def fetch_weather(lat: float, lon: float, timeout: int, provider: str,
                  units: str, force_cache: bool) -> Tuple[Dict[str, Any], Optional[str], str, Optional[float], bool]:

    # Build deterministic cache key
    cache_id = f"{lat},{lon}:{units}:{provider}"

    # Try cache first
    cached, cached_ts = load_cache(cache_id)
    cache_age = None
    if cached_ts:
        cache_age = (datetime.now() - cached_ts).total_seconds()

    # Forced cache mode
    if force_cache:
        if cached is None:
            raise RuntimeError("Forced cache read but no cache exists")
        return cached, None, "cache-forced", cache_age, False

    # Try live provider
    live = None
    url = None
    try:
        if provider == "open-meteo":
            live, url = fetch_weather_open_meteo(lat, lon, timeout)
        else:
            raise ValueError(f"Unsupported provider: {provider}")
    except Exception:
        live = None

    # Live success → convert + save cache
    if live:
        data = convert_units(live, units)
        save_cache(cache_id, data)
        return data, url, "live", 0, True

    # Live failed → fallback to cache
    if cached:
        data = convert_units(cached, units)
        return data, None, "cache", cache_age, False

    # No live + no cache → fail
    raise RuntimeError("Weather API unreachable and no cached data")
def parse_iso(ts: str) -> datetime:
    return datetime.strptime(ts, "%Y-%m-%dT%H:%M")# ---------------------------------------------------------------------------
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
def format_age(seconds: float) -> str:
    if seconds is None:
        return "unknown"
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h}h {m}m {s}s"
    elif m > 0:
        return f"{m}m {s}s"
    else:
        return f"{s}s"
def build_normal_message(data: Dict[str, Any], args: argparse.Namespace) -> str:
    if args.units == "imperial":
        t = data.get("temperature_f")
        w = data.get("wind_mph")
        return f"Weather normal: {t:.2f}°F, {w:.2f} mph"
    else:
        t = data.get("temperature_c")
        w = data.get("wind_kph")
        return f"Weather normal: {t:.2f}°C, {w:.2f} kph"
def output_and_exit(status: int, payload: Dict[str, Any], args: argparse.Namespace, flags: Flags ) -> None:
    if flags[FlagNames.JSON]:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    elif flags[FlagNames.VERBOSE]:
        verbose_output(payload, args, flags)
    elif not flags[FlagNames.QUIET]:
        perf = build_perfdata(payload["data"], args, flags)
        print(f"{payload['status']}: {payload['message']} | {perf}")
    sys.exit(status)
def verbose_output(payload: Dict[str, Any], args: argparse.Namespace, flags: Flags) -> None:
    d = payload["data"]

    # ---------------------------------------------------------
    # LOCATION DETAILS (debug flag)
    # ---------------------------------------------------------
    if flags[FlagNames.SHOW_LOCATION_DETAILS] and "resolved_location" in payload:
        print("Location Resolution Details:")
        rl = payload["resolved_location"]
        print(f"  Input: {rl['input']}")
        print(f"  Location Provider: {rl['location_provider']}")
        print(f"  Location Provider URL: {rl['location_provider_url']}")
        print(f"  Weather Provider: {rl['weather_provider']}")
        print(f"  Weather Provider URL: {rl['weather_provider_url']}")
        print(f"  Resolved Name: {rl['city']}, {rl['state']}, {rl['country']}")
        print(f"  Latitude: {rl['latitude']}")
        print(f"  Longitude: {rl['longitude']}")
        print(f"  Weather API URL: {rl['weather_url']}")

    # ---------------------------------------------------------
    # CORE STATUS BLOCK
    # ---------------------------------------------------------
    print(f"Status: {payload['status']}")
    print(f"Message: {payload['message']}")
    print(f"Location: {payload['location']}")

    # ---------------------------------------------------------
    # TEMPERATURE
    # ---------------------------------------------------------
    tf = d.get("temperature_f")
    tc = d.get("temperature_c")
    if tf is not None and tc is not None:
        print(f"Temperature: {tf:.2f}°F ({tc:.2f}°C)")
    elif tf is not None:
        print(f"Temperature: {tf:.2f}°F")
    elif tc is not None:
        print(f"Temperature: {tc:.2f}°C")

    # ---------------------------------------------------------
    # WIND SPEED
    # ---------------------------------------------------------
    wm = d.get("wind_mph")
    wk = d.get("wind_kph")
    if wm is not None and wk is not None:
        print(f"Wind Speed: {wm:.2f} mph ({wk:.2f} kph)")
    elif wm is not None:
        print(f"Wind Speed: {wm:.2f} mph")
    elif wk is not None:
        print(f"Wind Speed: {wk:.2f} kph")

    # ---------------------------------------------------------
    # WIND GUSTS (optional)
    # ---------------------------------------------------------
    if flags[FlagNames.INCLUDE_GUSTS]:
        gm = d.get("wind_gust_mph")
        gk = d.get("wind_gust_kph")
        if gm is not None and gk is not None:
            print(f"Wind Gust: {gm:.2f} mph ({gk:.2f} kph)")
        elif gm is not None:
            print(f"Wind Gust: {gm:.2f} mph")
        elif gk is not None:
            print(f"Wind Gust: {gk:.2f} kph")

    # ---------------------------------------------------------
    # HUMIDITY (always included)
    # ---------------------------------------------------------
    if d.get("humidity") is not None:
        print(f"Humidity: {d['humidity']:.2f}%")

    # ---------------------------------------------------------
    # PRECIPITATION (optional)
    # ---------------------------------------------------------
    if flags[FlagNames.INCLUDE_PRECIP]:
        pm = d.get("precip_mm")
        pi = d.get("precip_in")
        if pm is not None and pi is not None:
            print(f"Precipitation: {pm:.2f} mm ({pi:.2f} in)")
        elif pm is not None:
            print(f"Precipitation: {pm:.2f} mm")
        elif pi is not None:
            print(f"Precipitation: {pi:.2f} in")

    # ---------------------------------------------------------
    # CLOUD COVER (optional)
    # ---------------------------------------------------------
    if flags[FlagNames.INCLUDE_CLOUDS]:
        cloud = d.get("cloudcover")
        if cloud is not None:
            print(f"Cloud Cover: {cloud:.2f}%")

    # ---------------------------------------------------------
    # CONDITION (with color + optional code)
    # ---------------------------------------------------------
    condition = d.get("condition_text", "Unknown")
    code = d.get("condition")

    # choose color based on condition
    cond_lower = condition.lower()
    if "rain" in cond_lower or "drizzle" in cond_lower:
        cond_color = Color.YELLOW
    elif "storm" in cond_lower:
        cond_color = Color.RED
    elif "clear" in cond_lower:
        cond_color = Color.GREEN
    elif "cloud" in cond_lower:
        cond_color = Color.GRAY
    else:
        cond_color = Color.CYAN

    cond_display = condition
    if flags[FlagNames.SHOW_CODES]:
        cond_display = f"{condition} ({code})"

    print("Condition:",
          colorize(cond_display, cond_color, not flags[FlagNames.NO_COLOR]))

    # ---------------------------------------------------------
    # SOURCE + CACHE INFO
    # ---------------------------------------------------------
    source = d.get("source")
    cache_age = d.get("cache_age")

    print(f"Source: {source}")
    if source in ["cache", "forced cache"]:
        print(f"Source: Cache (age: {cache_age})")

    # ---------------------------------------------------------
    # RUNTIME
    # ---------------------------------------------------------
    print(f"Runtime: {payload['runtime_ms']} ms")
def convert_units(data: Dict[str, Any], units: str) -> Dict[str, Any]:
    out = dict(data)

    # Temperature C → F
    if out.get("temperature_c") is not None:
        out["temperature_f"] = round(out["temperature_c"] * 9/5 + 32, 2)

    if out.get("apparent_temperature_c") is not None:
        out["apparent_temperature_f"] = round(out["apparent_temperature_c"] * 9/5 + 32, 2)

    if out.get("dewpoint_c") is not None:
        out["dewpoint_f"] = round(out["dewpoint_c"] * 9/5 + 32, 2)

    # Wind kph → mph
    if out.get("wind_kph") is not None:
        out["wind_mph"] = round(out["wind_kph"] * 0.621371, 2)

    if out.get("wind_gust_kph") is not None:
        out["wind_gust_mph"] = round(out["wind_gust_kph"] * 0.621371, 2)

    # Precip mm → inches
    if out.get("precip_mm") is not None:
        out["precip_in"] = round(out["precip_mm"] / 25.4, 2)

    # Visibility meters → miles
    if out.get("visibility_m") is not None:
        out["visibility_km"] = round(out["visibility_m"] / 1000, 2)
        out["visibility_mi"] = round(out["visibility_m"] / 1609.344, 2)

    # Pressure hPa → inHg
    if out.get("pressure_msl") is not None:
        out["pressure_inhg"] = round(out["pressure_msl"] * 0.0295299830714, 3)

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
def build_perfdata(data: Dict[str, Any], args: argparse.Namespace, flags: Flags) -> str:
    parts = []

    # -----------------------------
    # Unit selection
    # -----------------------------
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
    cloud = data.get("cloudcover")

    # -----------------------------
    # Temperature (always included)
    # -----------------------------
    if temp is not None:
        w = args.warning_temp or ""
        c = args.critical_temp or ""
        parts.append(f"temp={temp:.2f};{w};{c}")

    # -----------------------------
    # Wind (always included)
    # -----------------------------
    if wind is not None:
        w = args.warning_wind or ""
        c = args.critical_wind or ""
        parts.append(f"wind={wind:.2f};{w};{c}")

    # -----------------------------
    # Gusts (only if operator requested)
    # -----------------------------
    if flags[FlagNames.INCLUDE_GUSTS] and gust is not None:
        w = args.warning_gust or ""
        c = args.critical_gust or ""
        parts.append(f"gust={gust:.2f};{w};{c}")

    # -----------------------------
    # Humidity (always included)
    # -----------------------------
    if humidity is not None:
        w = args.warning_humidity or ""
        c = args.critical_humidity or ""
        parts.append(f"humidity={humidity:.2f};{w};{c}")

    # -----------------------------
    # Precipitation (only if operator requested)
    # -----------------------------
    if flags[FlagNames.INCLUDE_PRECIP] and precip is not None:
        w = args.warning_precip or ""
        c = args.critical_precip or ""
        parts.append(f"precip={precip:.2f};{w};{c}")

    # -----------------------------
    # Cloud cover (only if operator requested)
    # -----------------------------
    if flags[FlagNames.INCLUDE_CLOUDS] and cloud is not None:
        w = args.warning_cloud or ""
        c = args.critical_cloud or ""
        parts.append(f"cloud={cloud:.2f};{w};{c}")

    return " ".join(parts)
# --------------------------------------
# Logging Functions
# --------------------------------------
def ts():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
def write_log(meta, message):
    log_dir = meta.get("log_dir")

    try:
        os.makedirs(log_dir, exist_ok=True)
        logfile = os.path.join(log_dir, f"{meta['script_name']}.log")
        with open(logfile, "a") as f:
            f.write(f"{ts()}; {message}\n")
    except Exception as e:
        if not meta.get("_log_warn_emitted"):
            meta["_log_warn_emitted"] = True
            warning = f"[WARN] Unable to write to log directory: {log_dir} — {e}"
            if meta["mode"] == "verbose":
                print(f"[WARN] {warning}")
            if "warnings" not in meta:
                meta["warnings"] = []
            meta["warnings"].append(warning)
def rotate_log_if_needed(meta):
    """
    Deterministic log rotation for check_cert.
    Assumes caller has already checked logging_enabled.
    Uses meta['log_max_mb'] as the rotation threshold.
    """

    log_dir = meta["log_dir"]
    logfile = os.path.join(log_dir, f"{meta['script_name']}.log")

    if not os.path.exists(logfile):
        return

    # Rotation threshold (default 50 MB)
    max_mb = meta.get("log_max_mb", 50)
    max_bytes = max_mb * 1024 * 1024

    try:
        if os.path.getsize(logfile) < max_bytes:
            return

        # Build archive path
        archive_path = build_archive_path(meta)

        # Atomic move
        shutil.move(logfile, archive_path)

        # Compress archive
        compress_file(archive_path)

        # Write rotation notice to new log
        with open(logfile, "w", encoding="utf-8") as f:
            f.write(f"{ts()}; [INFO] log rotated to {os.path.basename(archive_path)}.zip\n")

    except Exception as e:
        if not meta.get("_log_warn_emitted"):
            meta["_log_warn_emitted"] = True

            warn = f"[WARN] Unable to rotate log file '{logfile}': {e}"

            if meta.get("mode") == "verbose":
                print(warn)

            meta.setdefault("warnings", []).append(warn)
def build_archive_path(meta):
    base = meta["script_name"]
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return os.path.join(meta["log_dir"], f"{base}_{ts}.log")
def compress_file(path):
    zip_path = path + ".zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(path, os.path.basename(path))
    os.remove(path)
def start_banner_weather(meta):
    return (
        f"[START] {meta['script_name']}.py"
        f" location={meta['location_input']}"
        f" country={meta['country']}"
        f" provider={meta['provider']}"
        f" units={meta['units']}"
        f" ignore_cache={meta['ignore_cache']}"
        f" ignore_ttl={meta['ignore_ttl']}"
        f" force_cache={meta['force_cache']}"
        f" include_gusts={meta['include_gusts']}"
        f" include_precip={meta['include_precip']}"
        f" include_clouds={meta['include_clouds']}"
    )
def log_weather_data(weather):
    fields = []
    for k, v in weather.items():
        fields.append(f"{k}={v}")
    return "[WEATHER] " + " ".join(fields)
def log_summary_weather(state, message):
    return f"[RESULT] state={state} message=\"{message}\""
def end_banner():
    return "[END]"

# -----------------------------
# Main
# -----------------------------
def main() -> None:
    args = build_parser()
    if args.version:
        print(f"check_weather.py using Python {sys.version.split()[0]}")
        sys.exit(0)
    if not validate_location_input(args.location, args.country):
        raise ValueError(f"Invalid Location Specified: {args.location}")
    
    flags = Flags.from_args(args)
    start = time.time()
    mode = "json" if flags[FlagNames.JSON] else "verbose" if flags[FlagNames.VERBOSE] else "quiet" if flags[FlagNames.QUIET] else "nagios" 
    meta = {
        "script_name": Path(sys.argv[0]).stem,
        "location_input": args.location,
        "country": args.country,
        "units": args.units,
        "provider": args.provider,
        "ignore_cache": flags[FlagNames.IGNORE_CACHE],
        "ignore_ttl": flags[FlagNames.IGNORE_TTL],
        "force_cache": flags[FlagNames.FORCE_CACHE],
        "include_gusts": flags[FlagNames.INCLUDE_GUSTS],
        "include_precip": flags[FlagNames.INCLUDE_PRECIP],
        "include_clouds": flags[FlagNames.INCLUDE_CLOUDS],
        "log_dir": str(Path(args.log_dir).expanduser()) if args.log_dir else None,
        "log_max_mb": args.log_max_mb,
        "mode": mode,
    }
    logging_enabled = mode != "nagios" and args.log_dir
    loc = resolve_location(args)
    lat = loc.get("latitude", 0)
    lon = loc.get("longitude", 0)
    if logging_enabled:
        write_log(meta, start_banner_weather(meta))
        write_log(meta, log_weather_data(loc))
    data, url, source, cache_age, cache_written = fetch_weather(
        lat, lon,
        args.timeout,
        args.provider,
        args.units,
        args.force_cache
    )

    data["source"] = "Live API" if source == "live" else source
    data["cache_written"] = cache_written
    if cache_age is not None:
        data["cache_age"] = format_age(cache_age)
    # Add human-readable condition text
    code = data.get("condition")
    if isinstance(code, int):
        data["condition_text"] = WEATHER_CODES.get(code, "Unknown")
    else:
        data["condition_text"] = "Unknown"
    status, message = evaluate_weather(data, args)
    if logging_enabled:
        write_log(meta, log_weather_data(data))
    runtime = round((time.time() - start) * 1000, 2)
    payload = {
        "status": ["OK", "WARNING", "CRITICAL", "UNKNOWN"][status],
        "message": message,
        "location": format_resolved_name(loc),
        "data": strip_none(data),
        "runtime_ms": runtime,
    }
    if flags[FlagNames.SHOW_LOCATION_DETAILS]:
        weather_url=url.split("?")[0] if url is not None else None
        payload["resolved_location"] = {
            "input": args.location,

            # Weather provider (from --provider)
            "weather_provider": args.provider,
            "weather_provider_url": weather_url,

            # Location provider (from geocoding)
            "location_provider": loc.get("provider"),
            "location_provider_url": loc.get("url"),

            # Resolved location metadata
            "city": loc.get("city"),
            "state": loc.get("state"),
            "zip": loc.get("zip"),
            "country": args.country,
            "latitude": loc.get("latitude"),
            "longitude": loc.get("longitude"),

            # Final weather API URL
            "weather_url": url,
        }
    if logging_enabled:
        write_log(meta, log_summary_weather(payload.get("state"), payload.get("message")))
        write_log(meta,end_banner())
    output_and_exit(status, payload, args, flags)

if __name__ == "__main__":
    main()
