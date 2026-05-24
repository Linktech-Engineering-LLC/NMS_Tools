#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Leon McClatchey, Linktech Engineering LLC
"""
File: run_tests.py
Author: Leon McClatchey
Company: Linktech Engineering LLC
Created: 2026-05-04
Modified: 2026-05-06
Required: Python 3.8+
Part of: NMS_Tools Monitoring Suite
License: MIT (see LICENSE for details)

Description: Description of this module

"""
# recolor_engine/tests/run_tests.py

import os
import sys

# Make sure the recolor_engine package is importable
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, BASE_DIR)

from check_weather.recolor_engine.classifier import classify_from_filename
from check_weather.recolor_engine.analyzer import analyze_svg
from check_weather.recolor_engine.recolor import recolor
from check_weather.recolor_engine.palette import SUN, CLOUD_RAIN, CLOUD_SNOW, RAIN, SNOW, THUNDER

TEST_DIR = os.path.dirname(__file__)
FIXTURES = os.path.join(TEST_DIR, "fixtures")


def test_classifier():
    print("\n=== CLASSIFIER TESTS ===")

    tests = {
        "day-sunny.svg": ["sun"],
        "rain.svg": ["cloud", "rain"],
        "snow.svg": ["cloud", "snow"],
        "sleet.svg": ["snow", "rain"],
        "thunderstorm.svg": ["cloud", "thunder"],
    }

    for name, expected in tests.items():
        result = classify_from_filename(name)
        if result == expected:
            print(f"[PASS] {name} → {result}")
        else:
            print(f"[FAIL] {name} → {result}, expected {expected}")


def test_analyzer():
    print("\n=== ANALYZER TESTS ===")

    fixture_files = [
        "sun.svg",
        "cloud.svg",
        "rain.svg",
        "snow.svg",
        "thunder.svg",
    ]

    for fname in fixture_files:
        path = os.path.join(FIXTURES, fname)
        try:
            _, groups = analyze_svg(path)
            detected = [g for g, elems in groups.items() if elems]
            print(f"[PASS] {fname} → detected: {detected}")
        except Exception as e:
            print(f"[FAIL] {fname} → error: {e}")


def test_recolor():
    print("\n=== RECOLOR TESTS ===")

    # Use cloud.svg fixture to test cloud recoloring
    cloud_svg = os.path.join(FIXTURES, "cloud.svg")
    tree, groups = analyze_svg(cloud_svg)

    # Test snow cloud recoloring
    recolor(tree, groups, ["cloud", "snow"])
    cloud_elems = groups["cloud"]
    if all(elem.attrib.get("fill") == CLOUD_SNOW for elem in cloud_elems):
        print("[PASS] snow cloud recolor → CLOUD_SNOW")
    else:
        print("[FAIL] snow cloud recolor")

    # Test rain cloud recoloring
    tree, groups = analyze_svg(cloud_svg)
    recolor(tree, groups, ["cloud", "rain"])
    cloud_elems = groups["cloud"]
    if all(elem.attrib.get("fill") == CLOUD_RAIN for elem in cloud_elems):
        print("[PASS] rain cloud recolor → CLOUD_RAIN")
    else:
        print("[FAIL] rain cloud recolor")


def main():
    print("Running recolor_engine test harness...\n")
    test_classifier()
    test_analyzer()
    test_recolor()
    print("\nDone.\n")


if __name__ == "__main__":
    main()

