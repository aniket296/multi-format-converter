@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo ============================================================================
echo   Multi-Format Document Batch Converter - Local Studio Launcher
echo ============================================================================

if not exist ".venv\Scripts\python.exe" (
    echo [1/3] Creating local Python virtual environment ^(.venv^)...
    python -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment. Ensure Python 3.11+ is installed and on PATH.
        exit /b 1
    )
    echo [2/3] Installing runtime dependencies from requirements.txt...
    ".venv\Scripts\pip.exe" install --upgrade pip
    ".venv\Scripts\pip.exe" install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Failed to install dependencies.
        exit /b 1
    )
)

if not exist "assets\app_icon.ico" (
    echo [INFO] Generating application icon asset...
    ".venv\Scripts\python.exe" scripts\generate_icon.py
)

echo [3/3] Launching Multi-Format Document Batch Converter Studio...
".venv\Scripts\python.exe" -m src.main
exit /b %ERRORLEVEL%
