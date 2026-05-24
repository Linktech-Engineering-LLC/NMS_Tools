#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Leon McClatchey, Linktech Engineering LLC
"""
File: test_classifier.py
Author: Leon McClatchey
Company: Linktech Engineering LLC
Created: 2026-05-04
Modified: 2026-05-06
Required: Python 3.8+
Part of: NMS_Tools Monitoring Suite
License: MIT (see LICENSE for details)

Description: Description of this module

"""


# recolor_engine/tests/test_classifier.py

import os
from check_weather.recolor_engine.classifier import classify_from_filename

def test_classifier_basic():
    tests = {
        "day-sunny.svg": ["sun"],
        "rain.svg": ["cloud", "rain"],
        "snow.svg": ["cloud", "snow"],
        "sleet.svg": ["snow", "rain"],
        "thunderstorm.svg": ["cloud", "thunder"],
    }

    for name, expected in tests.items():
        assert classify_from_filename(name) == expected
