#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Leon McClatchey, Linktech Engineering LLC
"""
File: export_icons.py
Author: Leon McClatchey
Company: Linktech Engineering LLC
Created: 2026-05-04
Modified: 2026-09-23
Required: Python 3.8+
Part of: NMS_Tools Monitoring Suite
License: MIT (see LICENSE for details)

Description:
    Extracts the SVG icon filenames referenced by WEATHER_CODES in check_weather.py,
    copies the corresponding source icons into the web/icons directory, and applies
    deterministic recoloring using the recolor_engine subsystem. Supports dry-run,
    verbose output, and operator-grade logging with rotation.

"""
# export_icons.py

import os
import requests
import shutil
import sys
import time
from collections import Counter
from pathlib import Path

from PythonTools.log_helpers.factory import LoggerFactory
from PythonTools.weather import (
    collect_alert_icons,
    collect_weather_icons,
    generate_alert_svg
)
from PythonTools.weather.codes import WEATHER_CODES
from PythonTools.weather.recolor_engine import analyze_svg
from PythonTools.weather.recolor_engine.recolor import recolor
from PythonTools.utils.common import load_version
from PythonTools.parser import BaseScriptParser
from PythonTools.nagios import build_version_string
# Global Constants
SUITE_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_VERSION = "1.0.0"
SCRIPT_NAME = Path(sys.argv[0]).stem
VERSION = load_version(SUITE_ROOT)
SRC_DIR = Path(__file__).resolve().parent / "svg"
DST_DIR = Path(__file__).resolve().parent / "web" / "icons"
DEFAULT_LOG_DIR = Path.home() / "logs"
STATS = Counter()
GROUPS_PER_ICON = Counter()
DAY_NIGHT = Counter()
# ---------------------------------------------------------------------------
# Status Codes
# ---------------------------------------------------------------------------
STATUS_OK = 0
STATUS_WARNING = 1
STATUS_CRITICAL = 2
STATUS_UNKNOWN = 3
MIN_MAJOR = 3
MIN_MINOR = 8
# ----------------------------------------------
# Argument Parser
# -----------------------------------------------
def build_parser():
    parser = BaseScriptParser(
        prog=SCRIPT_NAME,
        description=(
            "Icon Export Tool\n\n"
            "Extracts, copies, and recolors the SVG icons referenced by "
            "check_weather.py. Intended for use during development and "
            "deployment of the NMS_Tools weather demo."
        ),
        version_string = build_version_string(SCRIPT_NAME, SCRIPT_VERSION, VERSION)
    )

    # Remove irrelevant global groups
    parser.remove_group("Config Options")
    parser.remove_group("Inventory Options")
    parser.remove_group("Vault Options")

    # Remove global JSON/color flags
    parser.remove_flag("--json")
    parser.remove_flag("--color")

    # Path options
    paths = parser.add_group("Paths Options")
    paths.add_argument(
        "-s", "--src",
        default=str(SRC_DIR),
        help="Source directory containing raw SVG icons",
    )
    paths.add_argument(
        "-d", "--dst",
        default=str(DST_DIR),
        help="Destination directory for exported/recolored icons",
    )
    source = parser.add_group("Icon Source")
    source.add_argument(
        "--icon-source",
        choices=["local", "remote", "hybrid"],
        default="local",
        help=(
            "Where to obtain icons:\n"
            "'local' uses only local SVGs;\n"
            "'remote' downloads all icons from the upstream Weather Icons repo;\n"
            "'hybrid' uses local icons when present and downloads missing ones."
        )
    )
    source.add_argument(
        "--icon",
        action="append",
        help="Name of a specific icon to export. Use multiple --icon flags to export more than one."
    )
    args = parser.parse()
    if hasattr(args, "func"):
        return args.func(args)
    args.log_dir = args.log_dir or DEFAULT_LOG_DIR
    return args
# Manage the Icons
def extract_icon_list(args, logger=None):
    """
    Return the full set of icons used by weather conditions + alerts.
    If --icon is provided, validate the requested icons.
    """
    icons = set()

    icons.update(collect_weather_icons())
    icons.update(collect_alert_icons())

    # User requested specific icons
    if args.icon:
        requested = set(args.icon)
        invalid = requested - icons

        if invalid:
            # Compact single-line list of invalid icons
            bad = ", ".join(sorted(invalid))
            msg = (
                f"[ERROR] The following icons are not recognized: {bad}\n"
                "Use --list-icons to see valid names."
            )

            if logger:
                logger.error(msg)
            else:
                print(msg)

            return []  # signal invalid input

        return sorted(requested)

    # Default: return all icons
    return sorted(icons)
def fetch_remote_icon(dst, logger=None):
    """
    Download icon_name from the Weather Icons repo and save it to dst.
    If dst already exists, skip download.
    Returns the path to the saved file.
    """

    # Guard against malformed paths
    if not dst.name or dst.name in {"None", ""}:
        msg = f"Invalid icon name in path: {dst}"
        if logger:
            logger.error(msg)
        raise ValueError(msg)

    icon_name = dst.name

    # Skip if already downloaded
    if dst.exists():
        if logger:
            logger.debug(f"Skipping {icon_name}: already exists at {dst}")
        return dst
    if icon_name == "alert.svg":
        if logger:
            logger.info(f"Creating icon: {icon_name}")
        dst.write_text(generate_alert_svg())
        return dst

    url = f"https://raw.githubusercontent.com/erikflowers/weather-icons/master/svg/{icon_name}"

    if logger:
        logger.info(f"Downloading remote icon: {icon_name}")

    resp = requests.get(url, timeout=10)

    if resp.status_code != 200:
        msg = f"Could not download icon {icon_name}: HTTP {resp.status_code}"
        if logger:
            logger.error(msg)
        raise RuntimeError(msg)

    # Ensure directory exists
    dst.parent.mkdir(parents=True, exist_ok=True)

    # Save the file
    dst.write_text(resp.text)

    if logger:
        logger.info(f"Saved remote icon: {icon_name} → {dst}")

    return dst

def copy_icon(src, dst):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(src, dst)
def process_icon(icon, meta, logger = None):
    src = SRC_DIR / icon
    dst = DST_DIR / icon
    if not SRC_DIR.exists():
        SRC_DIR.mkdir(parents=True, exist_ok=True)

    if not src.exists():
        msg = f"[MISSING] {icon}"
        print(msg)
        if logger:
            logger.info(msg)
        return

    # DRY RUN
    if meta["dry_run"]:
        msg = f"[DRYRUN] Would copy {src} → {dst}"
        print(msg)
        if logger:
            logger.info(msg)
        return

    # REAL MODE: copy
    copy_icon(src, dst)

    # REAL MODE: analyze + recolor
    tree, groups = analyze_svg(dst)

    # groups is already the final classification:
    # { "sun": [...], "cloud": [...], ... }

    # Determine which groups are active (non-empty)
    active = [g for g, elems in groups.items() if elems]

    # Update stats
    STATS.update(active)
    # Histogram: how many groups per icon
    GROUPS_PER_ICON[len(active)] += 1

    # Day/night breakdown
    name = icon.lower()
    if "day" in name:
        DAY_NIGHT["day"] += 1
    elif "night" in name:
        DAY_NIGHT["night"] += 1
    else:
        DAY_NIGHT["unknown"] += 1

    # Stable ordering
    priority = ["sun", "moon", "cloud", "rain", "snow", "thunder", "fog", "wind"]
    active = [g for g in priority if g in active]

    # Recolor using the analyzer's groups
    recolored = recolor(tree, groups, active)
    recolored.write(dst)

    msg = f"[OK] {icon} → groups={active}"
    print(msg)
    if logger:
        logger.info(msg)

# --------------------------------------
# Logging Functions (export_icons)
# --------------------------------------
def initialize_logger(meta, debug=False):
    log_dir = meta.get("log_dir")
    if not log_dir:
        return None

    try:
        os.makedirs(log_dir, exist_ok=True)

        log_cfg = {
            "path": os.path.join(log_dir, "export_icons.log"),
            "log_level": "DEBUG" if debug else "INFO",
            "log_max_mb": meta.get("log_max_mb", 50),
            "archive_mode": "zip",
            "backup_count": 7,
            "console_stream": sys.stderr,
            "console_enabled": meta.get("console_enabled", False),
            "color": False,
        }

        logger_factory = LoggerFactory(log_cfg, SCRIPT_NAME)
        return logger_factory.get_logger("main")

    except Exception as e:
        warn = f"Unable to initialize logger: {e}"
        print(warn)
        meta.setdefault("warnings", []).append(warn)
        return None

def main():
    start = time.time()
    args = build_parser()
    meta = {
        "log_dir": args.log_dir,
        "log_max_mb": args.log_max_mb,
        "dry_run": args.dry_run,
        "_log_warn_emitted": False,
        "warnings": [],
    }
    logger = initialize_logger(meta, args.debug)
    if logger:
        logger.info(f"[START] export_icons.py dry_run={meta['dry_run']}")
    icons = extract_icon_list(args, logger)
    print(f"Downloading {len(icons)} icons...")
    for icon in icons:
        fetch_remote_icon(SRC_DIR / icon, logger)
    fetch_remote_icon(SRC_DIR / "alert.svg", logger)
    print(f"Processing {len(icons)} icons...")
    for icon in icons:
        process_icon(icon, meta, logger)

    duration = round(time.time() - start, 3)
    if logger:
        logger.info(f"[SUMMARY] icons={len(icons)} dry_run={meta['dry_run']} duration={duration}s status=success")
        logger.info(f"Total icons: {len(icons)}\n")
        logger.info("=== Icon Classification Summary ===")
    for g in ["sun", "moon", "cloud", "rain", "snow", "thunder", "fog", "wind"]:
        if logger:
            logger.info(f"{g:8}: {STATS[g]}")
    # Percentages
    if logger:
        logger.info("")
        logger.info("=== Group Coverage Percentages ===")
    for g in ["sun", "moon", "cloud", "rain", "snow", "thunder", "fog", "wind"]:
        pct = (STATS[g] / len(icons)) * 100
        if logger:
            logger.info(f"{g:8}: {STATS[g]:2d}  ({pct:5.1f}%)")

    # Histogram of groups per icon
    if logger:
        logger.info("")
        logger.info("=== Groups Per Icon Histogram ===")
    for n in sorted(GROUPS_PER_ICON):
        if logger:
            logger.info(f"{n} groups: {GROUPS_PER_ICON[n]}")

    # Day/night breakdown
    if logger:
        logger.info("")
        logger.info("=== Day/Night Breakdown ===")
        logger.info(f"day     : {DAY_NIGHT['day']}")
        logger.info(f"night   : {DAY_NIGHT['night']}")
        logger.info(f"unknown : {DAY_NIGHT['unknown']}")
        logger.info("[END]")

if __name__ == "__main__":
    main()


