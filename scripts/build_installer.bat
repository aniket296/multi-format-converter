@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0\.."

echo ============================================================================
echo   Multi-Format Document Batch Converter - Windows Installer Build Pipeline
echo ============================================================================

call "%~dp0build_exe.bat"
if errorlevel 1 (
    echo [ERROR] Standalone executable build failed. Cannot proceed to installer step.
    exit /b 1
)

set "ISCC_PATH="

if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" (
    set "ISCC_PATH=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
) else if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" (
    set "ISCC_PATH=%ProgramFiles%\Inno Setup 6\ISCC.exe"
) else if exist "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" (
    set "ISCC_PATH=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
) else (
    for /f "delims=" %%I in ('where ISCC.exe 2^>nul') do (
        if not defined ISCC_PATH set "ISCC_PATH=%%I"
    )
)

if defined ISCC_PATH (
    echo [INFO] Found Inno Setup Compiler at: "!ISCC_PATH!"
    echo [INFO] Compiling Windows Setup Wizard ^(installer\setup.iss^)...
    "!ISCC_PATH!" "installer\setup.iss"
    if errorlevel 1 (
        echo [ERROR] Inno Setup compilation failed.
        exit /b 1
    )
    echo ============================================================================
    echo   [SUCCESS] Windows Installer created: dist_installer\MultiFormatConverter_Setup.exe
    echo ============================================================================
    exit /b 0
) else (
    echo.
    echo ============================================================================
    echo   [NOTICE] Inno Setup 6 ^(ISCC.exe^) was not detected on this machine.
    echo   Standalone portable binary is ready at: dist\MultiFormatConverter.exe
    echo   To compile the Windows Setup Wizard ^(MultiFormatConverter_Setup.exe^),
    echo   install Inno Setup 6 from: https://jrsoftware.org/isdl.php
    echo ============================================================================
    exit /b 0
)
