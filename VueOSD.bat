@echo off
cd /d "%~dp0"
title VueOSD — Digital FPV OSD Tool

set SFPATH=%TEMP%\vueosd_splash.txt

:: ── Write initial status and launch HTA splash immediately ───────────────────
echo 2>&1>"%SFPATH%" 5
echo Starting^&hellip;>>"%SFPATH%"
start "" mshta.exe "%~dp0splash.hta"

:: ── Check for Python ──────────────────────────────────────────────────────────
set PYTHON=
py --version >nul 2>&1 && set PYTHON=py
if "%PYTHON%"=="" python --version >nul 2>&1 && set PYTHON=python

:: ── Install Python if missing ─────────────────────────────────────────────────
if "%PYTHON%"=="" (
    echo 12>"%SFPATH%"
    echo Installing Python 3^&hellip;>>"%SFPATH%"
    winget install --id Python.Python.3.13 --source winget --accept-package-agreements --accept-source-agreements >nul 2>&1

    echo 40>"%SFPATH%"
    echo Python installed, restarting^&hellip;>>"%SFPATH%"

    :: Try to find it on the refreshed PATH
    py --version >nul 2>&1 && set PYTHON=py
    if "%PYTHON%"=="" python --version >nul 2>&1 && set PYTHON=python

    if "%PYTHON%"=="" (
        echo CLOSE>"%SFPATH%"
        echo.
        echo Python was installed but is not yet on PATH.
        echo Please close this window and double-click the bat again.
        pause
        exit /b 0
    )
)

:: ── Hand off to bootstrap — it closes the HTA and shows PyQt6 splash ─────────
echo 45>"%SFPATH%"
echo Loading app^&hellip;>>"%SFPATH%"

%PYTHON% "%~dp0bootstrap.py"

if %ERRORLEVEL% neq 0 (
    echo CLOSE>"%SFPATH%"
    echo.
    echo ERROR: App failed to start. See any error window that appeared.
    pause
)
