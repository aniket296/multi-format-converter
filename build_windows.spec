# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller specification for standalone Windows executable MultiFormatConverter.exe."""

from PyInstaller.utils.hooks import collect_data_files

block_cipher = None

docx_datas = collect_data_files("docx")

a = Analysis(
    ["src/main.py"],
    pathex=["."],
    binaries=[],
    datas=[
        ("assets/app_icon.ico", "assets"),
        *docx_datas,
    ],
    hiddenimports=[
        "fitz",
        "pymupdf",
        "docx",
        "markdown",
        "markdown.extensions.tables",
        "markdown.extensions.fenced_code",
        "markdown.extensions.sane_lists",
        "bs4",
        "striprtf",
        "striprtf.striprtf",
        "PIL",
        "PIL.Image",
        "PIL.ImageDraw",
        "dotenv",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "onnxruntime",
        "pymupdf4llm",
        "pymupdf_layout",
        "pytest",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="MultiFormatConverter",
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
    icon="assets/app_icon.ico",
)
