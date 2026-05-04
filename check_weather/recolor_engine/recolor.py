#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Leon McClatchey, Linktech Engineering LLC
"""
File: recolor.py
Author: Leon McClatchey
Company: Linktech Engineering LLC
Created: 2026-05-04
Modified: 2026-05-04
Required: Python 3.8+
Part of: NMS_Tools Monitoring Suite
License: MIT (see LICENSE for details)

Description: Description of this module

"""


# recolor_engine/recolor.py

from .palette import *

def apply_color(elements, color):
    for elem in elements:
        elem.attrib["fill"] = color

def recolor(tree, verified, expected):
    """
    expected: list of semantic groups from filename
    verified: dict of semantic groups → elements
    """
    # SUN
    if "sun" in expected:
        apply_color(verified["sun"], SUN)

    # CLOUDS
    if "cloud" in expected:
        if "snow" in expected:
            apply_color(verified["cloud"], CLOUD_SNOW)
        else:
            apply_color(verified["cloud"], CLOUD_RAIN)

    # RAIN
    if "rain" in expected:
        apply_color(verified["rain"], RAIN)

    # SNOW
    if "snow" in expected:
        apply_color(verified["snow"], SNOW)

    # THUNDER
    if "thunder" in expected:
        apply_color(verified["thunder"], THUNDER)

    # FOG
    if "fog" in expected:
        apply_color(verified["fog"], FOG)

    # WIND
    if "wind" in expected:
        apply_color(verified["wind"], WIND)

    return tree
