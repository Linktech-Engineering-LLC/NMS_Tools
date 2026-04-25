#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Leon McClatchey, Linktech Engineering LLC
"""
File: validate_env.py
Author: Leon McClatchey
Company: Linktech Engineering LLC
Created: 2026-04-25
Modified: 2026-04-25
Required: Python 3.8+
Part of: NMS_Tools Monitoring Suite
License: MIT (see LICENSE for details)

Description: 
    validate_env.py
    Performs preflight validation for building or installing the NMS_Tools suite.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REQUIRED_PYTHON = (3, 8)


def check_python_version():
    if sys.version_info < REQUIRED_PYTHON:
        print(f"[env] ERROR: Python {REQUIRED_PYTHON[0]}.{REQUIRED_PYTHON[1]}+ required.")
        sys.exit(1)
    print(f"[env] Python version OK: {sys.version.split()[0]}")


def check_venv():
    if sys.prefix == sys.base_prefix:
        print("[env] WARNING: Not running inside a virtual environment.")
        print("[env] This is fine for installation, but required for building.")
    else:
        print("[env] Virtual environment detected.")


def check_file(path, name):
    if not path.exists():
        print(f"[env] ERROR: Missing required file: {name}")
        sys.exit(1)
    print(f"[env] Found: {name}")


def check_dir(path, name):
    if not path.exists():
        print(f"[env] WARNING: Missing directory: {name}")
    else:
        print(f"[env] Found: {name}")


def main():
    print("[env] Validating NMS_Tools environment...")

    check_python_version()
    check_venv()

    check_file(ROOT / "requirements.txt", "requirements.txt")
    check_file(ROOT / "VERSION", "VERSION")

    check_dir(ROOT / "libs", "libs/")
    check_dir(ROOT / "check_weather", "check_weather/")
    check_dir(ROOT / "check_cert", "check_cert/")
    check_dir(ROOT / "check_html", "check_html/")

    print("[env] Environment validation complete.")


if __name__ == "__main__":
    main()
