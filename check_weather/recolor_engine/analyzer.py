#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Leon McClatchey, Linktech Engineering LLC
"""
File: analyzer.py
Author: Leon McClatchey
Company: Linktech Engineering LLC
Created: 2026-05-04
Modified: 2026-05-04
Required: Python 3.8+
Part of: NMS_Tools Monitoring Suite
License: MIT (see LICENSE for details)

Description: Description of this module

"""


# recolor_engine/analyzer.py

import xml.etree.ElementTree as ET

def analyze_svg(path):
    """
    Returns a dict mapping semantic group → list of XML elements.
    """
    tree = ET.parse(path)
    root = tree.getroot()

    groups = {
        "sun": [],
        "cloud": [],
        "rain": [],
        "snow": [],
        "thunder": [],
        "fog": [],
        "wind": []
    }

    for elem in root.iter():
        tag = elem.tag.lower()

        # SUN (circle only)
        if elem.tag.endswith("circle"):
            groups["sun"].append(elem)
            continue

        if not tag.endswith("path") and not tag.endswith("polygon"):
            continue

        d = elem.attrib.get("d", "")

        # CLOUD
        if "C" in d and "S" in d:
            groups["cloud"].append(elem)
            continue

        # RAIN (lowercase c, no Z)
        if "c" in d and "Z" not in d:
            groups["rain"].append(elem)
            continue

        # SNOW (snow.svg uses arc A)
        if "A" in d and d.strip().endswith("Z"):
            groups["snow"].append(elem)
            continue

        # SNOW (sleet.svg uses short C-curve)
        if "C" in d and d.strip().endswith("Z") and len(d) < 40:
            groups["snow"].append(elem)
            continue

        # THUNDER
        if d.count("L") >= 4:
            groups["thunder"].append(elem)
            continue

    return tree, groups
