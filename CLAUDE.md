# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**VueOSD — Digital FPV OSD Tool** overlays MSP-OSD telemetry data onto FPV DVR video footage using a Python/PyQt6 GUI with an FFmpeg backend. It parses `.osd` binary files or `.srt` subtitle telemetry, renders OSD glyphs via NumPy+Pillow, and pipes the result to FFmpeg for GPU-accelerated encoding (NVENC, AMF, QSV, VAAPI, VideoToolbox).

## Running the Application

```bash
# Windows (auto-installs deps on first run)
"VueOSD.bat"

# Linux/macOS (creates venv, installs deps, launches)
chmod +x run.sh && ./run.sh

# Direct Python launch (after deps installed)
python main.py
```

## Building Distributables

```bash
# Windows → dist/VueOSD.exe
build.bat

# Linux/macOS → dist/VueOSD
./build.sh
```

Both scripts use PyInstaller. FFmpeg must be on PATH.

## Dependencies

- **Python 3.10+** required
- `pip install -r requirements.txt` — installs PyQt6, Pillow, NumPy
- **FFmpeg** must be on PATH (Windows: auto-installed via `winget` through `bootstrap.py`)
- No test framework, no linter configured

## Architecture

The application is a pipeline: parse → render → pipe → encode.

```
main.py (PyQt6 GUI)
    │
    ├── osd_parser.py      — Binary .osd format parser (timestamp-indexed, bisect lookup)
    ├── p1_osd_parser.py   — BetaFPV P1 MP4 embedded OSD extraction
    ├── srt_parser.py      — .srt subtitle telemetry parser (speed, alt, sats, signal)
    ├── font_loader.py     — OSD font sheet loader (Betaflight/INAV/ArduPilot HD fonts)
    │
    ├── osd_renderer.py    — Composites OSD glyph grid + SRT bar → PNG (NumPy+PIL)
    │
    ├── video_processor.py — Orchestrates FFmpeg subprocess; auto-detects GPU encoders
    │
    ├── theme.py           — Dark/light palette definitions; persists to theme_custom.json
    ├── theme_editor.py    — In-app theme customization dialog
    └── splash_screen.py   — Animated progress screen (used during encoding)
```

**Critical rendering path:** Python renders OSD-only PNG frames (~1 ms/frame) and pipes them to a concurrently running FFmpeg process that decodes the video, applies the overlay filter, and GPU-encodes the output. Python is never in the per-frame hot loop with FFmpeg.

## Key Implementation Details

**GPU encoder detection** (`video_processor.py`): Tests NVENC → AMF → QSV → VAAPI → VideoToolbox → libx264. NVIDIA detection has a 20-second timeout for CUDA context initialization. Results are cached at startup.

**OSD parsing** (`osd_parser.py`): Binary format with timestamp-indexed frames; uses `bisect` for O(log n) frame lookup by video timestamp.

**Font system** (`font_loader.py`): Supports multi-column HD font sheets. Fonts live in `fonts/` with prefixes: `BTFL_` (Betaflight), `INAV` (INAV), `ARDU_` (ArduPilot). Quicksilver is not supported.

**Theme system** (`theme.py`): 16-color token system (backgrounds, surfaces, text, accent, status, borders). User overrides stored in `theme_custom.json` at runtime.

**Bootstrap flow** (`bootstrap.py`): On Windows, re-launches as `pythonw.exe` to hide the console, creates a venv, installs requirements, and auto-installs FFmpeg via `winget`. Only runs when the packaged `.bat` launcher is used.

**Firmware auto-detection** (`main.py` `_load_osd()`): Reads the 4-byte FC type tag from the OSD header (`BTFL` → Betaflight, `INAV` → INAV, `ARDU` → ArduPilot) and calls `_on_fw_changed()` directly. Unknown tags fall back to Betaflight. There is no firmware selector in the UI.

**Preview placeholder** (`PreviewPanel`, `main.py`): When no video is loaded, draws a Quick Start panel using `QPainter` on a `QPixmap` sized to the actual widget dimensions. Includes a pixel-art heart and donation link at the bottom (hidden when the widget is too short). Click zones are stored in `self._donate_rects` and hit-tested in `mousePressEvent`/`mouseMoveEvent`.

**Windows taskbar integration** (`main.py`): Sets `AppUserModelID` via ctypes for proper icon display.
