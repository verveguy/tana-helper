# -*- mode: python ; coding: utf-8 -*-

version = '0.2.0' # TODO: get this from the build environment

# BUILD UNSIGNED .APP BUNDLES FOR CURRENT ARCH
# We will assemble them into a universal, signed bundle later

import platform
from PyInstaller.building.api import PYZ, EXE, COLLECT
from PyInstaller.building.build_main import Analysis

plat = platform.system()
if plat == 'Darwin':
  from PyInstaller.building.osx import BUNDLE

from PyInstaller.utils.hooks import collect_data_files
from PyInstaller.utils.hooks import collect_submodules
from PyInstaller.utils.hooks import collect_all
from PyInstaller.utils.hooks import copy_metadata

helper_title = 'TanaHelper'
helper_name = 'tanahelpermenu'

service_title = 'TanaHelperService'
service_name = 'tanahelperservice'

# FIRST BUILD THE SERVICE PACKAGE
service_datas = []
service_binaries = []
service_hiddenimports = []

service_hiddenimports += ['service.small_main', 'service.main']

service_hiddenimports += collect_submodules('service')

service_datas += [
  ('service/dist', 'service/dist'), 
  ('icons', 'icons'), 
  ('service/bin', 'service/bin'),
  ('service/scripts', 'service/scripts')]


# chromadb, llamindex and ollama need things that aren't detected
# automatically by pyinstaller
service_hiddenimports += ['hnswlib', 'tiktoken_ext.openai_public', 'tiktoken_ext', 'llama_index']

for meta in ['opentelemetry-sdk', 'tqdm', 'regex', 'requests', 'llama_index']:
  service_datas += copy_metadata(meta)

# llamaindex is really picky about package metadata...
if plat == 'Windows':
  service_datas += [('.venv/lib/site-packages/llama_index/VERSION', 'llama_index/')]
else:
  service_datas += [('.venv/lib/python3.11/site-packages/llama_index/VERSION', 'llama_index/')]
  service_datas += [('.venv/lib/python3.11/site-packages/llama_index/_static', 'llama_index/_static')]

for coll in ['transformers', 'chromadb']:
    stuff = collect_all(coll)
    service_datas += stuff[0]
    service_binaries += stuff[1]
    service_hiddenimports += stuff[2]

service_a = Analysis(
    ['start.py'],
    pathex=['service'],
    binaries=service_binaries,
    datas=service_datas,
    hiddenimports=service_hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

service_pyz = PYZ(service_a.pure)

service_exe = EXE(
    service_pyz,
    service_a.scripts,
    [],
    exclude_binaries=True,
    name=service_name,
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

if plat == 'Darwin':

  service_coll = COLLECT( 
    service_exe,
    service_a.binaries,
    service_a.zipfiles,
    service_a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name=service_name,
  )

  service_app = BUNDLE(
    service_coll,
    name=f'{service_title}.app',
    version=version,
    icon=f'icons/{service_title}.icns',
    bundle_identifier='com.v3rv.app.Tana-Helper-Service',
  )


# NOW BUILD HELPER APP
    
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
  name=helper_name,
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

# WINDOWS BUILD IS A UNIFIED BUILD OF BOTH APPS
if plat == 'Windows':

    coll = COLLECT( 
        helper_exe,
        service_exe,
        helper_a.binaries,
        helper_a.zipfiles,
        helper_a.datas,
        service_a.binaries,
        service_a.zipfiles,
        service_a.datas,
        strip=False,
        upx=True,
        upx_exclude=[],
        name=helper_name,
    )

# BUILD TWO .app on MAC ONLY
elif plat == 'Darwin':
    # actually, just build one binary
    helper_coll = COLLECT( 
        helper_exe,
        service_exe,
        helper_a.binaries,
        helper_a.zipfiles,
        helper_a.datas,
        service_a.binaries,
        service_a.zipfiles,
        service_a.datas,
        strip=False,
        upx=True,
        upx_exclude=[],
        name=helper_name,
    )

    helper_app = BUNDLE(
        helper_coll,
        name=f'{helper_title}.app',
        version=version,
        icon=f'icons/{helper_title}.icns',
        bundle_identifier='com.v3rv.app.Tana-Helper',
    )
