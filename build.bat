@echo off
setlocal EnableDelayedExpansion
cd /d "%~dp0"
title OnyxFPV OSD Tool - Build

echo ==============================================
echo  OnyxFPV OSD Tool  -  Build standalone .exe
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
    --name "OnyxFPVOSDTool" ^
    --add-data "fonts;fonts" ^
    --add-data "icons;icons" ^
    --icon "icon.ico" ^
    main.py

echo.
if exist "dist\OnyxFPVOSDTool.exe" (
    echo [SUCCESS] dist\OnyxFPVOSDTool.exe
    echo.
    echo Place ffmpeg.exe alongside OnyxFPVOSDTool.exe
    echo Distribute dist\OnyxFPVOSDTool.exe -- no Python needed on target machine.
) else (
    echo [ERROR] Build failed -- check output above.
)
pause
