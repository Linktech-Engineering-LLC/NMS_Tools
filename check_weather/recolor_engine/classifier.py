#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Leon McClatchey, Linktech Engineering LLC
"""
File: classifier.py
Author: Leon McClatchey
Company: Linktech Engineering LLC
Created: 2026-05-04
Modified: 2026-05-04
Required: Python 3.8+
Part of: NMS_Tools Monitoring Suite
License: MIT (see LICENSE for details)

Description: Description of this module

"""

# recolor_engine/classifier.py

def classify_from_filename(name: str):
    name = name.lower()
    groups = []

    if "sun" in name or "day" in name:
        groups.append("sun")

    if "rain" in name:
        groups.append("cloud")
        groups.append("rain")

    if "snow" in name:
        groups.append("cloud")
        groups.append("snow")

    if "sleet" in name:
        groups.append("snow")
        groups.append("rain")

    if "thunder" in name or "storm" in name:
        groups.append("cloud")
        groups.append("thunder")

    return groups
