# -*- mode: python ; coding: utf-8 -*-
#
# Project: MGR-S (Multi-GPU Runtime System)
# File:    mgrs_app.spec  — PyInstaller build spec
# Author:  Jaspinder
#
# Build command (run from j:\GPU linking\ui\):
#   pyinstaller mgrs_app.spec --noconfirm
#
# Output: dist\mgrs_app\mgrs_app.exe
#

import os
import sys

# ── Paths ─────────────────────────────────────────────────────────────────────
HERE = os.path.dirname(os.path.abspath(SPEC))     # j:\GPU linking\ui
ROOT = os.path.join(HERE, "..")                   # j:\MGR-S
ICON = os.path.join(HERE, "resources", "mgrs_icon.ico")
LOG_DIR = os.path.join(ROOT, "logs")


# ── Analysis ──────────────────────────────────────────────────────────────────
a = Analysis(
    [os.path.join(HERE, "mgrs_gui.py")],
    pathex=[HERE],
    binaries=[],
    datas=[
        # Bundle all UI Python modules
        (os.path.join(HERE, "mgrs_core.py"),      "."),
        (os.path.join(HERE, "mgrs_monitor.py"),   "."),
        (os.path.join(HERE, "mgrs_scheduler.py"), "."),
        (os.path.join(HERE, "mgrs_memory.py"),    "."),
        (os.path.join(HERE, "mgrs_tray.py"),      "."),
        (ICON, "."),
        # Bundle a blank first_launch marker template
        (ICON, "installer\\resources"),
    ],
    hiddenimports=[
        "tkinter",
        "tkinter.ttk",
        "tkinter.scrolledtext",
        "tkinter.messagebox",
        # Optional — will be skipped gracefully if not available
        "pystray",
        "PIL",
        "PIL.Image",
        "PIL.ImageDraw",
        "psutil",
        "wmi",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "matplotlib.tests",
        "numpy.testing",
        "IPython",
        "jupyter",
        "scipy",
        "cv2",
    ],
    cipher=None,
    noarchive=False,
)

# ── Strip matplotlib font cache noise ─────────────────────────────────────────
a.datas = [d for d in a.datas if "mpl-data/sample_data" not in d[0]]

pyz = PYZ(a.pure, a.zipped_data, cipher=None)


# ── One-folder EXE (recommended — faster startup than one-file) ───────────────
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='mgrs_app',
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
    icon=ICON if os.path.exists(ICON) else None,
)
