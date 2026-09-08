#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Leon McClatchey, Linktech Engineering LLC
"""
File: export_icons.py
Author: Leon McClatchey
Company: Linktech Engineering LLC
Created: 2026-05-04
Modified: 2026-09-08
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

import argparse
import os
import platform
import re
import shutil
import sys
import time
import zipfile
from collections import Counter
from datetime import datetime
from pathlib import Path

from PythonTools.log_helpers.factory import LoggerFactory
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

    # Core options
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

    return parser.parse()
# Manage the Icons
def extract_icon_list():
    """
    Extract all .svg filenames from the WEATHER_CODES dict in check_weather.py.
    Returns a sorted list of unique filenames.
    """
    source = Path(__file__).resolve().parent / "check_weather.py"

    if not source.exists():
        raise FileNotFoundError(f"Cannot find check_weather.py at {source}")

    text = source.read_text()

    # Extract the WEATHER_CODES dict block
    m = re.search(r"WEATHER_CODES\s*=\s*{(.*?)}\s*$", text, re.S | re.M)
    if not m:
        raise RuntimeError("Could not locate WEATHER_CODES dict in check_weather.py")

    block = m.group(1)

    # Extract all .svg filenames
    icons = re.findall(r'"([^"]+\.svg)"', block)

    return sorted(set(icons))
def copy_icon(src, dst):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(src, dst)
def process_icon(icon, meta, logger = None):
    src = SRC_DIR / icon
    dst = DST_DIR / icon

    if not src.exists():
        msg = f"[MISSING] {icon}"
        print(msg)
        if logger:
            logger.info(meta, msg)
        return

    # DRY RUN
    if meta["dry_run"]:
        msg = f"[DRYRUN] Would copy {src} → {dst}"
        print(msg)
        if logger:
            logger.info(meta, msg)
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
        logger.info(meta, msg)

# --------------------------------------
# Logging Functions (export_icons)
# --------------------------------------
def initialize_logger(meta):
    log_dir = meta.get("log_dir")
    if not log_dir:
        return None

    try:
        os.makedirs(log_dir, exist_ok=True)

        log_cfg = {
            "path": os.path.join(log_dir, "export_icons.log"),
            "log_level": "INFO",
            "log_max_mb": meta.get("log_max_mb", 50),
            "archive_mode": "zip",
            "backup_count": 7,
            "console_stream": sys.stderr,
            "console_enabled": meta.get("console_enabled", False),
            "color": False,
        }

        logger_factory = LoggerFactory(log_cfg, "export_icons")
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
    logger = initialize_logger(meta)
    if logger:
        logger.info(meta, f"[START] export_icons.py dry_run={meta['dry_run']}")
    icons = extract_icon_list()
    print(f"Processing {len(icons)} icons...")
    for icon in icons:
        process_icon(icon, meta, logger)

    duration = round(time.time() - start, 3)
    if logger:
        logger.info(meta, f"[SUMMARY] icons={len(icons)} dry_run={meta['dry_run']} duration={duration}s status=success")
        logger.info(meta, f"Total icons: {len(icons)}\n")
        logger.info(meta, "=== Icon Classification Summary ===")
    for g in ["sun", "moon", "cloud", "rain", "snow", "thunder", "fog", "wind"]:
        if logger:
            logger.info(meta, f"{g:8}: {STATS[g]}")
    # Percentages
    if logger:
        logger.inf(meta, "")
        logger.info(meta, "=== Group Coverage Percentages ===")
    for g in ["sun", "moon", "cloud", "rain", "snow", "thunder", "fog", "wind"]:
        pct = (STATS[g] / len(icons)) * 100
        if logger:
            logger.info(meta, f"{g:8}: {STATS[g]:2d}  ({pct:5.1f}%)")

    # Histogram of groups per icon
    if logger:
        logger.info(meta, "")
        logger.info(meta, "=== Groups Per Icon Histogram ===")
    for n in sorted(GROUPS_PER_ICON):
        if logger:
            logger.info(meta, f"{n} groups: {GROUPS_PER_ICON[n]}")

    # Day/night breakdown
    if logger:
        logger.info(meta, "")
        logger.info(meta, "=== Day/Night Breakdown ===")
        logger.info(meta, f"day     : {DAY_NIGHT['day']}")
        logger.info(meta, f"night   : {DAY_NIGHT['night']}")
        logger.info(meta, f"unknown : {DAY_NIGHT['unknown']}")
        logger.info(meta, "[END]")

if __name__ == "__main__":
    main()


