# -*- mode: python ; coding: utf-8 -*-

# BUILD UNSIGNED .APP BUNDLES FOR CURRENT ARCH
# We will assemble them into a universal, signed bundle later

import platform
from PyInstaller.building.api import PYZ, EXE, COLLECT

plat = platform.system()

from PyInstaller.utils.hooks import collect_data_files
from PyInstaller.utils.hooks import collect_submodules
from PyInstaller.utils.hooks import collect_all
from PyInstaller.utils.hooks import copy_metadata

title = 'Tana Helper'
name = 'tanahelper'

start_datas = []
start_binaries = []
start_hiddenimports = []

start_hiddenimports += collect_submodules('service')

start_datas += [('service/dist', 'service/dist'), 
    ('icons', 'icons'), 
    ('service/bin', 'service/bin'),
     ('service/scripts', 'service/scripts')]


# chromadb needs things that aren't detected
# automatically by pyinstaller
start_hiddenimports += ['hnswlib']

for meta in ['opentelemetry-sdk']:
    start_datas += copy_metadata(meta)


start_a = Analysis(
    ['start.py'],
    pathex=['service'],
    binaries=start_binaries,
    datas=start_datas,
    hiddenimports=start_hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

start_pyz = PYZ(start_a.pure)

start_exe = EXE(
    start_pyz,
    start_a.scripts,
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

helper_a = Analysis(
    ['tanahelper.py'],
    pathex=[],
    binaries=[],
    datas = [('icons','icons')],
    hiddenimports=['pkgutil'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
helper_pyz = PYZ(helper_a.pure)

icon=None
if plat == 'Windows':
    icon=['icons/TanaHelper.ico']

helper_exe = EXE(
    helper_pyz,
    helper_a.scripts,
    [],
    exclude_binaries=True,
    name=name,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon,
)

coll = COLLECT( 
    helper_exe,
    start_exe,
    helper_a.binaries,
    helper_a.zipfiles,
    helper_a.datas,
    start_a.binaries,
    start_a.zipfiles,
    start_a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name=name,
)

# BUILD .app on MAC ONLY
if plat == 'Darwin':
    app = BUNDLE(
        coll,
        name=f'{title}.app',
        icon=f'icons/{title}.icns',
        bundle_identifier='com.v3rv.app.Tana-Helper',
    )