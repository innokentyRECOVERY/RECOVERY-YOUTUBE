# -*- mode: python ; coding: utf-8 -*-
import os
import sys

# хвост от предыдущего .exe: PyInstaller считает tkinter сломанным и не кладёт его в сборку
for key in ("TCL_LIBRARY", "TK_LIBRARY", "TCLLIBPATH"):
    val = os.environ.get(key, "")
    if (not val) or ("_MEI" in val.replace("\\", "/")) or (not os.path.isdir(val)):
        os.environ.pop(key, None)

_prefix = getattr(sys, "base_prefix", sys.prefix)
_tcl = os.path.join(_prefix, "tcl", "tcl8.6")
_tk = os.path.join(_prefix, "tcl", "tk8.6")
if os.path.isdir(_tcl):
    os.environ["TCL_LIBRARY"] = _tcl
if os.path.isdir(_tk):
    os.environ["TK_LIBRARY"] = _tk

a = Analysis(
    ['G:/AAARECOVERY/RECOVERYYOUTUBE.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=["tkinter", "tkinter.messagebox", "tkinter.filedialog"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='RECOVERY_YOUTUBE',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version='G:/AAARECOVERY/version_info.txt',
    icon=['G:/AAARECOVERY/app_icon.ico'],
)
