#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Leon McClatchey, Linktech Engineering LLC
"""
File: bump_version.py
Author: Leon McClatchey
Company: Linktech Engineering LLC
Created: 2026-04-25
Modified: 2026-04-25
Required: Python 3.8+
Part of: NMS_Tools Monitoring Suite
License: MIT (see LICENSE for details)

Description: 
    bump_version.py
    Bumps the NMS_Tools suite version in the VERSION file.
Usage:
    python3 tools/bump_version.py patch
    python3 tools/bump_version.py minor
    python3 tools/bump_version.py major
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VERSION_FILE = ROOT / "VERSION"


def read_version():
    return VERSION_FILE.read_text().strip()


def write_version(v):
    VERSION_FILE.write_text(v + "\n")


def bump(version, part):
    major, minor, patch = map(int, version.split("."))

    if part == "patch":
        patch += 1
    elif part == "minor":
        minor += 1
        patch = 0
    elif part == "major":
        major += 1
        minor = 0
        patch = 0
    else:
        raise ValueError(f"Unknown bump type: {part}")

    return f"{major}.{minor}.{patch}"


def main():
    if len(sys.argv) != 2:
        print("Usage: bump_version.py [major|minor|patch]")
        sys.exit(1)

    part = sys.argv[1].lower()
    if part not in ("major", "minor", "patch"):
        print("ERROR: bump type must be one of: major, minor, patch")
        sys.exit(1)

    old = read_version()
    new = bump(old, part)

    write_version(new)

    print(f"[version] Old version: {old}")
    print(f"[version] New version: {new}")


if __name__ == "__main__":
    main()
