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

Description: Description of this module

"""
# export_icons.py

import os
import re
import shutil
import sys
from pathlib import Path

from recolor_engine.classifier import classify_from_filename
from recolor_engine.analyzer import analyze_svg
from recolor_engine.recolor import recolor

SRC_DIR = Path(__file__).resolve().parent / "svg"
DST_DIR = Path(__file__).resolve().parent / "web" / "icons"

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

def process_icon(icon):
    src = os.path.join(SRC_DIR, icon)
    dst = os.path.join(DST_DIR, icon)

    if not os.path.exists(src):
        print(f"[MISSING] {icon}")
        return

    copy_icon(src, dst)

    expected = classify_from_filename(icon)
    tree, verified = analyze_svg(dst)

    # intersection check
    if not any(verified[g] for g in expected):
        print(f"[SKIP] {icon} — no verified groups")
        return

    recolored = recolor(tree, verified, expected)
    recolored.write(dst)

    print(f"[OK] {icon} → {expected}")

def main():
    icons = extract_icon_list()
    print(f"Processing {len(icons)} icons...")
    sys.exit(0)
    for icon in icons:
        process_icon(icon)

if __name__ == "__main__":
    main()


