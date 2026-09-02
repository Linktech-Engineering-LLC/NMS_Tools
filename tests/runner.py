#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Leon McClatchey, Linktech Engineering LLC
"""
File: runner.py
Author: Leon McClatchey
Company: Linktech Engineering LLC
Created: 2026-09-02
Modified: 2026-09-02
Required: Python 3.8+
Part of: NMS_Tools Monitoring Suite
License: MIT (see LICENSE for details)

Description: Description of this module

"""

import os
import sys
import traceback
import time
import platform

# Import the LoggerFactory
from PythonTools.log_helpers.factory import LoggerFactory

# Import test modules explicitly
# (You will add more as you expand the harness)
from check_weather.test_indexes import (
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
HARNESS = {
    "Weather Index": WEATHER,
    # "HTML": HTML,
    # "Interfaces": INTERFACES,
    # "Cert": CERT,
}

# ---------------------------------------------------------------------------
# Logger Initialization
# ---------------------------------------------------------------------------
def initialize_harness_logger():
    """
    Deterministic logger for the NMS_Tools test harness.
    Uses the same LoggerFactory identity as all tools.
    """

    script_name = os.path.splitext(os.path.basename(__file__))[0]

    log_dir = os.path.join(os.getcwd(), "logs")
    os.makedirs(log_dir, exist_ok=True)

    log_cfg = {
        "path": os.path.join(log_dir, f"{script_name}.log"),
        "log_level": "INFO",
        "log_max_mb": 5,
        "archive_mode": "zip",
        "backup_count": 5,

        # Harness always logs to console
        "console_stream": sys.stderr,
        "console_enabled": True,

        # Harness does not use color
        "color": False,
    }

    factory = LoggerFactory(log_cfg, script_name)
    return factory.get_logger("harness")
def log_environment(logger):
    logger.info(f"Python: {platform.python_version()}")
    logger.info(f"OS: {platform.system()} {platform.release()}")
    logger.info(f"Machine: {platform.machine()}")
    logger.info(f"Working Directory: {os.getcwd()}")

# ---------------------------------------------------------------------------
# Test Runner Helpers
# ---------------------------------------------------------------------------
def run_group(logger, group_name, tests):
    logger.info(f"=== Running {group_name} Tests ===")
    results = []

    for name, func in tests.items():
        results.append(run_test(name, func, logger))

    passed = sum(1 for r in results if r)
    failed = len(results) - passed

    logger.info(f"=== {group_name} Summary: {passed} passed, {failed} failed ===")
    return results

def run_test(name, func, logger):
    start = time.perf_counter()
    logger.info(f"Running test: {name}")

    try:
        func()
        duration = time.perf_counter() - start
        logger.info(f"PASS: {name} ({duration:.4f}s)")
        return True

    except Exception as e:
        duration = time.perf_counter() - start
        logger.error(f"FAIL: {name} ({duration:.4f}s) error={e}")
        logger.error(traceback.format_exc())
        return False


# ---------------------------------------------------------------------------
# Main Harness Execution
# ---------------------------------------------------------------------------

def main():
    
    logger = initialize_harness_logger()
    logger.info("=== Starting NMS_Tools Test Harness ===")
    log_environment(logger)
    
    results = []

    for group_name, tests in HARNESS.items():
        results.extend(run_group(logger, group_name, tests))

    # Add more tests here as you expand the harness
    # results.append(run_test("check_html.test_structure", test_structure))
    # results.append(run_test("check_interfaces.test_parsing", test_parsing))

    # Summary
    passed = sum(1 for r in results if r)
    failed = len(results) - passed

    logger.info(f"=== Harness Complete: {passed} passed, {failed} failed ===")

    # Exit code for CI or operator use
    os._exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
