#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Leon McClatchey, Linktech Engineering LLC
"""
File: test_recolor.py
Author: Leon McClatchey
Company: Linktech Engineering LLC
Created: 2026-05-04
Modified: 2026-05-06
Required: Python 3.8+
Part of: NMS_Tools Monitoring Suite
License: MIT (see LICENSE for details)

Description: Description of this module

"""


# recolor_engine/tests/test_recolor.py

import os
from check_weather.recolor_engine.analyzer import analyze_svg
from check_weather.recolor_engine.recolor import recolor
from check_weather.recolor_engine.palette import CLOUD_RAIN, CLOUD_SNOW
from .fixtures import load

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")

#def load(name):
#    return os.path.join(FIXTURES, name)

def test_recolor_snow_cloud():
    tree, groups = analyze_svg(load("cloud.svg"))
    recolor(tree, groups, ["cloud", "snow"])
    cloud_elems = groups["cloud"]
    assert all(elem.attrib.get("fill") == CLOUD_SNOW for elem in cloud_elems)

def test_recolor_rain_cloud():
    tree, groups = analyze_svg(load("cloud.svg"))
    recolor(tree, groups, ["cloud", "rain"])
    cloud_elems = groups["cloud"]
    assert all(elem.attrib.get("fill") == CLOUD_RAIN for elem in cloud_elems)
