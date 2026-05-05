#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Leon McClatchey, Linktech Engineering LLC
"""
File: export_icons.py
Author: Leon McClatchey
Company: Linktech Engineering LLC
Created: 2026-05-04
Modified: 2026-05-04
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

from recolor_engine.analyzer import analyze_svg
from recolor_engine.recolor import recolor
# Global Constants
SUITE_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_VERSION = "1.0.0"
SCRIPT_NAME = Path(sys.argv[0]).stem
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
# ----------------------------------------------------------------------------
# Python Version
# ----------------------------------------------------------------------------
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
        prog=SCRIPT_NAME,
        description=(
            "Icon Export Tool\n\n"
            "Extracts, copies, and recolors the SVG icons referenced by "
            "check_weather.py. Intended for use during development and "
            "deployment of the NMS_Tools weather demo."
        ),
        formatter_class=CustomFormatter,
        add_help=True,
    )

    # Core options
    core = parser.add_argument_group("Core Options")
    core.add_argument(
        "-s", "--src",
        default=str(SRC_DIR),
        help="Source directory containing raw SVG icons",
    )
    core.add_argument(
        "-d", "--dst",
        default=str(DST_DIR),
        help="Destination directory for exported/recolored icons",
    )
    core.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate actions without writing files",
    )

    # Logging options
    log = parser.add_argument_group("Logging Options")
    log.add_argument(
        "-l", "--log-dir",
        dest="log_dir",
        default=str(DEFAULT_LOG_DIR),
        help="Directory to store logs (optional). If omitted, logging is disabled.",
    )
    log.add_argument(
        "--log-max-mb",
        type=int,
        default=50,
        dest="log_max_mb",
        help="Maximum log size in MB before rotation.",
    )

    # Output options
    out = parser.add_argument_group("Output Options")
    out.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Detailed output",
    )
    out.add_argument(
        "-V", "--version",
        action="version",
        version=(
            f"NMS_TOOLS Suite Version: {VERSION}\n"
            f"{SCRIPT_NAME}: {SCRIPT_VERSION}\n"
            f"Python: {platform.python_version()}"
        ),
        help="Show script and Python version",
    )

    return parser.parse_args()
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
def process_icon(icon, meta):
    src = SRC_DIR / icon
    dst = DST_DIR / icon

    if not src.exists():
        msg = f"[MISSING] {icon}"
        print(msg)
        write_log(meta, msg)
        return

    # DRY RUN
    if meta["dry_run"]:
        msg = f"[DRYRUN] Would copy {src} → {dst}"
        print(msg)
        write_log(meta, msg)
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
    write_log(meta, msg)

# --------------------------------------
# Logging Functions (export_icons)
# --------------------------------------
def ts():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
def write_log(meta, message):
    log_dir = meta.get("log_dir")
    if not log_dir:
        return

    try:
        os.makedirs(log_dir, exist_ok=True)
        logfile = os.path.join(log_dir, f"{SCRIPT_NAME}.log")
        with open(logfile, "a", encoding="utf-8") as f:
            f.write(f"{ts()}; {message}\n")
    except Exception as e:
        if not meta.get("_log_warn_emitted"):
            meta["_log_warn_emitted"] = True
            warning = f"[WARN] Unable to write to log directory: {log_dir} — {e}"
            print(warning)
            meta.setdefault("warnings", []).append(warning)
def rotate_log_if_needed(meta):
    log_dir = meta.get("log_dir")
    if not log_dir:
        return

    logfile = os.path.join(log_dir, f"{SCRIPT_NAME}.log")
    if not os.path.exists(logfile):
        return

    max_mb = meta.get("log_max_mb", 50)
    max_bytes = max_mb * 1024 * 1024

    try:
        if os.path.getsize(logfile) < max_bytes:
            return

        archive_path = build_archive_path(meta)
        shutil.move(logfile, archive_path)
        compress_file(archive_path)

        with open(logfile, "w", encoding="utf-8") as f:
            f.write(f"{ts()}; [INFO] log rotated to {os.path.basename(archive_path)}.zip\n")

    except Exception as e:
        if not meta.get("_log_warn_emitted"):
            meta["_log_warn_emitted"] = True
            warn = f"[WARN] Unable to rotate log file '{logfile}': {e}"
            print(warn)
            meta.setdefault("warnings", []).append(warn)
def build_archive_path(meta):
    ts_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    return os.path.join(meta["log_dir"], f"{SCRIPT_NAME}_{ts_str}.log")
def compress_file(path):
    zip_path = path + ".zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(path, os.path.basename(path))
    os.remove(path)

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
    rotate_log_if_needed(meta)
    write_log(meta, f"[START] export_icons.py dry_run={meta['dry_run']}")
    icons = extract_icon_list()
    print(f"Processing {len(icons)} icons...")
    for icon in icons:
        process_icon(icon, meta)

    duration = round(time.time() - start, 3)
    write_log(meta, f"[SUMMARY] icons={len(icons)} dry_run={meta['dry_run']} duration={duration}s status=success")
    write_log(meta, f"Total icons: {len(icons)}\n")
    write_log(meta, "=== Icon Classification Summary ===")
    for g in ["sun", "moon", "cloud", "rain", "snow", "thunder", "fog", "wind"]:
        write_log(meta, f"{g:8}: {STATS[g]}")
    # Percentages
    write_log(meta, "")
    write_log(meta, "=== Group Coverage Percentages ===")
    for g in ["sun", "moon", "cloud", "rain", "snow", "thunder", "fog", "wind"]:
        pct = (STATS[g] / len(icons)) * 100
        write_log(meta, f"{g:8}: {STATS[g]:2d}  ({pct:5.1f}%)")

    # Histogram of groups per icon
    write_log(meta, "")
    write_log(meta, "=== Groups Per Icon Histogram ===")
    for n in sorted(GROUPS_PER_ICON):
        write_log(meta, f"{n} groups: {GROUPS_PER_ICON[n]}")

    # Day/night breakdown
    write_log(meta, "")
    write_log(meta, "=== Day/Night Breakdown ===")
    write_log(meta, f"day     : {DAY_NIGHT['day']}")
    write_log(meta, f"night   : {DAY_NIGHT['night']}")
    write_log(meta, f"unknown : {DAY_NIGHT['unknown']}")

    write_log(meta, "[END]")

if __name__ == "__main__":
    main()


