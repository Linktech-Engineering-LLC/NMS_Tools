#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Leon McClatchey, Linktech Engineering LLC
"""
File: test_integration.py
Author: Leon McClatchey
Company: Linktech Engineering LLC
Created: 2026-05-04
Modified: 2026-05-06
Required: Python 3.8+
Part of: NMS_Tools Monitoring Suite
License: MIT (see LICENSE for details)

Description: Description of this module

"""


import xml.etree.ElementTree as ET
from check_weather.recolor_engine.analyzer import analyze_svg
from check_weather.recolor_engine.classifier import classify_from_filename
from check_weather.recolor_engine.recolor import recolor
from .fixtures import load


def extract_colors(svg_tree):
    """Return all fill colors found in the SVG."""
    colors = set()
    for elem in svg_tree.iter():
        fill = elem.attrib.get("fill")
        if fill:
            colors.add(fill.lower())
    return colors


def run_pipeline(name: str):
    path = load(name)            # returns PosixPath
    _, groups = analyze_svg(path)  # analyze_svg expects a path

    parsed = ET.parse(path)        # recolor expects a parsed tree
    classified = classify_from_filename(name)
    recolored = recolor(parsed, groups, classified)

    return sorted([g for g, elems in groups.items() if elems]), classified, recolored


def test_integration_rain():
    detected, classified, recolored = run_pipeline("rain.svg")

    assert detected == ["cloud", "rain"]
    assert classified == ["cloud", "rain"]

    colors = extract_colors(recolored)
    assert any("#" in c for c in colors)  # recolor applied something


def test_integration_snow():
    detected, classified, recolored = run_pipeline("snow.svg")

    assert detected == ["cloud", "snow"]
    assert classified == ["cloud", "snow"]

    colors = extract_colors(recolored)
    assert any("#" in c for c in colors)


def test_integration_thunder():
    detected, classified, recolored = run_pipeline("thunder.svg")

    assert detected == ["cloud", "thunder"]
    assert classified == ["cloud", "thunder"]

    colors = extract_colors(recolored)
    assert any("#" in c for c in colors)


def test_integration_sunny():
    detected, classified, recolored = run_pipeline("day-sunny.svg")

    assert detected == ["sun"]
    assert classified == ["sun"]

    colors = extract_colors(recolored)
    assert any("#" in c for c in colors)


def test_integration_sleet():
    detected, classified, recolored = run_pipeline("sleet.svg")

    # sleet = snow + rain
    assert sorted(detected) == ["rain", "snow"]
    assert sorted(classified) == ["rain", "snow"]

    colors = extract_colors(recolored)
    assert any("#" in c for c in colors)
