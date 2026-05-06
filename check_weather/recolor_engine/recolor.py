#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Leon McClatchey, Linktech Engineering LLC
"""
File: recolor.py
Author: Leon McClatchey
Company: Linktech Engineering LLC
Created: 2026-05-04
Modified: 2026-05-06
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
    verified: dict of semantic groups → list of XML elements
    """
    # Remove all existing fills so nothing stays yellow
    for elem in tree.getroot().iter():
        if "fill" in elem.attrib:
            del elem.attrib["fill"]

    # --- SUN ---
    if verified["sun"]:
        apply_color(verified["sun"], SUN)

    # --- CLOUD ---
    if verified["cloud"]:
        # If snow is present, clouds get the snow-cloud color
        if verified["snow"]:
            apply_color(verified["cloud"], CLOUD_SNOW)
        else:
            apply_color(verified["cloud"], CLOUD_RAIN)

    # --- RAIN ---
    if verified["rain"]:
        apply_color(verified["rain"], RAIN)

    # --- SNOW ---
    if verified["snow"]:
        apply_color(verified["snow"], SNOW)

    # --- THUNDER ---
    if verified["thunder"]:
        apply_color(verified["thunder"], THUNDER)

    # --- FOG ---
    if verified["fog"]:
        apply_color(verified["fog"], FOG)

    # --- WIND ---
    if verified["wind"]:
        apply_color(verified["wind"], WIND)

    # --- FALLBACK ---
    # Any element not recolored yet gets cloud color (neutral base)
    for elem in tree.getroot().iter():
        if "fill" not in elem.attrib or elem.attrib["fill"] in ("", None):
            elem.attrib["fill"] = CLOUD_RAIN

    return tree