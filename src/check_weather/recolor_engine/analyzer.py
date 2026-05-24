#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Leon McClatchey, Linktech Engineering LLC
"""
File: analyzer.py
Author: Leon McClatchey
Company: Linktech Engineering LLC
Created: 2026-05-04
Modified: 2026-05-06
Required: Python 3.8+
Part of: NMS_Tools Monitoring Suite
License: MIT (see LICENSE for details)

Description: 
    Classifier that normalizes Weather Icons into semantic groups by 
    blending geometric detection (sun/moon/cloud) with filename‑based precipitation inference 
    for accurate recoloring.
"""

import math
import re
import xml.etree.ElementTree as ET
from pathlib import Path

GROUPS = ["sun", "moon", "cloud", "rain", "snow", "thunder", "fog", "wind"]


# ------------------------------------------------------------
# Path parsing → approximate curves as line segments
# ------------------------------------------------------------

def parse_path(d):
    """
    Returns a list of line segments: [(x1,y1,x2,y2), ...]
    Handles M, L, H, V, C, Z (enough for Weather Icons).
    Curves are approximated by straight segments.
    """
    tokens = re.findall(r"[A-Za-z]|[-+]?\d*\.\d+|[-+]?\d+", d)
    i = 0
    cmd = None
    x = y = 0.0
    start_x = start_y = 0.0
    segments = []

    def add_seg(x1, y1, x2, y2):
        segments.append((x1, y1, x2, y2))

    while i < len(tokens):
        t = tokens[i]

        if re.match(r"[A-Za-z]", t):
            cmd = t
            i += 1
            continue

        if cmd in ("M", "m"):
            nx = float(tokens[i]); ny = float(tokens[i+1])
            if cmd == "m":
                nx += x; ny += y
            x, y = nx, ny
            start_x, start_y = x, y
            i += 2
            cmd = "L" if cmd == "M" else "l"
            continue

        if cmd in ("L", "l"):
            nx = float(tokens[i]); ny = float(tokens[i+1])
            if cmd == "l":
                nx += x; ny += y
            add_seg(x, y, nx, ny)
            x, y = nx, ny
            i += 2
            continue

        if cmd in ("H", "h"):
            nx = float(tokens[i])
            if cmd == "h":
                nx += x
            add_seg(x, y, nx, y)
            x = nx
            i += 1
            continue

        if cmd in ("V", "v"):
            ny = float(tokens[i])
            if cmd == "v":
                ny += y
            add_seg(x, y, x, ny)
            y = ny
            i += 1
            continue

        if cmd in ("C", "c"):
            # C x1 y1 x2 y2 x y
            x1 = float(tokens[i]);   y1 = float(tokens[i+1])
            x2 = float(tokens[i+2]); y2 = float(tokens[i+3])
            nx = float(tokens[i+4]); ny = float(tokens[i+5])
            if cmd == "c":
                x1 += x; y1 += y
                x2 += x; y2 += y
                nx += x; ny += y
            px, py = x, y
            for tval in [k/10 for k in range(1, 11)]:
                xt = ((1-tval)**3)*x + 3*((1-tval)**2)*tval*x1 + 3*(1-tval)*(tval**2)*x2 + (tval**3)*nx
                yt = ((1-tval)**3)*y + 3*((1-tval)**2)*tval*y1 + 3*(1-tval)*(tval**2)*y2 + (tval**3)*ny
                add_seg(px, py, xt, yt)
                px, py = xt, yt
            x, y = nx, ny
            i += 6
            continue

        if cmd in ("Z", "z"):
            add_seg(x, y, start_x, start_y)
            x, y = start_x, start_y
            i += 1
            continue

        i += 1

    return segments


# ------------------------------------------------------------
# Geometry helpers
# ------------------------------------------------------------

def bbox_of_segments(segments):
    xs = [s[0] for s in segments] + [s[2] for s in segments]
    ys = [s[1] for s in segments] + [s[3] for s in segments]
    return min(xs), max(xs), min(ys), max(ys)


def tiny_segment_count(segments, thresh=0.5):
    return sum(
        1 for (x1, y1, x2, y2) in segments
        if math.hypot(x2 - x1, y2 - y1) < thresh
    )


# ------------------------------------------------------------
# Geometry-based classification (only for base shapes)
# ------------------------------------------------------------

def classify_base_shape(segments):
    """
    Use geometry ONLY to decide between sun / moon / cloud / none.
    Everything else (rain/snow/fog/thunder/wind) comes from filename.
    """
    if not segments:
        return None

    x_min, x_max, y_min, y_max = bbox_of_segments(segments)
    w = x_max - x_min
    h = y_max - y_min
    if h == 0:
        return None

    ratio = w / h
    tiny = tiny_segment_count(segments)

    # Heuristics from your dumps:
    # - sun: round-ish (ratio ~1.0), many tiny segments
    # - cloud: wide (ratio > ~1.4), many tiny segments
    # - moon: round-ish but fewer segments than sun
    if tiny > 200 and 0.85 <= ratio <= 1.15:
        return "sun"
    if tiny > 150 and ratio > 1.4:
        return "cloud"
    if tiny > 80 and 0.85 <= ratio <= 1.15:
        return "moon"

    return None


# ------------------------------------------------------------
# Filename-based classification (precipitation / effects)
# ------------------------------------------------------------

def classify_from_filename(path: str):
    """
    Use the Weather Icons filename to infer rain/snow/fog/thunder/wind.
    This is reliable and necessary because geometry merges everything.
    """
    name = Path(path).name.lower()

    groups = set()

    if "day" in name:
        groups.add("sun")
    if "night" in name or "moon" in name:
        groups.add("moon")

    if "cloud" in name:
        groups.add("cloud")

    if "rain" in name or "showers" in name or "sprinkle" in name:
        groups.add("rain")

    if "snow" in name or "sleet" in name or "hail" in name:
        groups.add("snow")

    if "fog" in name or "haze" in name:
        groups.add("fog")

    if "storm" in name or "thunder" in name or "lightning" in name:
        groups.add("thunder")

    if "wind" in name:
        groups.add("wind")

    return groups


# ------------------------------------------------------------
# Main entry point
# ------------------------------------------------------------

def analyze_svg(path):
    """
    Returns (tree, groups) where groups is:
        { "sun": [elements...], "cloud": [...], ... }

    Strategy:
    - Use geometry to decide base shape (sun/moon/cloud).
    - Use filename to add rain/snow/fog/thunder/wind (and sun/moon/cloud hints).
    - Merge both, but never try to detect precipitation from geometry.
    """
    tree = ET.parse(path)
    root = tree.getroot()

    # Start with empty groups
    groups = {k: [] for k in GROUPS}

    # 1) Filename-based groups (logical, not per-element yet)
    filename_groups = classify_from_filename(str(path))

    # 2) Geometry-based base shape detection
    all_segments = []
    for elem in root.iter():
        if not elem.tag.lower().endswith("path"):
            continue
        d = elem.attrib.get("d", "")
        if not d:
            continue
        segs = parse_path(d)
        all_segments.extend(segs)

    base_shape = classify_base_shape(all_segments)
    # If filename indicates night, never classify as sun
    if "night" in str(path).lower():
        if base_shape == "sun":
            base_shape = "moon"

    # 3) Decide final logical groups
    logical_groups = set()

    # Base shape from geometry wins if present
    if base_shape == "sun":
        logical_groups.add("sun")
    elif base_shape == "moon":
        logical_groups.add("moon")
    elif base_shape == "cloud":
        logical_groups.add("cloud")

    # Merge filename groups
    logical_groups |= filename_groups

    # 4) Assign all <path> elements to the logical groups
    #    We don't try to split per-shape; Weather Icons merge shapes anyway.
    elements = [e for e in root.iter() if e.tag.lower().endswith("path")]
    for g in logical_groups:
        groups[g].extend(elements)

    return tree, groups
