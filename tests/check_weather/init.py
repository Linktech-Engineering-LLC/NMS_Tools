#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Leon McClatchey, Linktech Engineering LLC
"""
File: init.py
Author: Leon McClatchey
Company: Linktech Engineering LLC
Created: 2026-09-02
Modified: 2026-09-02
Required: Python 3.8+
Part of: NMS_Tools Monitoring Suite
License: MIT (see LICENSE for details)

Description: Description of this module

"""
from .test_indexes import (
    test_heat_index_valid,
    test_heat_index_invalid_low_rh,
    test_heat_index_invalid_low_temp,
    test_humidex_valid,
    test_compute_all_indexes,
    test_wet_bulb_valid,
    test_wind_chill_invalid_high_temp,
    test_wind_chill_invalid_low_wind,
    test_wind_chill_valid,
)
WEATHER = {
    "valid_heat": test_heat_index_valid,
    "heat_low_rh": test_heat_index_invalid_low_rh,
    "heat_low_temp": test_heat_index_invalid_low_temp,
    "valid_humidex": test_humidex_valid,
    "all_indexes": test_compute_all_indexes,
    "valid_wet_bulb": test_wet_bulb_valid,
    "wind_chill_high_temp": test_wind_chill_invalid_high_temp,
    "wind_chill_low_wind": test_wind_chill_invalid_low_wind,
    "valid_wind_chill": test_wind_chill_valid,
}

