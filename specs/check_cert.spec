# -*- mode: python ; coding: utf-8 -*-
import os
block_cipher = None

repo_root = os.getcwd()

a = Analysis(
    [os.path.join(repo_root, 'src/check_cert/check_cert.py')],
    pathex=[os.path.join(repo_root, 'src/check_cert')],
    binaries=[],
    datas=[],
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
