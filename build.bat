@echo off
setlocal EnableDelayedExpansion
cd /d "%~dp0"
title VueOSD - Build

echo ==============================================
echo  VueOSD  -  Build standalone .exe
echo ==============================================
echo.

:: Activate venv (run.bat must have been run at least once)
if not exist ".venv\Scripts\activate.bat" (
    echo No venv found. Run run.bat once first to set up dependencies.
    pause
    exit /b 1
)

call .venv\Scripts\activate.bat

echo Installing PyInstaller...
python -m pip install --quiet pyinstaller

echo.
echo Building...
pyinstaller ^
    --onefile ^
    --windowed ^
    --name "VueOSD" ^
    --add-data "fonts;fonts" ^
    --add-data "icons;icons" ^
    --add-data "assets;assets" ^
    --icon "assets\icon.ico" ^
    main.py

echo.
if exist "dist\VueOSD.exe" (
    echo [SUCCESS] dist\VueOSD.exe
    echo.
    echo Place ffmpeg.exe alongside VueOSD.exe
    echo Distribute dist\VueOSD.exe -- no Python needed on target machine.
) else (
    echo [ERROR] Build failed -- check output above.
)
pause
