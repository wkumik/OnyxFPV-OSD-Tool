#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
VENV=".venv"

find_python() {
    for cmd in python3.13 python3.12 python3.11 python3.10 python3 python; do
        if command -v "$cmd" &>/dev/null; then
            if "$cmd" -c "import sys; exit(0 if sys.version_info>=(3,10) else 1)" 2>/dev/null; then
                echo "$cmd"; return 0
            fi
        fi
    done
    return 1
}

PYTHON=$(find_python 2>/dev/null) || true
if [ -z "$PYTHON" ]; then
    echo "Python 3.10+ not found. Install with: sudo apt install python3 python3-venv"
    read -p "Press Enter..." 2>/dev/null || true; exit 1
fi
echo "Python: $($PYTHON --version 2>&1)"

if [ ! -f "$VENV/bin/python" ]; then
    echo "Creating virtual environment..."
    # --without-pip avoids the pip-download hang seen on some systems
    "$PYTHON" -m venv --without-pip "$VENV" || {
        echo "venv failed. Try: sudo apt install python3-venv"; exit 1
    }
    "$VENV/bin/python" -m ensurepip --upgrade
fi

if ! "$VENV/bin/python" -c "import PyQt6, PIL, numpy" 2>/dev/null; then
    echo "Installing dependencies (first run only)..."
    "$VENV/bin/python" -m pip install -r requirements.txt
fi

echo "Starting VueOSD — Digital FPV OSD Tool..."
exec "$VENV/bin/python" main.py
