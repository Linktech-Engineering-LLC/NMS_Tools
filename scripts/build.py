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
import toml
import subprocess
from pathlib import Path

# build.py lives in NMS_Tools/scripts, so ROOT is one directory up
ROOT = Path(__file__).resolve().parents[1]

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

def collect_assets(src_dir):
    """Collect all asset files under src/<tool>/assets."""
    assets_dir = src_dir / "assets"
    datas = []

    if assets_dir.exists():
        for root, dirs, files in os.walk(assets_dir):
            for f in files:
                full_path = Path(root) / f
                rel_path = full_path.relative_to(src_dir)
                datas.append((str(full_path), str(rel_path)))
    return datas

def generate_spec(tool_name, cfg):
    src_dir = ROOT / cfg["src_dir"] / tool_name
    script_path = src_dir / f"{tool_name}.py"

    spec_path = ROOT / f"{tool_name}.spec"

    python_tools = ROOT / cfg["PythonTools"]

    # Base datas: PythonTools injection
    datas = [
        (str(python_tools / "VERSION"), "PythonTools"),
        (str(python_tools / "PythonTools"), "PythonTools/PythonTools"),
        (str(python_tools / "PythonTools" / "ansible"), "PythonTools/PythonTools/ansible"),
        (str(python_tools / "PythonTools" / "core"), "PythonTools/PythonTools/core"),
        (str(python_tools / "PythonTools" / "utils"), "PythonTools/PythonTools/utils"),
    ]

    # Add assets if present (check_weather, future tools)
    datas.extend(collect_assets(src_dir))

    hiddenimports = [
        "PythonTools",
        "PythonTools.ansible",
        "PythonTools.core",
        "PythonTools.utils",
    ]

    spec_content = f"""
# -*- mode: python ; coding: utf-8 -*-
import os
block_cipher = None

repo_root = os.getcwd()

a = Analysis(
    ['{script_path}'],
    pathex=['{src_dir}', '{python_tools}'],
    binaries=[],
    datas={datas},
    hiddenimports={hiddenimports},
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
    print(f"[+] Generated spec for {tool_name}")

def freeze_tool(tool_name):
    print(f"[+] Freezing {tool_name}...")
    subprocess.run(["pyinstaller", f"{tool_name}.spec"], check=True)

def main():
    cfg = load_config()

    TOOLS = discover_tools()

    for tool in TOOLS:
        generate_spec(tool, cfg)
        freeze_tool(tool)

    print("[+] All tools frozen successfully.")

if __name__ == "__main__":
    main()
