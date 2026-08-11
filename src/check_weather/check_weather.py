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

from datetime import datetime, timedelta
from enum import IntEnum, auto
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from PythonTools.cache import (
    ensure_subdir,
    cache_path,
    load_json_cache,
    save_json_cache,
    serialize_for_json,
)

from PythonTools.color import Color,colorize
from PythonTools.datetime import (
    format_age,
    get_timezone,
)
from PythonTools.location import (
    US_STATES,
    normalize_city_name,
    validate_location_input,
    format_resolved_name,
    resolve_location as pt_resolve,
    LocationNotFoundError,
    LocationInfo,
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
from PythonTools.utils import strip_none
from PythonTools.weather import (
    WEATHER_PROVIDERS,
    convert_units_mode_aware,
    fmt_temp,
    fmt_clouds,
    fmt_wind,
    fmt_precip,
)
from PythonTools.weather.providers import register_providers, resolve_nws_meta
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
DEFAULT_WEATHER_ICON = "wi-na.svg"

# Flag Classes
class WeatherFlagNames(IntEnum):
    INCLUDE_GUSTS = auto()
    INCLUDE_PRECIP = auto()
    INCLUDE_CLOUDS = auto()
    WEEKLY = auto()
    HOURLY = auto()
    FULL = auto()

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
        f.set(WeatherFlagNames.FULL, args.full)

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
    modes.add_argument("--full", action="store_true",
                    help="Show full forecast, including current, weekly, hourly.")
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
    # Enforce mutual exclusivity manually
    mode_flags = [
        args.weekly,
        args.hourly,
        args.full
    ]

    if sum(bool(x) for x in mode_flags) > 1:
        raise ValueError("Only one mode may be selected: --weekly, --hourly, or --full.")

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
        raise ValueError("Specify exactly one of --location, --zip, --city, or --lat/--lon")
    if args.zip:
        args.location = args.zip
    elif args.city:
        args.location = args.city
    elif args.lat and args.lon:
        args.location = f"{args.lat},{args.lon}"

    return args, flags, mode
# ---------------------------------------------------------------------------
# Location Resolver (ZIP, City, Lat/Long)
# ---------------------------------------------------------------------------
# check_weather/location.py
def resolve_location(args):
    """
    Weather-specific wrapper around PythonTools.location.resolve_location.
    Adds caching and returns a weather-tooling dict.
    """

    original = args.location.strip()
    country = (args.country or "US").upper()
    timeout = args.timeout

    cache_key = f"{country}:{original.lower().strip()}"
    cached = load_location_from_cache(cache_key)
    if cached:
        return cached

    try:
        info: LocationInfo = pt_resolve(original, country, timeout)
    except LocationNotFoundError:
        raise RuntimeError(f"City not found: {original}")

    result = {
        "query": info.query,
        "provider": info.provider,
        "latitude": info.point.latitude,
        "longitude": info.point.longitude,
        "city": normalize_city_name(info.city),
        "state": info.state,
        "country": info.country,
        "zip": info.zip,
        "url": info.url,
    }

    save_location_to_cache(cache_key, result)
    return result
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
    register_providers()
    # -----------------------------
    # WEATHER MODE (new)
    # -----------------------------
    weather_mode = (
        "weekly" if weather_flags[WeatherFlagNames.WEEKLY] else
        "hourly" if weather_flags[WeatherFlagNames.HOURLY] else
        "full" if weather_flags[WeatherFlagNames.FULL] else
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
