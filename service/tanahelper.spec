# -*- mode: python ; coding: utf-8 -*-

# BUILD UNSIGNED .APP BUNDLES FOR CURRENT ARCH
# We will assemble them into a universal, signed bundle later

import platform
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
start_datas += copy_metadata('opentelemetry-sdk')

tmp_ret = collect_all('chromadb')
start_datas += tmp_ret[0]
start_binaries += tmp_ret[1]
start_hiddenimports += tmp_ret[2]


tmp_ret = collect_all('transformers')
start_datas += tmp_ret[0]
start_binaries += tmp_ret[1]
start_hiddenimports += tmp_ret[2]


start_datas += [('.venv/lib/python3.11/site-packages/llama_index/VERSION', 'llama_index/')]

start_hiddenimports += collect_submodules('service')
start_hiddenimports += ['hnswlib']

start_datas += [('service/dist', 'service/dist'), 
    ('icons', 'icons'), 
    ('service/bin', 'service/bin'),
     ('service/scripts', 'service/scripts')]

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