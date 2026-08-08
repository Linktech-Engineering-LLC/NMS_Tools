#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Leon McClatchey, Linktech Engineering LLC
"""
File: check_weather.py
Author: Leon McClatchey
Company: Linktech Engineering LLC
Created: 2026-04-07
Last Modified: 2026-04-27
Required: Python 3.8+
Part of: NMS_Tools Monitoring Suite
License: MIT (see LICENSE for details)

Description: 
    Deterministic weather checker with ZIP/city/lat-long support.
"""

import argparse
import json
import os
import requests
import sys
import time
import urllib.parse
import urllib.request

from datetime import datetime, timedelta, date
from enum import IntEnum, auto
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, List

from PythonTools.cache import (
    ensure_subdir,
    cache_path,
    load_json_cache,
    save_json_cache,
    serialize_for_json,
)
from PythonTools.color import Color,colorize
from PythonTools.datetime import (
    parse_iso, 
    format_age,
    get_timezone,
    ensure_dt,
    compute_sun_times,
)
from PythonTools.location import (
    US_STATES,
    normalize_city_name,
    validate_location_input,
    PROVIDERS,
)
from PythonTools.log_helpers.factory import LoggerFactory
from PythonTools.nagios import (
    OK,
    WARNING,
    CRITICAL,
    UNKNOWN,
    FlagNames,
    Flags,
    BaseNagiosParser,
    should_output,
    nagios_summary,
)
from PythonTools.units import (
    convert_temperature, 
    convert_speed, 
    convert_pressure,
    convert_distance,
)
from PythonTools.utils import strip_none

# Root of the suite (two levels up from the tool script)
SUITE_ROOT = Path(__file__).resolve().parent.parent

def load_version() -> str:
    """
    Load the suite VERSION file if present.
    If missing, return a fallback string indicating external execution.
    """
    version_file = SUITE_ROOT / "VERSION"

    try:
        return version_file.read_text(encoding="utf-8").strip()
    except Exception:
        return "External to NMS_TOOLS Suite"

VERSION = load_version()
MIN_MAJOR = 3
MIN_MINOR = 8
# Other Global Constants
SCRIPT_VERSION = "2.2.0"
SCRIPT_NAME = Path(sys.argv[0]).stem
# Weather Constants
DEFAULT_PROVIDER = "nws"
WEATHER_CODES = {
    0: {
        "canonical": "Clear sky",
        "contexts": [
            "Clear sky", "Clear", "Sunny", "Mostly Sunny"
        ],
        "day_icon": "wi-day-sunny.svg",
        "night_icon": "wi-night-clear.svg",
    },

    1: {
        "canonical": "Mainly clear",
        "contexts": [
            "Mainly clear", "Mostly Clear"
        ],
        "day_icon": "wi-day-sunny.svg",
        "night_icon": "wi-night-clear.svg",
    },

    2: {
        "canonical": "Partly cloudy",
        "contexts": [
            "Partly Cloudy", "Partly Sunny"
        ],
        "day_icon": "wi-day-cloudy.svg",
        "night_icon": "wi-night-alt-partly-cloudy.svg",
    },

    3: {
        "canonical": "Overcast",
        "contexts": [
            "Overcast",
            "Cloudy",
            "Mostly Cloudy",
            "Cloudy and breezy",
            "Cloudy and windy",
            "Increasing clouds",
            "Decreasing clouds",
            "Cloudy then clearing",
            "Cloudy then becoming partly cloudy",
        ],
        "day_icon": "wi-cloudy.svg",
        "night_icon": "wi-night-cloudy.svg",
    },

    45: {
        "canonical": "Fog",
        "contexts": [
            "Fog", "Patchy Fog", "Depositing rime fog"
        ],
        "day_icon": "wi-day-fog.svg",
        "night_icon": "wi-night-fog.svg",
    },

    48: {
        "canonical": "Depositing rime fog",
        "contexts": [
            "Depositing rime fog"
        ],
        "day_icon": "wi-day-fog.svg",
        "night_icon": "wi-night-fog.svg",
    },

    51: {
        "canonical": "Light drizzle",
        "contexts": [
            "Light drizzle"
        ],
        "day_icon": "wi-day-sprinkle.svg",
        "night_icon": "wi-night-alt-sprinkle.svg",
    },

    53: {
        "canonical": "Moderate drizzle",
        "contexts": [
            "Moderate drizzle"
        ],
        "day_icon": "wi-day-sprinkle.svg",
        "night_icon": "wi-night-alt-sprinkle.svg",
    },

    55: {
        "canonical": "Dense drizzle",
        "contexts": [
            "Dense drizzle"
        ],
        "day_icon": "wi-day-rain-mix.svg",
        "night_icon": "wi-night-alt-rain-mix.svg",
    },

    56: {
        "canonical": "Freezing drizzle",
        "contexts": [
            "Freezing drizzle"
        ],
        "day_icon": "wi-day-sleet.svg",
        "night_icon": "wi-night-alt-sleet.svg",
    },

    57: {
        "canonical": "Dense freezing drizzle",
        "contexts": [
            "Freezing drizzle (dense)"
        ],
        "day_icon": "wi-day-sleet.svg",
        "night_icon": "wi-night-alt-sleet.svg",
    },

    61: {
        "canonical": "Slight rain",
        "contexts": [
            "Slight rain", "Rain", "Rain Showers", "Showers"
        ],
        "day_icon": "wi-day-rain.svg",
        "night_icon": "wi-night-alt-rain.svg",
    },

    63: {
        "canonical": "Moderate rain",
        "contexts": [
            "Moderate rain"
        ],
        "day_icon": "wi-day-rain.svg",
        "night_icon": "wi-night-alt-rain.svg",
    },

    65: {
        "canonical": "Heavy rain",
        "contexts": [
            "Heavy rain"
        ],
        "day_icon": "wi-day-rain-wind.svg",
        "night_icon": "wi-night-alt-rain-wind.svg",
    },

    66: {
        "canonical": "Freezing rain",
        "contexts": [
            "Freezing rain"
        ],
        "day_icon": "wi-day-sleet.svg",
        "night_icon": "wi-night-alt-sleet.svg",
    },

    67: {
        "canonical": "Heavy freezing rain",
        "contexts": [
            "Freezing rain (heavy)"
        ],
        "day_icon": "wi-day-sleet-storm.svg",
        "night_icon": "wi-night-alt-sleet-storm.svg",
    },

    71: {
        "canonical": "Slight snow",
        "contexts": [
            "Slight snow", "Snow", "Snow grains"
        ],
        "day_icon": "wi-day-snow.svg",
        "night_icon": "wi-night-alt-snow.svg",
    },

    73: {
        "canonical": "Moderate snow",
        "contexts": [
            "Moderate snow"
        ],
        "day_icon": "wi-day-snow.svg",
        "night_icon": "wi-night-alt-snow.svg",
    },

    75: {
        "canonical": "Heavy snow",
        "contexts": [
            "Heavy snow"
        ],
        "day_icon": "wi-day-snow-wind.svg",
        "night_icon": "wi-night-alt-snow-wind.svg",
    },

    80: {
        "canonical": "Rain showers",
        "contexts": [
            "Rain showers", "Showers"
        ],
        "day_icon": "wi-day-showers.svg",
        "night_icon": "wi-night-alt-showers.svg",
    },

    81: {
        "canonical": "Moderate rain showers",
        "contexts": [
            "Rain showers (moderate)"
        ],
        "day_icon": "wi-day-showers.svg",
        "night_icon": "wi-night-alt-showers.svg",
    },

    82: {
        "canonical": "Violent rain showers",
        "contexts": [
            "Rain showers (violent)"
        ],
        "day_icon": "wi-day-storm-showers.svg",
        "night_icon": "wi-night-alt-storm-showers.svg",
    },

    85: {
        "canonical": "Slight snow showers",
        "contexts": [
            "Snow showers"
        ],
        "day_icon": "wi-day-snow.svg",
        "night_icon": "wi-night-alt-snow.svg",
    },

    86: {
        "canonical": "Heavy snow showers",
        "contexts": [
            "Snow showers (heavy)"
        ],
        "day_icon": "wi-day-snow-wind.svg",
        "night_icon": "wi-night-alt-snow-wind.svg",
    },

    95: {
        "canonical": "Thunderstorm",
        "contexts": [
            "Thunderstorm", "Thunderstorms", 
        ],
        "day_icon": "wi-day-thunderstorm.svg",
        "night_icon": "wi-night-alt-thunderstorm.svg",
    },

    96: {
        "canonical": "Thunderstorm with hail",
        "contexts": [
            "Thunderstorm with hail"
        ],
        "day_icon": "wi-day-hail.svg",
        "night_icon": "wi-night-alt-hail.svg",
    },

    99: {
        "canonical": "Thunderstorm with heavy hail",
        "contexts": [
            "Thunderstorm with heavy hail"
        ],
        "day_icon": "wi-day-hail.svg",
        "night_icon": "wi-night-alt-hail.svg",
    },
}
VALID_WMO_CODES = set(WEATHER_CODES.keys())
DEFAULT_WEATHER_ICON = "wi-na.svg"

def validate_weather_code(code: Any) -> bool:
    """Return True if code is a valid WMO weather code."""
    return isinstance(code, int) and code in VALID_WMO_CODES
def nws_text_to_wmo(text: str | None) -> int | None:
    if not text:
        return None

    norm = normalize_nws_text(text)  # e.g., "Slight Chance Showers And Thunderstorms"

    best_code = None

    for code, info in WEATHER_CODES.items():
        for ctx in info["contexts"]:
            # substring match, case-insensitive
            if ctx.lower() in norm.lower():
                # choose the highest-impact code
                if best_code is None or code > best_code:
                    best_code = code

    return best_code
def normalize_nws_text(text: str | None) -> str:
    if not text:
        return ""

    # Lowercase
    t = text.lower()

    # Remove punctuation
    for ch in ",.;:-":
        t = t.replace(ch, "")

    # Collapse multiple spaces
    t = " ".join(t.split())

    # Title-case to match WEATHER_CODES contexts
    return t.title()

# Flag Classes
class WeatherFlagNames(IntEnum):
    INCLUDE_GUSTS = auto()
    INCLUDE_PRECIP = auto()
    INCLUDE_CLOUDS = auto()
    WEEKLY = auto()
    HOURLY = auto()

    IGNORE_CACHE = auto()
    IGNORE_TTL = auto()
    CACHE_INFO = auto()
    FORCE_CACHE = auto()

    SHOW_LOCATION_DETAILS = auto()
    SHOW_CODES = auto()
    NO_COLOR = auto()
class WeatherFlags(Flags):

    @classmethod
    def from_args(cls, args):
        f = cls()

        # Weather flags
        f.set(WeatherFlagNames.INCLUDE_GUSTS, args.include_gusts)
        f.set(WeatherFlagNames.INCLUDE_PRECIP, args.include_precip)
        f.set(WeatherFlagNames.INCLUDE_CLOUDS, args.include_clouds)
        f.set(WeatherFlagNames.WEEKLY, args.weekly)
        f.set(WeatherFlagNames.HOURLY, args.hourly)

        # Cache flags
        f.set(WeatherFlagNames.IGNORE_CACHE, args.ignore_cache)
        f.set(WeatherFlagNames.IGNORE_TTL, args.ignore_ttl)
        f.set(WeatherFlagNames.CACHE_INFO, args.cache_info)
        f.set(WeatherFlagNames.FORCE_CACHE, args.force_cache)

        # Debug flags
        f.set(WeatherFlagNames.SHOW_LOCATION_DETAILS, args.show_location_details)
        f.set(WeatherFlagNames.SHOW_CODES, args.show_codes)
        f.set(WeatherFlagNames.NO_COLOR, args.no_color)

        return f
# ------------------------------------------------------------
# Cache Directories + TTLs
# ------------------------------------------------------------
WEATHER_CACHE_DIR = ensure_subdir("weather")
LOCATION_CACHE_DIR = ensure_subdir("location")
CACHE_TTL = timedelta(minutes=15)       # Weather TTL
LOCATION_TTL = timedelta(hours=24)      # Location TTL
# ------------------------------------------------------------
# Weather Cache Functions
# ------------------------------------------------------------
def weather_cache_path(key): return cache_path(WEATHER_CACHE_DIR, key)
def load_weather_cache(key): return load_json_cache(weather_cache_path(key), CACHE_TTL)
def save_weather_cache(key, data): return save_json_cache(weather_cache_path(key), data)
# ------------------------------------------------------------
# Location Cache Functions
# ------------------------------------------------------------
def location_cache_path(key: str) -> Path:
    return cache_path(LOCATION_CACHE_DIR, key)
def load_location_from_cache(key: str):
    return load_json_cache(location_cache_path(key), LOCATION_TTL)[0]
def save_location_to_cache(key: str, data: dict):
    return save_json_cache(location_cache_path(key), data)# -----------------------------
# Parsers
# -----------------------------
def build_parser():
    nag = BaseNagiosParser(
        prog=SCRIPT_NAME,
        description=(
            "Deterministic weather checker using pluggable providers (Open-Meteo, NOAA/NWS) "
            "Nagios‑compatible output and optional JSON diagnostics.\n\n"
            "Supports verbose, JSON, and Nagios output."
        ),
        script_version=SCRIPT_VERSION,
        suite_version=VERSION,
    )

    # Usage line
    nag.parser.usage = (
        "%(prog)s (--zip <code> | --city <name> | --lat <lat> --lon <lon>) [options]"
    )

    # ------------------------------------------------------------
    # Core Options
    # ------------------------------------------------------------
    core = nag.add_group("Core Options")
    core.add_argument(
        "-l", "--location",
        help="Free-form location: ZIP, City/State, or lat,lon",
    )
    core.add_argument(
        "--zip",
        help="ZIP code (e.g., 67576)",
    )
    core.add_argument(
        "--city",
        help='City name (e.g., "St John, KS")',
    )
    core.add_argument(
        "--lat",
        type=float,
        help="Latitude",
    )
    core.add_argument(
        "--lon",
        type=float,
        help="Longitude",
    )
    core.add_argument(
        "--country",
        default="US",
        help="Country code for location resolution",
    )
    core.add_argument(
        "--units",
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
        "--provider",
        choices=["open-meteo", "nws"],
        default=DEFAULT_PROVIDER,
        help="Weather provider to use"
    )
    # ------------------------------------------------------------
    # Nagios Behavior Filters (required by PythonTools)
    # ------------------------------------------------------------
    filt = nag.add_group("Nagios Behavior Filters")
    filt.add_argument(
        "--require-all",
        action="store_true",
        help="Require all checks to pass; if any fail, return CRITICAL.",
    )
    filt.add_argument(
        "--require-any",
        action="store_true",
        help="Require at least one check to pass; if all fail, return CRITICAL.",
    )
    filt.add_argument(
        "--fail-only",
        action="store_true",
        help="Only report failed conditions in verbose or JSON output.",
    )
    include = nag.add_group("Inclusion Options")
    include.add_argument("--include-gusts", action="store_true",
                        help="Include wind gusts in output and perfdata.")
    include.add_argument("--include-precip", action="store_true",
                        help="Include precipitation fields in output and perfdata.")
    include.add_argument("--include-clouds", action="store_true",
                        help="Include cloud cover fields in output and perfdata.")
    modes = nag.add_group("Weather Modes")
    modes.add_argument("--weekly", action="store_true",
                    help="Show weekly forecast.")
    modes.add_argument("--hourly", action="store_true",
                    help="Show hourly forecast.")
    debug = nag.add_group("Debug Options")
    debug.add_argument("--ignore-cache", action="store_true")
    debug.add_argument("--ignore-ttl", action="store_true")
    debug.add_argument("--cache-info", action="store_true")
    debug.add_argument("--force-cache", action="store_true")
    debug.add_argument("--show-location-details", action="store_true")
    debug.add_argument("--show-codes", action="store_true")
    debug.add_argument("--no-color", action="store_true")

    # ------------------------------------------------------------
    # Weather Thresholds
    # ------------------------------------------------------------
    thr = nag.add_group("Weather Thresholds")
    thr.add_argument("--warning-temp", type=float, help="Warning threshold for temperature")
    thr.add_argument("--critical-temp", type=float, help="Critical threshold for temperature")
    thr.add_argument("--warning-wind", type=float, help="Warning threshold for wind speed")
    thr.add_argument("--critical-wind", type=float, help="Critical threshold for wind speed")
    thr.add_argument("--warning-gust", type=float, help="Warning threshold for wind gust speed")
    thr.add_argument("--critical-gust", type=float, help="Critical threshold for wind gust speed")
    thr.add_argument("--warning-humidity", type=float, help="Warning threshold for humidity (rate)")
    thr.add_argument("--critical-humidity", type=float, help="Critical threshold for humidity (rate)")
    thr.add_argument("--warning-precip", type=float, help="Warning threshold for precipitation")
    thr.add_argument("--critical-precip", type=float, help="Critical threshold for precipitation")
    thr.add_argument("--warning-cloud", type=float, help="Warning threshold for cloud cover (rate)")
    thr.add_argument("--critical-cloud", type=float, help="Critical threshold for cloud cover (rate)")

    nag.parser.epilog = (
        "Examples:\n"
        "  %(prog)s --zip 67576 -v\n"
        "  %(prog)s --city \"St John, KS\" --json\n"
        "  %(prog)s --lat 38.00 --lon -98.76 --warning-temp 30\n"
    )

    # Parse using BaseNagiosParser
    args, flags, mode = nag.parse()

    # ------------------------------------------------------------
    # Required Location Validation
    # ------------------------------------------------------------
    count = 0
    if args.location:
        count += 1
    if args.zip:
        count += 1
    if args.city:
        count += 1
    if args.lat and args.lon:
        count += 1

    if count != 1:
        nag.exit_unknown("Specify exactly one of --location, --zip, --city, or --lat/--lon")
    if args.zip:
        args.location = args.zip
    elif args.city:
        args.location = args.city
    elif args.lat and args.lon:
        args.location = f"{args.lat},{args.lon}"

    return args, flags, mode
def parse_nws_speed(value):
    """
    Extract the first numeric speed from NWS strings.
    Examples:
        "5 mph" → 5
        "10 to 20 mph" → 10
        "Calm" → None
        "Light and variable" → None
    """
    if not value:
        return None

    parts = value.split()
    try:
        return float(parts[0])
    except Exception:
        return None
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
# -------------------------------------
# Weather fetch and helpers
# -------------------------------------
def build_open_meteo_url(lat: float, lon: float, mode: str) -> str:
    base = PROVIDERS["open-meteo"]["url"]

    match mode:
        case "current":
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
                "daily": "sunrise,sunset",
                "timezone": "auto",
            }

        case "hourly":
            params = {
                "latitude": lat,
                "longitude": lon,
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
                "daily": ",".join(["sunrise,sunset",]),   # ⭐ FIXED
                "timezone": "auto",
            }

        case "weekly":
            params = {
                "latitude": lat,
                "longitude": lon,
                "daily": ",".join([
                    "weathercode",
                    "temperature_2m_max",
                    "temperature_2m_min",
                    "precipitation_sum",
                    "precipitation_probability_max",
                    "windspeed_10m_max",
                    "sunrise",
                    "sunset",
                ]),
                "timezone": "auto",
            }

        case _:
            raise ValueError(f"Unsupported mode for Open-Meteo: {mode}")

    return f"{base}?{urllib.parse.urlencode(params)}"
def build_nws_url(lat: float, lon: float, mode: str) -> str:
    base = PROVIDERS["nws"]["url"]

    # Step 1: resolve gridpoint metadata
    point_url = f"{base}/points/{lat},{lon}"
    point_data = requests.get(point_url, timeout=5).json()
    props = point_data["properties"]

    match mode:
        case "current" | "hourly":
            # Hourly forecast (used for both current + hourly)
            return props["forecastHourly"]

        case "weekly":
            # Daily forecast (7-day periods)
            return props["forecast"]

        case _:
            raise ValueError(f"Unsupported mode for NWS: {mode}")
def fetch_hourly_open_meteo(lat, lon, timeout, meta):
    url = build_open_meteo_url(lat, lon, "hourly")

    raw = json.loads(urllib.request.urlopen(url, timeout=timeout).read())
    hourly = raw["hourly"]
    daily = raw["daily"]

    sunrise = daily["sunrise"][0]
    sunset  = daily["sunset"][0]

    result = []
    for i, t in enumerate(hourly["time"]):
        entry = {
            "time": t,
            "temperature_c": hourly["temperature_2m"][i],
            "wind_kph": hourly["windspeed_10m"][i],
            "condition": hourly["weathercode"][i],   # WMO code
            "sunrise": sunrise,
            "sunset": sunset,
        }
        result.append(entry)

    return {"hours": result}, url
def fetch_hourly_nws(lat, lon, timeout, meta):
    url = build_nws_url(lat, lon, "hourly")
    raw = requests.get(url, timeout=timeout).json()

    periods = raw["properties"]["periods"]

    result = []
    for p in periods:
        start = p.get("startTime")
        date_str = start.split("T")[0] if start else None
        date_obj = date.fromisoformat(date_str) if date_str else None
        sunrise, sunset = compute_sun_times(lat, lon, date_obj, meta["timezone"])
        wmo = nws_text_to_wmo(p["shortForecast"])   # maps text → WMO code

        entry = {
            "time": p["startTime"],
            "temperature_c": convert_temperature(p["temperature"], p["temperatureUnit"], "C"),
            "wind_kph": convert_speed(parse_nws_speed(p["windSpeed"]),"mph","kph"),
            "condition": wmo,
            "sunrise": sunrise,
            "sunset": sunset,
        }
        result.append(entry)

    return {"hours":result}, url
def fetch_current_open_meteo(lat: float, lon: float, timeout: int, meta: dict):
    url = build_open_meteo_url(lat, lon, "current")

    with urllib.request.urlopen(url, timeout=timeout) as resp:
        raw = json.loads(resp.read())

    current = raw.get("current_weather", {})
    hourly = raw.get("hourly", {})
    daily = raw.get("daily", {})

    sunrise = daily.get("sunrise", [None])[0]
    sunset  = daily.get("sunset", [None])[0]

    current_time = current.get("time")
    times = hourly.get("time", [])

    # Align current time to nearest hourly index
    idx = 0
    if current_time and times:
        ct = parse_iso(current_time)
        hourly_dt = [parse_iso(t) for t in times]
        idx = min(range(len(hourly_dt)), key=lambda i: abs(hourly_dt[i] - ct))

    def h(field, default=None):
        arr = hourly.get(field)
        if not arr or idx >= len(arr):
            return default
        return arr[idx]

    # RAW result — no normalization, no icons, no context
    result = {
        "time": current_time,
        "sunrise": sunrise,
        "sunset": sunset,
        "temperature_c": current.get("temperature", h("temperature_2m")),
        "wind_kph": current.get("windspeed", h("windspeed_10m")),
        "wind_gust_kph": h("windgusts_10m"),
        "humidity": h("relativehumidity_2m"),
        "precip_mm": h("precipitation"),
        "cloudcover": h("cloudcover"),
        "condition": current.get("weathercode", h("weathercode")),  # WMO code
        "apparent_temperature_c": h("apparent_temperature"),
        "dewpoint_c": h("dewpoint_2m"),
        "visibility_m": h("visibility"),
        "pressure_msl": h("pressure_msl"),
        "precipitation_probability": h("precipitation_probability"),
    }

    return result, url
def fetch_current_nws(lat: float, lon: float, timeout: int, meta: Dict[str, Any]):
    url = build_nws_url(lat, lon, "current")

    headers = {"User-Agent": "NMS_Tools/1.0"}
    r = requests.get(url, headers=headers, timeout=timeout)
    r.raise_for_status()

    data = r.json()
    periods = data.get("properties", {}).get("periods", [])

    if not periods:
        return None, url

    p = periods[0]

    # Compute sunrise/sunset using Astral
    start = p.get("startTime")
    date_str = start.split("T")[0] if start else None
    date_obj = date.fromisoformat(date_str) if date_str else None
    sunrise, sunset = compute_sun_times(lat, lon, date_obj, meta["timezone"])

    result = {
        "time": p.get("startTime"),
        "temperature_c": convert_temperature(p["temperature"], p["temperatureUnit"], "C"),
        "wind_kph": convert_speed(parse_nws_speed(p.get("windSpeed")),"mph","kph"),
        "condition": nws_text_to_wmo(p.get("shortForecast")),
        "sunrise": sunrise,
        "sunset": sunset,
    }

    return result, url
def fetch_weekly_open_meteo(lat: float, lon: float, timeout: int, meta: dict):
    url = build_open_meteo_url(lat, lon, "weekly")

    with urllib.request.urlopen(url, timeout=timeout) as resp:
        raw = json.loads(resp.read())

    daily = raw.get("daily", {})
    dates = daily.get("time", [])

    days = []
    for i, d in enumerate(dates[:7]):  # next 7 days

        def h(field: str, default=None):
            arr = daily.get(field)
            if not arr or i >= len(arr):
                return default
            return arr[i]

        days.append({
            "date": d,
            "sunrise": h("sunrise"),
            "sunset": h("sunset"),
            "condition": h("weathercode"),  # WMO code
            "temp_max_c": h("temperature_2m_max"),
            "temp_min_c": h("temperature_2m_min"),
            "precip_mm": h("precipitation_sum"),
            "precipitation_probability_max": h("precipitation_probability_max"),
            "wind_kph_max": h("windspeed_10m_max"),
        })

    # RAW weekly result — no normalization, no icons, no context
    return {"days": days}, url
def fetch_weekly_nws(lat: float, lon: float, timeout: int, meta: Dict[str, Any]):
    url = build_nws_url(lat, lon, "weekly")

    headers = {"User-Agent": "NMS_Tools/1.0"}
    r = requests.get(url, headers=headers, timeout=timeout)
    r.raise_for_status()

    data = r.json()
    periods = data.get("properties", {}).get("periods", [])

    normalized = []
    for p in periods:
        start = p.get("startTime")
        date_str = start.split("T")[0] if start else None
        date_obj = date.fromisoformat(date_str) if date_str else None
        sunrise, sunset = compute_sun_times(lat, lon, date_obj, meta["timezone"])
        
        normalized.append({
            "date": date_str,
            "sunrise": sunrise,
            "sunset": sunset,
            "condition": nws_text_to_wmo(p.get("shortForecast")),
            "temp_max_c": convert_temperature(p.get("temperature"), p.get("temperatureUnit"), "C"),
            "temp_min_c": convert_temperature(p.get("temperature"), p.get("temperatureUnit"), "C"),
            "precip_mm": 0.0,  # NWS weekly lacks precip
            "precipitation_probability_max": p.get("probabilityOfPrecipitation", {}).get("value"),
            "wind_kph_max": convert_speed(parse_nws_speed(p.get("windSpeed")),"mph","kph"),
        })

    return {"days": normalized}, url
def resolve_nws_meta(lat: float, lon: float) -> Dict[str, Any]:
    url = f"https://api.weather.gov/points/{lat},{lon}"
    headers = {"User-Agent": "NMS_Tools/1.0"}

    r = requests.get(url, headers=headers, timeout=10)
    r.raise_for_status()

    props = r.json().get("properties", {})

    return {
        "office": props.get("gridId"),
        "gridX": props.get("gridX"),
        "gridY": props.get("gridY")
    }
def select_icon(weather_code, sunrise, sunset, now, mapping):
    """
    Selects the correct icon (day or night) based on sunrise/sunset times.

    Parameters:
        weather_code (int): WMO weather code.
        sunrise (str): ISO timestamp for sunrise, e.g. "2026-04-27T06:28".
        sunset (str): ISO timestamp for sunset, e.g. "2026-04-27T20:12".
        now (str or datetime): Current local time.
        mapping (dict): WEATHER_CODES mapping with day_icon/night_icon.

    Returns:
        str: The icon filename to use.
    """

    # Normalize "now" to datetime
    if isinstance(now, str):
        now = datetime.fromisoformat(now)

    sunrise_dt = ensure_dt(sunrise)
    sunset_dt = ensure_dt(sunset)
    now_dt = ensure_dt(now)
    
    entry = mapping.get(weather_code)

    if not entry or sunrise_dt is None or sunset_dt is None:
        # Fallback to NA icon if code missing
        return "wi-na.svg"

    # Handle polar day (sun never sets)
    if sunrise_dt == sunset_dt:
        return entry["day_icon"]

    # Handle polar night (sun never rises)
    if sunrise_dt > sunset_dt:
        return entry["night_icon"]

    # Normal case: between sunrise and sunset = day
    if sunrise_dt <= now_dt < sunset_dt:
        return entry["day_icon"]

    return entry["night_icon"]
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
        return CRITICAL, f"{label} {value:.2f} exceeds critical threshold"
    if warn is not None and value >= warn:
        return WARNING, f"{label} {value:.2f} exceeds warning threshold"
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
            return CRITICAL, f"Temperature {temp}°F is below critical threshold"
        if wt is not None and temp <= wt:
            return WARNING, f"Temperature {temp}°F is below warning threshold"
        return None

    # -----------------------------
    # Hot thresholds (temp >= threshold)
    # -----------------------------
    if ct is not None and temp >= ct:
        return CRITICAL, f"Temperature {temp}°F exceeds critical threshold"
    if wt is not None and temp >= wt:
        return WARNING, f"Temperature {temp}°F exceeds warning threshold"

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
    return OK, msg
# ---------------------------------------------------------------------------
# Output Helpers
# ---------------------------------------------------------------------------
def build_normal_message(data: Dict[str, Any], args: argparse.Namespace) -> str:
    if args.units == "imperial":
        t = data.get("temperature_f")
        w = data.get("wind_mph")
        if t is None or w is None:
            return "Weather data unavailable"
        return f"Weather normal: {t:.2f}°F, {w:.2f} mph"
    else:
        t = data.get("temperature_c")
        w = data.get("wind_kph")
        if t is None or w is None:
            return "Weather data unavailable"
        return f"Weather normal: {t:.2f}°C, {w:.2f} kph"
def output_and_exit(status: int, payload: Dict[str, Any], args, flags, weather_mode: str):
    """
    Unified output dispatcher for all display modes and all weather modes.
    weather_mode is passed explicitly from main() to avoid guessing.
    """

    # -----------------------------
    # JSON MODE (unchanged)
    # -----------------------------
    if flags[FlagNames.JSON]:
        print(json.dumps(serialize_for_json(payload), indent=2))
        os._exit(status)

    # -----------------------------
    # VERBOSE MODE
    # -----------------------------
    if flags[FlagNames.VERBOSE]:
        if weather_mode == "current":
            verbose_current(payload)
        elif weather_mode == "hourly":
            verbose_hourly(payload)
        elif weather_mode == "weekly":
            verbose_weekly(payload)
        else:
            print(f"Unknown weather mode: {weather_mode}")
        os._exit(status)

    # -----------------------------
    # QUIET MODE
    # -----------------------------
    if flags[FlagNames.QUIET]:
        if weather_mode == "current":
            quiet_current(payload)
        else:
            quiet_forecast(payload, weather_mode)
        os._exit(status)

    # -----------------------------
    # NAGIOS MODE (current only)
    # -----------------------------
    # main() already enforces that nagios cannot be used with hourly/weekly
    nagios_output(payload)
    os._exit(status)
def verbose_current(payload):
    data = payload["data"]
    units = data.get("units", "metric")

    print("Current Weather")
    print("----------------")
    print(f"Location: {payload['location']}")
    print(f"Time:     {data.get('time')}")
    print(f"Temp:     {fmt_temp(data, 'temperature', units)}")
    print(f"Feels:    {fmt_temp(data, 'apparent_temperature', units)}")
    print(f"Dewpoint: {fmt_temp(data, 'dewpoint', units)}")
    print(f"Humidity: {fmt_clouds(data.get('humidity'))}")
    print(f"Wind:     {fmt_wind(data, 'wind', units)}")
    print(f"Gusts:    {fmt_wind(data, 'wind_gust', units)}")
    print(f"Clouds:   {fmt_clouds(data.get('cloudcover'))}")
    print(f"Precip:   {fmt_precip(data, 'precip', units)}")
    print(f"Pressure: {data.get('pressure_msl')} hPa")
    print(f"Visibility: {data.get('visibility_m')} m")
    print(f"Condition: {data.get('context', 'Unknown')}")
    print(f"Source:   {data.get('source')}")
def verbose_hourly(payload):
    data = payload["data"]
    units = data.get("units", "metric")
    hours = data.get("hours", [])

    print("Hourly Forecast (Next 24 Hours)")
    print("--------------------------------")

    for h in hours:
        t = h.get("time")
        temp = fmt_temp(h, "temperature", units)
        wind = fmt_wind(h, "wind", units)
        clouds = fmt_clouds(h.get("cloudcover"))
        precip = fmt_precip(h, "precip", units)
        cond = h.get("context", "Unknown")

        print(f"{t}  {temp}  Wind {wind}  Clouds {clouds}  Precip {precip}  {cond}")
def verbose_weekly(payload):
    data = payload["data"]
    units = data.get("units", "metric")
    days = data.get("days", [])

    print("Weekly Forecast (7 Days)")
    print("------------------------")

    for d in days:
        date = d.get("date")
        tmax = fmt_temp(d, "temp_max", units)
        tmin = fmt_temp(d, "temp_min", units)
        precip = fmt_precip(d, "precip", units)
        prob = d.get("precipitation_probability_max")
        wind = fmt_wind(d, "wind", units)
        cond = d.get("context", "Unknown")

        print(f"{date}  High {tmax}  Low {tmin}  Rain {precip} ({prob}%)  Wind {wind}  {cond}")
def quiet_current(payload):
    print(payload["message"])
def quiet_forecast(payload, weather_mode):
    print(f"{weather_mode.capitalize()} forecast retrieved")
def nagios_output(payload):
    status = payload["status"]
    message = payload["message"]
    print(f"{status}: {message}")
def fmt_temp(data, key, units):
    if units == "imperial":
        return f"{data.get(key + '_f')}°F"
    return f"{data.get(key + '_c')}°C"
def fmt_wind(data, key, units):
    """
    Supports:
      - wind_kph / wind_mph
      - wind_kph_max / wind_mph_max
      - wind_gust_kph / wind_gust_mph
      - wind_gust_kph_max / wind_gust_mph_max
    """
    if units == "imperial":
        # Try normal field first, then weekly max field
        return f"{data.get(key + '_mph') or data.get(key + '_mph_max')} mph"
    else:
        return f"{data.get(key + '_kph') or data.get(key + '_kph_max')} kph"
def fmt_precip(data, key, units):
    if units == "imperial":
        return f"{data.get(key + '_in')} in"
    return f"{data.get(key + '_mm')} mm"
def fmt_clouds(v):
    return f"{v}%" if v is not None else "—"
def slice_next_24_hours(hourly):
    # Parse timestamps into datetime objects
    times = [datetime.fromisoformat(t) for t in hourly["time"]]

    # Round current time down to the hour
    now = datetime.now().replace(minute=0, second=0, microsecond=0)

    # Find first index >= now
    start = next((i for i, t in enumerate(times) if t >= now), 0)

    # Slice next 24 hours
    end = start + 24
    return range(start, min(end, len(times)))
def slice_weekly_days(days):
    today = date.today()

    # Find first index where date >= today
    start = next(
        (i for i, d in enumerate(days) if date.fromisoformat(d["date"]) >= today),
        0
    )

    # Always return 7 days if available
    return days[start:start+7]
def enrich(entry: Dict[str, Any],
           units: str,
           meta: Dict[str, Any],
           logging_enabled: bool,
           logger=None) -> Dict[str, Any]:

    # --- 1. Unit conversion (provider-agnostic) ---
    out = convert_units_any(entry, units)

    # --- 2. Extract WMO code (providers already supply this) ---
    code = entry.get("condition")

    # --- 3. Validate WMO code ---
    if code is None or not isinstance(code, int) or code not in WEATHER_CODES:
        if logger and logging_enabled:
            logger.error(f"Unknown or unmapped weather condition: {code!r}")

        out["condition"] = None
        out["context"] = "Unknown"
        out["icon"] = "wi-na.svg"
        return out

    # --- 4. Map WMO → canonical context ---
    info = WEATHER_CODES[code]
    out["context"] = info["canonical"]

    # --- 5. Icon selection (requires sunrise/sunset/time) ---
    sunrise = entry.get("sunrise")
    sunset = entry.get("sunset")
    # Weekly mode: date-only → build aware datetime using sunrise's timezone
    if entry.get("time"):
        now = entry["time"]
    elif entry.get("date"):
        # Use sunrise's timezone
        tz = meta["timezone"]
        now = datetime.fromisoformat(entry["date"]).replace(hour=12, tzinfo=tz)
    else:
        now = entry.get("startTime")

    if sunrise and sunset and now:
        out["icon"] = select_icon(code, sunrise, sunset, now, WEATHER_CODES)
    else:
        out["icon"] = "wi-na.svg"

    return out
def convert_units_mode_aware(
    data: Dict[str, Any],
    units: str,
    mode: str,
    meta: Dict[str, Any],
    logging_enabled: bool,
    logger=None
) -> Dict[str, Any]:

    match mode:
        case "current":
            out = enrich(data, units, meta, logging_enabled, logger)

        case "hourly":
            out = dict(data)
            out["hours"] = [
                enrich(h, units, meta, logging_enabled, logger)
                for h in data.get("hours", [])
            ]
            out["units"] = units
            return out

        case "weekly":
            out = dict(data)
            sliced = slice_weekly_days(data["days"])
            out["days"] = [
                enrich(d, units, meta, logging_enabled, logger)
                for d in sliced
            ]
            out["units"] = units
            return out

        case _:
            return data

    out["units"] = units
    return out
def convert_units_any(data: Dict[str, Any], units: str) -> Dict[str, Any]:
    """
    Convert any weather dictionary (current, hourly, weekly) to include
    both metric and imperial fields.
    """
    out = dict(data)

    # Temperature fields
    for key in ["temperature", "apparent_temperature", "dewpoint",
                "temp_max", "temp_min"]:
        c = out.get(f"{key}_c")
        if c is not None:
            out[f"{key}_f"] = convert_temperature(c, "C", "F")

    # Wind fields
    wind_fields = [
        ("wind_kph", "wind_mph"),
        ("wind_gust_kph", "wind_gust_mph"),
        ("wind_kph_max", "wind_mph_max"),
    ]

    for kph_key, mph_key in wind_fields:
        kph = out.get(kph_key)
        if kph is not None:
            out[mph_key] = convert_speed(kph, "kph","mph")

    # Precip fields
    for key in ["precip"]:
        mm = out.get(f"{key}_mm")
        if mm is not None:
            out[f"{key}_in"] = convert_distance(mm, "mm", "in")

    # Visibility
    if out.get("visibility_m") is not None:
        out["visibility_km"] = convert_distance(out["visibility_m"], "m", "km")
        out["visibility_mi"] = convert_distance(out["visibility_m"], "m", "mi")

    # Pressure
    if out.get("pressure_msl") is not None:
        out["pressure_inhg"] = convert_pressure(out["pressure_msl"], "hpa","inhg")

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
    if flags[WeatherFlagNames.INCLUDE_GUSTS] and gust is not None:
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
    if flags[WeatherFlagNames.INCLUDE_PRECIP] and precip is not None:
        w = args.warning_precip or ""
        c = args.critical_precip or ""
        parts.append(f"precip={precip:.2f};{w};{c}")

    # -----------------------------
    # Cloud cover (only if operator requested)
    # -----------------------------
    if flags[WeatherFlagNames.INCLUDE_CLOUDS] and cloud is not None:
        w = args.warning_cloud or ""
        c = args.critical_cloud or ""
        parts.append(f"cloud={cloud:.2f};{w};{c}")

    return " ".join(parts)
# --------------------------------------
# Logging Functions
# --------------------------------------
def initialize_logger(args, mode):
    if mode == "nagios" or not args.log_dir:
        return None

    try:
        os.makedirs(args.log_dir, exist_ok=True)

        log_cfg = {
            "path": os.path.join(args.log_dir, f"{SCRIPT_NAME}.log"),
            "log_level": "INFO",
            "log_max_mb": args.log_max_mb,
            "archive_mode": "zip",
            "backup_count": 7,
            "console_stream": sys.stderr,
            "console_enabled": not args.quiet and args.verbose,
            "color": False if mode == "nagios" else args.color,
        }

        logger_factory = LoggerFactory(log_cfg, SCRIPT_NAME)
        return logger_factory.get_logger("main")

    except Exception as e:
        if should_output(mode):
            print(nagios_summary(UNKNOWN, f"Failed to initialize LoggerFactory: {e}"))
        return None
def start_banner_weather(meta):
    return (
        f"[START] {SCRIPT_NAME}.py"
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
def log_weather_data_mode_aware(weather_mode: str, data: Dict[str, Any]) -> str:
    if weather_mode == "current":
        return log_weather_current_flat(data)
    elif weather_mode == "hourly":
        return log_weather_hourly_flat(data)
    elif weather_mode == "weekly":
        return log_weather_weekly_flat(data)
    else:
        return f"[WEATHER] error=unknown_mode mode={weather_mode}"
def log_weather_data(weather):
    fields = []
    for k, v in weather.items():
        fields.append(f"{k}={v}")
    return "[WEATHER] " + " ".join(fields)
def log_weather_current_flat(data: Dict[str, Any]) -> str:
    fields = []
    for k, v in data.items():
        fields.append(f"{k}={v}")
    return "[WEATHER] " + " ".join(fields)
def log_weather_hourly_flat(data: Dict[str, Any]) -> str:
    hours = data.get("hourly", [])
    lines = []

    for i, h in enumerate(hours):
        fields = []
        for k, v in h.items():
            fields.append(f"hour[{i}].{k}={v}")
        lines.append("[WEATHER] " + " ".join(fields))

    return "\n".join(lines)
def log_weather_weekly_flat(data: Dict[str, Any]) -> str:
    days = data.get("days", [])
    lines = []

    for i, d in enumerate(days):
        fields = []
        for k, v in d.items():
            fields.append(f"day[{i}].{k}={v}")
        lines.append("[WEATHER] " + " ".join(fields))

    return "\n".join(lines)
def log_summary_weather(state, message):
    return f"[RESULT] state={state} message=\"{message}\""
def end_banner():
    return "[END]"
# -----------------------------
# Provider Registry
# -----------------------------
WEATHER_PROVIDERS = {
    "open-meteo": {
        "supports": ["current", "hourly", "weekly"],
        "fetch_current": fetch_current_open_meteo,
        "fetch_hourly": fetch_hourly_open_meteo,
        "fetch_weekly": fetch_weekly_open_meteo,
    },
    "nws": {
        "supports": ["current", "hourly", "weekly"],
        "fetch_current": fetch_current_nws,
        "fetch_hourly": fetch_hourly_nws,
        "fetch_weekly": fetch_weekly_nws,
    }
}
def fetch_weather(
    lat: float,
    lon: float,
    timeout: int,
    provider: str,
    units: str,
    force_cache: bool,
    mode: str,
    meta: Dict[str, Any],
    logging_enabled: bool,
    logger = None
) -> Tuple[Dict[str, Any], Optional[str], str, Optional[float], bool]:

    # Cache key must include mode + provider
    cache_id = f"{lat},{lon}:{units}:{provider}:{mode}"

    # Try cache first
    cached, cached_ts = load_weather_cache(cache_id)
    cache_age = None
    if cached_ts:
        cache_age = (datetime.now() - cached_ts).total_seconds()

    # Forced cache mode
    if force_cache:
        if cached is None:
            raise RuntimeError("Forced cache read but no cache exists")
        return cached, None, "cache-forced", cache_age, False

    # Provider dispatch
    if provider not in WEATHER_PROVIDERS:
        raise ValueError(f"Unsupported provider: {provider}")

    prov = WEATHER_PROVIDERS[provider]

    if mode not in prov["supports"]:
        raise RuntimeError(f"Provider '{provider}' does not support mode '{mode}'")

    fetch_fn = prov[f"fetch_{mode}"]

    # Try live provider
    live = None
    url = None
    try:
        if provider == "nws":
            meta.update(resolve_nws_meta(lat,lon))
        live, url = fetch_fn(lat, lon, timeout, meta)
    except Exception:
        live = None

    # Live success → convert + save cache
    if live:
        data = convert_units_mode_aware(live, units, mode, meta, logging_enabled, logger)
        save_weather_cache(cache_id, data)
        return data, url, "live", 0, True

    # Live failed → fallback to cache
    if cached:
        data = convert_units_mode_aware(cached, units, mode, meta, logging_enabled, logger)
        return data, None, "cache", cache_age, False

    # No live + no cache → fail
    raise RuntimeError("Weather API unreachable and no cached data")
# -----------------------------
# Main
# -----------------------------
def main() -> None:
    args, flags, mode = build_parser()
    weather_flags = WeatherFlags.from_args(args)
    # Base metadata (script name, mode, log_dir)
    meta = {
        "log_dir": str(Path(args.log_dir).expanduser()) if args.log_dir else None,
        "flags": flags,
        "weather_flags": weather_flags,
        "mode": mode,
    }
    logger = initialize_logger(args, meta["mode"])
    # ------------------------------------------------------------
    # 5. Determine Nagios mode + logging
    # ------------------------------------------------------------
    logging_enabled = mode != "nagios" and meta["log_dir"]
    if not validate_location_input(args.location, args.country):
        raise ValueError(f"Invalid Location Specified: {args.location}")

    meta["start"] = time.time()


    # -----------------------------
    # WEATHER MODE (new)
    # -----------------------------
    weather_mode = (
        "weekly" if weather_flags[WeatherFlagNames.WEEKLY] else
        "hourly" if weather_flags[WeatherFlagNames.HOURLY] else
        "current"
    )

    # Nagios only works with current mode
    if mode == "nagios" and weather_mode != "current":
        raise RuntimeError("Nagios mode only supports current weather.")

    meta.update({
        "location_input": args.location,
        "country": args.country,
        "units": args.units,
        "provider": args.provider,
        "ignore_cache": weather_flags[WeatherFlagNames.IGNORE_CACHE],
        "ignore_ttl": weather_flags[WeatherFlagNames.IGNORE_TTL],
        "force_cache": weather_flags[WeatherFlagNames.FORCE_CACHE],
        "include_gusts": weather_flags[WeatherFlagNames.INCLUDE_GUSTS],
        "include_precip": weather_flags[WeatherFlagNames.INCLUDE_PRECIP],
        "include_clouds": weather_flags[WeatherFlagNames.INCLUDE_CLOUDS],
        "log_max_mb": args.log_max_mb,
        "mode": mode,
        "weather_mode": weather_mode,   # NEW
    })

    logging_enabled = mode != "nagios" and args.log_dir

    loc = resolve_location(args)
    lat = loc.get("latitude", 0)
    lon = loc.get("longitude", 0)
    meta.update({"timezone":get_timezone(lat,lon)})
    
    if logger and logging_enabled:
        logger.info(start_banner_weather(meta))
        logger.info(log_weather_data(loc))

    # -----------------------------
    # FETCH WEATHER (now mode-aware)
    # -----------------------------
    data, url, source, cache_age, cache_written = fetch_weather(
        lat, lon, args.timeout,
        args.provider, args.units,
        args.force_cache,
        weather_mode,
        meta,
        logging_enabled,
        logger
    )

    data["source"] = "Live API" if source == "live" else source
    data["cache_written"] = cache_written
    if cache_age is not None:
        data["cache_age"] = format_age(cache_age)

    # -----------------------------
    # STATUS EVALUATION (current only)
    # -----------------------------
    if weather_mode == "current":
        status, message = evaluate_weather(data, args)
    else:
        # Hourly/weekly do not produce Nagios-style status
        status, message = 0, f"{weather_mode.capitalize()} forecast retrieved"

    if logger and logging_enabled:
        logger.info(log_weather_data_mode_aware(weather_mode, data))

    runtime = round((time.time() - meta["start"]) * 1000, 2)

    payload = {
        "status": ["OK", "WARNING", "CRITICAL", "UNKNOWN"][status],
        "message": message,
        "location": format_resolved_name(loc),
        "data": strip_none(data),
        "runtime_ms": runtime,
        "weather_mode": weather_mode,
    }

    if flags[WeatherFlagNames.SHOW_LOCATION_DETAILS]:
        weather_url = url.split("?")[0] if url is not None else None
        payload["resolved_location"] = {
            "input": args.location,
            "weather_provider": args.provider,
            "weather_provider_url": weather_url,
            "location_provider": loc.get("provider"),
            "location_provider_url": loc.get("url"),
            "city": loc.get("city"),
            "state": loc.get("state"),
            "zip": loc.get("zip"),
            "country": args.country,
            "latitude": loc.get("latitude"),
            "longitude": loc.get("longitude"),
            "weather_url": url,
        }

    if logger and logging_enabled:
        logger.info(log_summary_weather(payload.get("status"), payload.get("message")))
        logger.info(end_banner())

    output_and_exit(status, payload, args, flags, weather_mode)

if __name__ == "__main__":
    if sys.version_info < (MIN_MAJOR, MIN_MINOR):
        print(f"CRITICAL: Python {MIN_MAJOR}.{MIN_MINOR}+ required, "
            f"but running on {sys.version_info.major}.{sys.version_info.minor}")
        sys.exit(2)
    main()
