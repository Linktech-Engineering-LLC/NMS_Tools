#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Leon McClatchey, Linktech Engineering LLC
"""
File: build.py
Author: Leon McClatchey
Company: Linktech Engineering LLC
Created: 2026-07-08
Modified: 2026-07-08
Required: Python 3.8+
Part of: NMS_Tools Monitoring Suite
License: MIT (see LICENSE for details)

Description: Description of this module

"""

import os
import sys
import sysconfig
import toml
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_NAME = Path(sys.argv[0]).stem
SCRIPT_VERSION = "1.0.0"

# ------------------------------------------------------------
# Tool discovery
# ------------------------------------------------------------
def discover_tools(src_dir="src"):
    tools = []
    for entry in os.listdir(src_dir):
        tool_dir = os.path.join(src_dir, entry)
        tool_script = os.path.join(tool_dir, f"{entry}.py")
        if os.path.isdir(tool_dir) and os.path.isfile(tool_script):
            tools.append(entry)
    return tools

def load_config():
    return toml.load(ROOT / "build.toml")

# ------------------------------------------------------------
# Asset collector (only NMS_Tools assets)
# ------------------------------------------------------------
def collect_assets(tool_dir):
    assets = []
    for root, dirs, files in os.walk(tool_dir):
        for f in files:
            if f.endswith(".py"):
                assets.append((os.path.join(root, f), os.path.relpath(root, tool_dir)))
    return assets

def generate_spec(tool_name, cfg, log=None):
    src_dir = ROOT / cfg["src_dir"] / tool_name
    script_path = src_dir / f"{tool_name}.py"
    spec_path = ROOT / f"{tool_name}.spec"
    python_tools_src = Path(os.path.expanduser("~/projects/Python/PythonTools"))

    pathex = [
        str(src_dir),
        sysconfig.get_paths()["purelib"]
    ]

    # Only add editable source path if it exists (local dev)
    if python_tools_src.exists():
        pathex.append(str(python_tools_src))

    # Convert list → Python literal for spec file
    pathex_literal = "[" + ", ".join(f"'{p}'" for p in pathex) + "]"

    datas = collect_assets(src_dir)
    binaries = []

    # Special case: easysnmp C-extension
    if tool_name == "check_interfaces":
        import easysnmp
        easysnmp_dir = Path(easysnmp.__file__).parent
        for f in easysnmp_dir.glob("*.so"):
            binaries.append((str(f), "easysnmp"))

    spec_content = f"""
# -*- mode: python ; coding: utf-8 -*-
import os
block_cipher = None

a = Analysis(
    ['{script_path}'],
    pathex={pathex_literal},
    binaries={binaries},
    datas={datas},
    hiddenimports=[],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='{tool_name}',
    debug=False,
    strip=False,
    upx=False,
    console=True,
    distpath='{cfg["build_dir"]}/linux-x86_64',
    workpath='{cfg["build_dir"]}/temp',
)
"""
    spec_path.write_text(spec_content)
    msg = f"[+] Generated spec for {tool_name}"
    log.info(msg) if log else print(msg)

# ------------------------------------------------------------
# Freeze
# ------------------------------------------------------------
def freeze_tool(tool_name, log=None):
    msg = f"[+] Freezing {tool_name}..."
    log.info(msg) if log else print(msg)
    subprocess.run(["pyinstaller", f"{tool_name}.spec"], check=True)

# ------------------------------------------------------------
# Logging
# ------------------------------------------------------------
def init_log():
    log_cfg = {
        "path": os.path.expanduser(f"~/logs/{SCRIPT_NAME}.log"),
        "log_level": "INFO",
        "log_max_mb": 5,
        "max_age_days": 30,
        "backup_count": 5,
        "archive_mode": "zip",
        "console_enabled": True,
        "color": False,
    }
    from PythonTools.log_helpers.factory import LoggerFactory
    logger_factory = LoggerFactory(log_cfg, "build")
    return logger_factory.get_logger("main")

# ------------------------------------------------------------
# Main
# ------------------------------------------------------------
def main():
    cfg = load_config()
    tools = discover_tools()

    log = init_log()
    log.info("[+] Building tools...")

    for tool in tools:
        generate_spec(tool, cfg, log)
        freeze_tool(tool, log)

    log.info("[+] All tools frozen successfully.")

if __name__ == "__main__":
    main()
