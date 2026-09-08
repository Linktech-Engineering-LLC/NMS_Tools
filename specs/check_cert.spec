# -*- mode: python ; coding: utf-8 -*-
import os
import pathlib

project_root = pathlib.Path(__file__).resolve().parents[1]
version_file = project_root / "VERSION"

block_cipher = None

repo_root = os.getcwd()

a = Analysis(
    [os.path.join(repo_root, 'src/check_cert/check_cert.py')],
    pathex=[os.path.join(repo_root, 'src/check_cert')],
    binaries=[],
    datas=[("../VERSION", "VERSION")],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
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
    name='check_cert',
    debug=False,
    strip=False,
    upx=False,
    console=True,
    distpath='build/linux-x86_64',
    workpath='build/temp',
)
