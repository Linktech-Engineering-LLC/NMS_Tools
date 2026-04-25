#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Leon McClatchey, Linktech Engineering LLC
"""
File: vendor_builder.py
Author: Leon McClatchey
Company: Linktech Engineering LLC
Created: 2026-04-25
Modified: 2026-04-25
Required: Python 3.8+
Part of: NMS_Tools Monitoring Suite
License: MIT (see LICENSE for details)

Description: 
    Builds the suite-level vendor directory (libs/) by copying installed
    packages from the active virtual environment's site-packages.

"""

import sys
import shutil
import site
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LIBS_DIR = ROOT / "libs"
REQ_FILE = ROOT / "requirements.txt"

NAME_MAP = {
    "python-dateutil": "dateutil",
    "charset-normalizer": "charset_normalizer",
}


def find_site_packages():
    """Return the site-packages directory for the active interpreter."""
    for p in site.getsitepackages():
        if "site-packages" in p:
            return Path(p)
    # fallback for virtualenvs
    return Path(site.getusersitepackages())


def parse_requirements():
    """Return a list of top-level package names from requirements.txt."""
    pkgs = []
    for line in REQ_FILE.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        pkg = line.split("==")[0].strip()
        pkgs.append(pkg)
    return pkgs


def copy_package(pkg_name, site_pkgs):
    """
    Copy a package directory or module file from site-packages into libs/.
    Handles both:
        - package directories (requests/, urllib3/, etc.)
        - single-file modules (six.py, dateutil/__init__.py, etc.)
    """
    real_name = NAME_MAP.get(pkg_name, pkg_name)

    candidates = [
        site_pkgs / real_name,
        site_pkgs / f"{real_name}.py",
    ]

    for c in candidates:
        if c.exists():
            dest = LIBS_DIR / c.name
            if c.is_dir():
                shutil.copytree(c, dest, dirs_exist_ok=True)
            else:
                shutil.copy2(c, dest)
            print(f"[vendor] Copied: {c.name}")
            return True

    print(f"[vendor] WARNING: {pkg_name} not found in site-packages")
    return False


def main():
    print("[vendor] Building suite-level vendor directory...")

    site_pkgs = find_site_packages()
    print(f"[vendor] Using site-packages: {site_pkgs}")

    if LIBS_DIR.exists():
        shutil.rmtree(LIBS_DIR)
    LIBS_DIR.mkdir()

    pkgs = parse_requirements()
    print(f"[vendor] Packages to vendor: {pkgs}")

    for pkg in pkgs:
        copy_package(pkg, site_pkgs)

    print("[vendor] Vendor build complete.")


if __name__ == "__main__":
    main()
