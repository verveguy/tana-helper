# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules

hiddenimports = []
hiddenimports += collect_submodules('service')


start_a = Analysis(
    ['start.py'],
    pathex=['service'],
    binaries=[],
    datas=[('service/dist', 'service/dist'), ('icons', 'icons')],
    hiddenimports=[collect_submodules('service')]
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
start_pyz = PYZ(a.pure)

start_exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='start',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='tanahelper',
)
