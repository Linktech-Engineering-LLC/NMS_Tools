#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Leon McClatchey, Linktech Engineering LLC
"""
File: build_suite.py
Author: Leon McClatchey
Company: Linktech Engineering LLC
Created: 2026-04-25
Modified: 2026-04-25
Required: Python 3.8+
Part of: NMS_Tools Monitoring Suite
License: MIT (see LICENSE for details)

Description: 
    build_suite.py
    Packages the NMS_Tools suite into a distributable tarball.

    Assumes vendor_builder.py has already populated libs/.
"""

import tarfile
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
LIBS = ROOT / "libs"
VERSION_FILE = ROOT / "VERSION"

def read_version():
    return VERSION_FILE.read_text().strip()
VERSION = read_version()

def main():
    print("[build] Building NMS_Tools suite package...")

    if not LIBS.exists():
        raise SystemExit("[build] ERROR: libs/ does not exist. Run vendor_builder.py first.")

    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir()

    tar_path = DIST / f"NMS_Tools-{VERSION}.tar.gz"

    with tarfile.open(tar_path, "w:gz") as tar:
        tar.add(ROOT, arcname="NMS_Tools", filter=lambda x: None)

    print(f"[build] Package created: {tar_path}")


if __name__ == "__main__":
    main()
