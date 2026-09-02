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
import inspect
import json
import traceback
import time
import platform
from dataclasses import dataclass
from pathlib import Path
from _pytest.monkeypatch import MonkeyPatch

# Add project root to sys.path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Import the LoggerFactory
from PythonTools.log_helpers.factory import LoggerFactory
from PythonTools.nagios import BaseNagiosParser
from PythonTools.color import colorize, Color
from PythonTools.test import display_results

# Import test modules explicitly
# (You will add more as you expand the harness)
from check_html.init import HTML
from check_ticker.init import TICKER
from check_weather.init import WEATHER

@dataclass
class TestResult:
    name: str
    group: str
    passed: bool
    duration: float
    error: str | None = None
        
HARNESS = {
    "Weather Index": WEATHER,
    "HTML Core": HTML,
    "Ticker API Keys": TICKER,
    # "Interfaces": INTERFACES,
    # "Cert": CERT,
}
def parse_cli() -> BaseNagiosParser:
    parser = BaseNagiosParser(
        prog="runner",
        description="NMS_Tools Deterministic Test Harness"
    )

    # Use add_group(), just like check_ticker
    group = parser.add_group("Harness Options")

    group.add_argument(
        "--group",
        default=None,
        help="Run only a specific test group (Weather, HTML, Ticker)"
    )

    group.add_argument(
        "--list",
        action="store_true",
        help="List available test groups"
    )
    group.add_argument(
        "--fail-fast",
        action="store_true",
        help="Stop after the first failed test"
    )

    group.add_argument(
        "--pattern",
        help="Run only tests whose names contain this substring"
    )

    args, flags, mode = parser.parse()
    return args, flags, mode
# ---------------------------------------------------------------------------
# Logger Initialization
# ---------------------------------------------------------------------------
def initialize_harness_logger(args):
    """
    Deterministic logger for the NMS_Tools test harness.
    Mirrors the structure of tool loggers but without Nagios mode.
    Falls back to harness defaults when no log-dir is provided.
    """

    # If user did not specify a log-dir, use harness default
    log_dir = args.log_dir or os.path.join(os.getcwd(), "logs")
    os.makedirs(log_dir, exist_ok=True)

    script_name = "runner"

    log_cfg = {
        "path": os.path.join(log_dir, f"{script_name}.log"),
        "log_level": "INFO",
        "log_max_mb": args.log_max_mb or 5,
        "archive_mode": "zip",
        "backup_count": 5,

        # Console output only when verbose AND not quiet
        "console_stream": sys.stderr,
        "console_enabled": args.verbose and not args.quiet,

        # Color only when user requests it
        #"color": args.color,
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
def run_group(group_name, tests, args, logger):
    logger.info("=== Running {group_name} Tests ===")
    results = []

    for name, func in tests.items():

        # Pattern filtering
        if args.pattern and args.pattern not in name:
            continue

        # Run the test → returns TestResult
        result = run_test(name, func, group_name)
        results.append(result)

        # Fail-fast
        if args.fail_fast and not result.passed:
            logger.error("Fail-fast enabled: stopping early")
            break

    # Compute group summary
    passed = sum(1 for r in results if r.passed)
    failed = len(results) - passed

    # Log summary (plain text only)
    logger.info(f"=== {group_name} Summary: {passed} passed, {failed} failed ===")

    return results

def run_test(name, func, group_name):
    start = time.perf_counter()

    try:
        sig = inspect.signature(func)
        params = sig.parameters

        if "monkeypatch" in params:
            mp = MonkeyPatch()
            func(mp)
            mp.undo()
        else:
            func()

        duration = time.perf_counter() - start
        return TestResult(name=name, group=group_name, passed=True, duration=duration)

    except Exception as e:
        duration = time.perf_counter() - start
        return TestResult(name=name, group=group_name, passed=False, duration=duration, error=str(e))

   

# ---------------------------------------------------------------------------
# Main Harness Execution
# ---------------------------------------------------------------------------

def main():
    args, flags, mode = parse_cli()
    if mode == "nagios":
        mode = "quiet"
    logger = initialize_harness_logger(args)
    logger.info("=== Starting NMS_Tools Test Harness ===")
    log_environment(logger)
    logger.info(f"Command Line: {' '.join(sys.argv)}")
    
    if args.list:
        logger.info("Available test groups:")
        for name in HARNESS.keys():
            logger.info(f" - {name}")
        os._exit(0)

    all_results = []
    # Determine which groups to run
    if args.group:
        if args.group not in HARNESS:
            logger.error(f"Unknown group: {args.group}")
            os._exit(1)

        groups_to_run = {args.group: HARNESS[args.group]}
    else:
        groups_to_run = HARNESS

    for group_name, tests in groups_to_run.items():
        group_results = run_group(group_name, tests, args, logger)
        all_results.extend(group_results)

        if args.fail_fast and any(not r.passed for r in group_results):
            break

    passed = sum(1 for r in all_results if r.passed)
    failed = len(all_results) - passed

    display_results(all_results, args)

    logger.info(f"=== Harness Complete: {passed} passed, {failed} failed ===")


    # Always exit with a code
    os._exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
