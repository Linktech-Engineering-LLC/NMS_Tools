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
#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Leon McClatchey, Linktech Engineering LLC

import os
import sys
import toml
import subprocess
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTOOLS_DIR = ROOT / "PythonTools"
SCRIPT_NAME = Path(sys.argv[0]).stem
SCRIPT_VERSION = "1.0.0"

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
# -------------------------------
# AST‑based PythonTools dependency scanner
# -------------------------------
def scan_imports(pyfile: Path):
    """Return all PythonTools.* imports found in a Python file."""
    deps = set()
    tree = ast.parse(pyfile.read_text())

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.module and node.module.startswith("PythonTools"):
                deps.add(node.module)

        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith("PythonTools"):
                    deps.add(alias.name)

    return deps
def collect_python_tools(python_tools):
    assets = []
    root_dir = python_tools / "PythonTools"
    for root, dirs, files in os.walk(root_dir):
        for f in files:
            if f.endswith(".py"):
                full = os.path.join(root, f)
                rel = os.path.relpath(root, python_tools)
                assets.append((full, f"PythonTools/{rel}"))
    return assets
def collect_python_tools_dependencies(tools, cfg):
    """Scan all tools and collect PythonTools.* dependencies."""
    src_root = ROOT / cfg["src_dir"]
    deps = set()

    for tool in tools:
        tool_dir = src_root / tool
        for pyfile in tool_dir.glob("*.py"):
            deps.update(scan_imports(pyfile))

    return deps
# -------------------------------
# PythonTools sync + verification
# -------------------------------
def sync_python_tools():
    """Ensure PythonTools repo exists and is up to date."""
    if not PYTOOLS_DIR.exists():
        print("[+] Cloning PythonTools...")
        subprocess.run([
            "git", "clone",
            "https://github.com/LinktechEngineering/PythonTools.git",
            str(PYTOOLS_DIR)
        ], check=True)
    else:
        print("[+] Pulling PythonTools updates...")
        subprocess.run(["git", "-C", str(PYTOOLS_DIR), "pull"], check=True)
def verify_python_tools_modules(deps, log=None):
    """Verify that required PythonTools modules exist."""
    missing = []

    for module in deps:
        parts = module.split(".")
        rel_path = PYTOOLS_DIR / "/".join(parts)  # e.g. PythonTools/market/trend
        module_file = rel_path.with_suffix(".py")
        package_init = rel_path / "__init__.py"

        if not module_file.exists() and not package_init.exists():
            missing.append(str(rel_path))

    if missing:
        msg = "[!] Missing PythonTools modules:"
        for m in missing:
            msg += f"\n\t-{m}"
        log.error(msg) if log else print(msg)
        raise RuntimeError("PythonTools sync failed: missing modules remain.")
# -------------------------------
# Asset collector + spec generator
# -------------------------------
def collect_assets(tool_dir):
    assets = []
    for root, dirs, files in os.walk(tool_dir):
        for f in files:
            # Only include Python source files
            if f.endswith(".py"):
                assets.append((os.path.join(root, f), os.path.relpath(root, tool_dir)))
    return assets
def generate_spec(tool_name, cfg, log=None):
    src_dir = ROOT / cfg["src_dir"] / tool_name
    script_path = src_dir / f"{tool_name}.py"
    spec_path = ROOT / f"{tool_name}.spec"

    python_tools = PYTOOLS_DIR

    datas = [
        (str(python_tools / "VERSION"), "PythonTools"),
    ]
    datas.extend(collect_python_tools(python_tools))
    datas.extend(collect_assets(src_dir))

    hiddenimports = ["PythonTools"]

    binaries = []

    # ------------------------------------------------------------
    # Special case: check_interfaces requires easysnmp C-extension
    # ------------------------------------------------------------
    if tool_name == "check_interfaces":
        import easysnmp
        import os

        easysnmp_dir = Path(easysnmp.__file__).parent
        for f in easysnmp_dir.glob("*.so"):
            binaries.append((str(f), "easysnmp"))

    spec_content = f"""
# -*- mode: python ; coding: utf-8 -*-
import os
block_cipher = None

repo_root = os.getcwd()

a = Analysis(
    ['{script_path}'],
    pathex=['{src_dir}', '{python_tools}'],
    binaries={binaries},
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
    msg = f"[+] Generated spec for {tool_name}"
    log.info(msg) if log else print(msg)
def freeze_tool(tool_name, log=None):
    msg = f"[+] Freezing {tool_name}..."
    log.info(msg) if log else print(msg)
    subprocess.run(["pyinstaller", f"{tool_name}.spec"], check=True)
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
# -------------------------------
# Main build flow
# -------------------------------
def main():
    cfg = load_config()
    tools = discover_tools()
    print("[+] Syncing PythonTools...")
    sync_python_tools()
    log = init_log()

    log.info("[+] Scanning PythonTools dependencies...")
    deps = collect_python_tools_dependencies(tools, cfg)

    
    log.info("[+] Verifying PythonTools modules...")
    verify_python_tools_modules(deps, log)

    log.info("[+] Building tools...")
    for tool in tools:
        generate_spec(tool, cfg, log)
        freeze_tool(tool, log)

    log.info("[+] All tools frozen successfully.")

if __name__ == "__main__":
    main()
