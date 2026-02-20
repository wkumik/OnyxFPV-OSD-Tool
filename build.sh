#!/usr/bin/env bash
# VueOSD — Digital FPV OSD Tool — Linux / macOS standalone build
# Produces a single executable in dist/ that needs no Python installed.

set -e
cd "$(dirname "$0")"

VENV=".venv"

echo "=================================================="
echo " VueOSD — Build standalone binary"
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
    --name "VueOSD" \
    --add-data "fonts:fonts" \
    --add-data "icons:icons" \
    --add-data "assets:assets" \
    --icon "assets/icon.png" \
    main.py

echo ""
if [ -f "dist/VueOSD" ]; then
    echo "✓ Built: dist/VueOSD"
    echo ""
    echo "Place ffmpeg alongside VueOSD, or ensure ffmpeg is on PATH."
    echo "Distribute the dist/VueOSD file — no Python needed on target machine."
else
    echo "✗ Build failed — check output above."
    exit 1
fi
