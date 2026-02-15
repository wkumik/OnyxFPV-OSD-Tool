# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2025 OnyxFPV — https://github.com/onyxfpv
"""
font_loader.py  –  Discover and load OSD bitmap fonts from the bundled fonts/ directory.

Font sheet formats (confirmed from actual PNG measurements):

  ARDU / BTFL_DJI  SD: 36  × 54 px per tile, single column, 256 tiles tall
  ARDU / BTFL_DJI  HD: 24  × 36 px per tile, single column, 256 tiles tall

  BTFL (most)      SD: 144 × 54 px per tile sheet row, 256 rows
                       → 4 columns of 36px × 54px = chars 0-255, 256-511, 512-767, 768-1023
  BTFL (most)      HD: 96  × 36 px per tile sheet row, 256 rows
                       → 4 columns of 24px × 36px = chars 0-255, 256-511, 512-767, 768-1023

  INAV             SD: 72  × 54 px per tile, single column, 256 tiles tall
  INAV             HD: 48  × 36 px per tile, single column, 256 tiles tall

  INAV (some)      SD: 36  × 108 px per tile (2 rows per char?)
  INAV (some)      HD: 24  × 72  px per tile

  Quicksilver      HD: 48 × 36 px (single column)
                   SD: 72 × 54 px (single column)

Multi-column sheets: each sheet row contains N_COLS glyphs of base_tile_w × tile_h.
  char_code → col = code // 256, row = code % 256
  pixel_x   = col * base_tile_w
  pixel_y   = row * tile_h
"""

from __future__ import annotations
import os
from pathlib import Path
from typing import Optional, Dict, List, Tuple

try:
    from PIL import Image
    PIL_OK = True
except ImportError:
    PIL_OK = False

NUM_CHARS = 256   # rows in every font sheet

# Firmware prefixes used in folder names
FIRMWARE_PREFIXES: Dict[str, List[str]] = {
    "Betaflight": ["BTFL_", "BFx4_"],
    "INAV":       ["INAV"],
    "ArduPilot":  ["ARDU_"],
    "Quicksilver":["SNEAKY_FPV_QS_"],
}

_FONTS_DIR = Path(__file__).parent / "fonts"

_HD_FILENAMES = ("font_btfl_hd.png", "font_inav_hd.png", "font_ardu_hd.png", "font_quic_hd.png")
_SD_FILENAMES = ("font_btfl.png",    "font_inav.png",    "font_ardu.png",    "font_quic.png")

# Standard base tile widths for single-column fonts
_STANDARD_BASE_TILE_W = {36, 24, 48, 72}


class OsdFont:
    """
    Wraps a font sheet image. Supports both single-column (256 chars)
    and multi-column (e.g. 4 × 256 = 1024 chars) layouts.

    tile_w / tile_h: the pixel dimensions of one glyph.
    n_cols: how many glyph columns the sheet has (1 or 4).
    """

    def __init__(self, image: "Image.Image",
                 tile_w: int, tile_h: int,
                 n_cols: int = 1,
                 name: str = ""):
        self.image  = image.convert("RGBA")
        self.tile_w = tile_w
        self.tile_h = tile_h
        self.n_cols = n_cols
        self.name   = name

    def get_char(self, code: int) -> Optional["Image.Image"]:
        """Return the RGBA glyph image for char code (may be > 255)."""
        if not PIL_OK:
            return None
        col = code // NUM_CHARS   # which column group (0 = chars 0-255)
        row = code % NUM_CHARS    # which row
        if col >= self.n_cols:
            col = 0               # fall back to first column
        x = col * self.tile_w
        y = row * self.tile_h
        if y + self.tile_h > self.image.height:
            return None
        if x + self.tile_w > self.image.width:
            return None
        return self.image.crop((x, y, x + self.tile_w, y + self.tile_h))

    def __repr__(self):
        return (f"OsdFont({self.name!r}, tile={self.tile_w}×{self.tile_h}, "
                f"n_cols={self.n_cols})")


def _detect_layout(img: "Image.Image") -> Tuple[int, int, int]:
    """
    Return (tile_w, tile_h, n_cols) from image dimensions.

    tile_h = image.height // 256  (always 256 rows in every font sheet).

    base_tile_w is derived from tile_h to match the correct 2:3 glyph aspect ratio:
      tile_h=36  → base_w=24   (HD standard)
      tile_h=54  → base_w=36   (SD standard)
      tile_h=72  → base_w=48   (HD tall variant)
      tile_h=108 → base_w=72   (SD tall variant)

    n_cols = image.width // base_tile_w
    Multi-column sheets (e.g. BTFL 96px wide HD = 4 × 24px cols) store:
      col 0: chars   0–255
      col 1: chars 256–511
      col 2: chars 512–767
      col 3: chars 768–1023
    """
    tile_h = img.height // NUM_CHARS

    _BASE_W: dict[int, int] = {36: 24, 54: 36, 72: 48, 108: 72}
    base_w = _BASE_W.get(tile_h)

    if base_w and img.width % base_w == 0:
        return base_w, tile_h, img.width // base_w

    # Fallback for non-standard tile heights
    for bw in (24, 36, 48, 72):
        if img.width % bw == 0:
            return bw, tile_h, img.width // bw

    return img.width, tile_h, 1


def load_font_from_file(path: str) -> Optional[OsdFont]:
    if not PIL_OK:
        return None
    try:
        img = Image.open(path)
        tw, th, nc = _detect_layout(img)
        name = os.path.basename(os.path.dirname(path))
        return OsdFont(img, tw, th, n_cols=nc, name=name)
    except Exception as e:
        print(f"[font_loader] {path}: {e}")
        return None


# ── Font database ────────────────────────────────────────────────────────────

def _firmware_of(folder_name: str) -> str:
    for fw, prefixes in FIRMWARE_PREFIXES.items():
        for p in prefixes:
            if folder_name.upper().startswith(p.upper()):
                return fw
    return "Other"


def scan_fonts() -> Dict[str, Path]:
    """Return {folder_name: folder_path} for all font dirs that contain a PNG."""
    result: Dict[str, Path] = {}
    if not _FONTS_DIR.is_dir():
        return result
    for d in sorted(_FONTS_DIR.iterdir()):
        if d.is_dir() and any(f.suffix.lower() == '.png' for f in d.iterdir()):
            result[d.name] = d
    return result


def fonts_by_firmware(firmware: str) -> Dict[str, Path]:
    """Return font dirs whose name starts with the given firmware's prefix(es)."""
    all_fonts = scan_fonts()
    prefixes  = [p.upper() for p in FIRMWARE_PREFIXES.get(firmware, [])]
    if not prefixes:
        return all_fonts
    return {
        name: path
        for name, path in all_fonts.items()
        if any(name.upper().startswith(p) for p in prefixes)
    }


def load_font(folder: Path, prefer_hd: bool = True) -> Optional[OsdFont]:
    """Load HD or SD PNG from a font folder."""
    if not folder.is_dir():
        return None
    files = {f.name.lower(): f for f in folder.iterdir() if f.suffix.lower() == '.png'}
    priority = (_HD_FILENAMES if prefer_hd else _SD_FILENAMES) + \
               (_SD_FILENAMES if prefer_hd else _HD_FILENAMES)
    for name in priority:
        if name in files:
            return load_font_from_file(str(files[name]))
    pngs = [f for f in folder.iterdir() if f.suffix.lower() == '.png']
    return load_font_from_file(str(pngs[0])) if pngs else None


def list_firmware_names() -> List[str]:
    return list(FIRMWARE_PREFIXES.keys())
