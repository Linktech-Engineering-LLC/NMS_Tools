# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Leon McClatchey, Linktech Engineering LLC
"""
 Package: PythonTools
 Author: Leon McClatchey
 Company: Linktech Engineering LLC
Created: 2026-08-10
Modified: 2026-08-28
 File: ~/projects/NMS_Tools/tests/test_indexes.py
 Version: 1.0.0
 Description: Tests the Weather Indexes
"""


import pytest

from PythonTools.weather.indexes import (
    compute_heat_index,
    compute_wind_chill,
    compute_humidex,
    compute_wet_bulb,
    compute_all_indexes,
)


def test_heat_index_valid():
    # NWS reference: T=90°F, RH=70% → HI ≈ 105°F
    assert compute_heat_index(90, 70) == pytest.approx(105, abs=1)


def test_heat_index_invalid_low_temp():
    assert compute_heat_index(75, 60) is None


def test_heat_index_invalid_low_rh():
    assert compute_heat_index(90, 30) is None


def test_wind_chill_valid():
    # NWS reference: T=30°F, wind=10 mph → WC ≈ 21°F
    assert compute_wind_chill(30, 10) == pytest.approx(21, abs=1)


def test_wind_chill_invalid_high_temp():
    assert compute_wind_chill(55, 10) is None


def test_wind_chill_invalid_low_wind():
    assert compute_wind_chill(30, 2) is None


def test_humidex_valid():
    # Environment Canada reference: T=30°C, dewpoint=20°C → Humidex ≈ 40
    assert compute_humidex(30, 20) == pytest.approx(37.5, abs=1)


def test_wet_bulb_valid():
    # Stull approximation reference: T=30°C, RH=70% → Tw ≈ 24°C
    assert compute_wet_bulb(30, 70) == pytest.approx(24, abs=2)


def test_compute_all_indexes():
    idx = compute_all_indexes(
        temp_f=90,
        temp_c=32.2,
        dewpoint_c=22,
        rh=70,
        wind_mph=10,
    )

    assert idx.heat_index is not None
    assert idx.wind_chill is None  # too warm for wind chill
    assert idx.humidex is not None
    assert idx.wet_bulb is not None
