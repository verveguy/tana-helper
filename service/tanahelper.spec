# -*- mode: python ; coding: utf-8 -*-

version = '0.2.1' # TODO: get this from the build environment

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
# Note: llama-index now uses modular structure, so we need llama_index.core instead
# Note: hnswlib is provided by chroma-hnswlib, transformers is not actually used
hidden_imports += ['tiktoken_ext.openai_public', 'tiktoken_ext', 'llama_index.core']

# Add ChromaDB-specific dependencies
hidden_imports += ['chromadb.api.models.Collection', 'chromadb.config']

# Add OpenTelemetry dependencies that ChromaDB needs
hidden_imports += ['opentelemetry.instrumentation', 'opentelemetry.instrumentation.requests']

# Copy metadata for required packages
for meta in ['opentelemetry-sdk', 'opentelemetry-api', 'tqdm', 'regex', 'requests', 'llama_index', 'llama_index_core', 'chromadb']:
  try:
    datas += copy_metadata(meta)
  except Exception:
    # Skip if package not found
    pass

# Modern llama-index uses modular structure - no need for specific VERSION files
# The old structure with VERSION and _static files no longer exists

# Only collect ChromaDB since transformers is not used
for coll in ['chromadb']:
  try:
    stuff = collect_all(coll)
    datas += stuff[0]
    binaries += stuff[1]
    hidden_imports += stuff[2]
  except Exception:
    # Skip if package collection fails
    pass

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
  excludes=['tkinter', 'matplotlib', 'FixTk', 'tcl', 'tk', '_tkinter', 'tkinter.constants', 'Tkinter'],
  noarchive=False,
)

pyz = PYZ(analysis.pure)



# NOW BUILD HELPER APP
    
icon=None
console=False
if plat == 'Windows':
  icon=['icons/TanaHelper.ico']
  console=False

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
  console=console,
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
    info_plist={
      'LSBackgroundOnly': True,
    },
  )

