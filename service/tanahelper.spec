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

title = 'TanaHelper'
name = 'tanahelpermenu'

# FIRST BUILD THE SERVICE PACKAGE
datas = []
binaries = []
hidden_imports = []

hidden_imports += ['service.small_main', 'service.main', 'pkgutil']

hidden_imports += collect_submodules('service')

datas += [
  ('service/dist', 'service/dist'), 
  ('icons', 'icons'), 
  ('service/bin', 'service/bin'),
  ('service/scripts', 'service/scripts')]


# chromadb, llamindex and ollama need things that aren't detected
# automatically by pyinstaller
hidden_imports += ['hnswlib', 'tiktoken_ext.openai_public', 'tiktoken_ext', 'llama_index']

for meta in ['opentelemetry-sdk', 'tqdm', 'regex', 'requests', 'llama_index']:
  datas += copy_metadata(meta)

# llamaindex is really picky about package metadata...
if plat == 'Windows':
  datas += [('.venv/lib/site-packages/llama_index/VERSION', 'llama_index/')]
else:
  datas += [('.venv/lib/python3.11/site-packages/llama_index/VERSION', 'llama_index/')]
  datas += [('.venv/lib/python3.11/site-packages/llama_index/_static', 'llama_index/_static')]

for coll in ['transformers', 'chromadb']:
  stuff = collect_all(coll)
  datas += stuff[0]
  binaries += stuff[1]
  hidden_imports += stuff[2]

analysis = Analysis(
  ['tanahelper.py'],
  # pathex=['service'],
  pathex=[],
  binaries=binaries,
  datas=datas,
  hiddenimports=hidden_imports,
  hookspath=[],
  hooksconfig={},
  runtime_hooks=[],
  excludes=[],
  noarchive=False,
)

pyz = PYZ(analysis.pure)



# NOW BUILD HELPER APP
    
icon=None
if plat == 'Windows':
  icon=['icons/TanaHelper.ico']

exe = EXE(
  pyz,
  analysis.scripts,
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

# WINDOWS BUILD IS A UNIFIED BUILD OF BOTH APPS
if plat == 'Windows':

  coll = COLLECT( 
    exe,
    analysis.binaries,
    analysis.zipfiles,
    analysis.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name=name,
  )

# BUILD TWO .app on MAC ONLY
elif plat == 'Darwin':
  # actually, just build one binary
  coll = COLLECT( 
    exe,
    analysis.binaries,
    analysis.zipfiles,
    analysis.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name=name,
  )

  app = BUNDLE(
    coll,
    name=f'{title}.app',
    version=version,
    icon=f'icons/{title}.icns',
    bundle_identifier='com.v3rv.app.Tana-Helper',
  )
