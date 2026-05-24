# check_weather.spec
# Lean PyInstaller spec file for monitoring-only builds of check_weather

import os
from PyInstaller.utils.hooks import collect_submodules

# Base path to the check_weather source folder
SRC_BASE = os.path.abspath("src/check_weather")

# Collect all Python submodules inside the check_weather package
hidden_imports = collect_submodules("check_weather")

block_cipher = None

a = Analysis(
    [os.path.join(SRC_BASE, "check_weather.py")],
    pathex=[SRC_BASE],
    binaries=[],
    datas=[
        # No assets included — monitoring build does not need web, svg, docs, or recolor engine
    ],
    hiddenimports=hidden_imports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[]
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    name="check_weather",
    debug=False,
    strip=False,
    upx=True,
    console=True
)
