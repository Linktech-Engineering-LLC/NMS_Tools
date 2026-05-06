#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Leon McClatchey, Linktech Engineering LLC
"""
File: test_analyzer.py
Author: Leon McClatchey
Company: Linktech Engineering LLC
Created: 2026-05-04
Modified: 2026-05-06
Required: Python 3.8+
Part of: NMS_Tools Monitoring Suite
License: MIT (see LICENSE for details)

Description: Description of this module

"""


# recolor_engine/tests/test_analyzer.py

import os
from check_weather.recolor_engine.analyzer import analyze_svg
from .test_recolor import load

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")

#def load(name):
#    return os.path.join(FIXTURES, name)

def test_analyzer_sun():
    _, groups = analyze_svg(load("sun.svg"))
    detected = [g for g, elems in groups.items() if elems]
    assert "sun" in detected

def test_analyzer_cloud():
    _, groups = analyze_svg(load("cloud.svg"))
    detected = [g for g, elems in groups.items() if elems]
    assert "cloud" in detected

def test_analyzer_rain():
    _, groups = analyze_svg(load("rain.svg"))
    detected = [g for g, elems in groups.items() if elems]
    assert "rain" in detected
    assert "cloud" in detected

def test_analyzer_snow():
    _, groups = analyze_svg(load("snow.svg"))
    detected = [g for g, elems in groups.items() if elems]
    assert "snow" in detected
    assert "cloud" in detected

def test_analyzer_thunder():
    _, groups = analyze_svg(load("thunder.svg"))
    detected = [g for g, elems in groups.items() if elems]
    assert "thunder" in detected
    assert "cloud" in detected
