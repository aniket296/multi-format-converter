@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0\.."

echo ============================================================================
echo   Multi-Format Document Batch Converter - Standalone .EXE Build Pipeline
echo ============================================================================

if not exist ".venv\Scripts\python.exe" (
    echo [INFO] Virtual environment not found. Creating .venv and installing dependencies...
    python -m venv .venv
    ".venv\Scripts\pip.exe" install -r requirements.txt pytest pyinstaller
)

echo [1/4] Running automated unit test suite ^(pytest^)...
".venv\Scripts\pytest.exe" -q
if errorlevel 1 (
    echo [ERROR] Unit tests failed! Aborting executable build.
    exit /b 1
)

echo [2/4] Generating multi-resolution application icon ^(assets\app_icon.ico^)...
".venv\Scripts\python.exe" scripts\generate_icon.py
if errorlevel 1 (
    echo [ERROR] Failed to generate application icon.
    exit /b 1
)

echo [3/4] Compiling standalone executable via PyInstaller...
".venv\Scripts\pyinstaller.exe" --noconfirm --clean build_windows.spec
if errorlevel 1 (
    echo [ERROR] PyInstaller build failed.
    exit /b 1
)

echo [4/4] Verifying output artifact...
if not exist "dist\MultiFormatConverter.exe" (
    echo [ERROR] Expected output binary dist\MultiFormatConverter.exe was not found!
    exit /b 1
)

echo ============================================================================
echo   [SUCCESS] Standalone executable built: dist\MultiFormatConverter.exe
echo ============================================================================
exit /b 0
