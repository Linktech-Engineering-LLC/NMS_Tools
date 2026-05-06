#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Leon McClatchey, Linktech Engineering LLC
"""
File: fixtures.py
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
from pathlib import Path

FIXTURE_DIR = Path(__file__).parent / "fixtures"

def load(name: str):
    """Load an SVG fixture by filename."""
    return FIXTURE_DIR / name
