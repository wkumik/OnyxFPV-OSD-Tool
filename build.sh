#!/usr/bin/env bash
# OnyxFPV OSD Tool — Linux / macOS standalone build
# Produces a single executable in dist/ that needs no Python installed.

set -e
cd "$(dirname "$0")"

VENV=".venv"

echo "=================================================="
echo " OnyxFPV OSD Tool — Build standalone binary"
echo "=================================================="
echo ""

# Activate venv (run.sh must have been run at least once)
if [ ! -f "$VENV/bin/activate" ]; then
    echo "No venv found. Run ./run.sh once first to set up dependencies."
    exit 1
fi
source "$VENV/bin/activate"

pip install --quiet pyinstaller

echo "Building..."
pyinstaller \
    --onefile \
    --windowed \
    --name "OnyxFPVOSDTool" \
    --add-data "fonts:fonts" \
    --add-data "icons:icons" \
    --icon "icon.png" \
    main.py

echo ""
if [ -f "dist/OnyxFPVOSDTool" ]; then
    echo "✓ Built: dist/OnyxFPVOSDTool"
    echo ""
    echo "Place ffmpeg alongside OnyxFPVOSDTool, or ensure ffmpeg is on PATH."
    echo "Distribute the dist/OnyxFPVOSDTool file — no Python needed on target machine."
else
    echo "✗ Build failed — check output above."
    exit 1
fi
