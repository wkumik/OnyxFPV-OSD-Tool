# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2025 OnyxFPV — https://github.com/onyxfpv
"""
Animated splash screen — plays splash_anim.gif while the app (or installer) loads.
"""

import os, sys, random
from PyQt6.QtWidgets import QWidget, QApplication
from PyQt6.QtCore    import Qt, QTimer, QRectF, QSize, pyqtSignal
from PyQt6.QtGui     import (QPainter, QColor, QLinearGradient, QPen,
                              QBrush, QFont, QPainterPath, QPixmap, QIcon)

W, H      = 560, 460
GIF_SIZE  = 260
GIF_Y     = 28
PROG_H    = 2
PROG_Y    = H - PROG_H

BG       = QColor( 10,  10,  18)
TEXT_C   = QColor(205, 214, 244)
SUB_C    = QColor(108, 112, 134)
STATUS_C = QColor(148, 156, 187)
PROG_BG  = QColor( 24,  24,  37)
PROG_A   = QColor(137, 180, 250)
PROG_B   = QColor(203, 166, 247)
BORDER_C = QColor( 49,  50,  68, 160)

_FUNNY = [
    "Charging LiPo batteries…",
    "Looking up Joshua Bardwell's newest video…",
    "Calculating prop wash compensation…",
    "Arguing with Betaflight configurator…",
    "Blaming the VTX for video feed issues…",
    "Printing replacement motor mount…",
    "Waiting for props to arrive from AliExpress…",
    "Checking wind speed at the flying field…",
    "Googling 'why is my quad flipping on takeoff'…",
    "Untangling video antenna cables…",
    "Watching Oscar Liang's tune guide for the 4th time…",
    "Recalibrating ESCs (again)…",
    "Forgetting where the arm switch is mapped…",
    "Explaining to mum what FPV means…",
    "Ordering yet another pair of goggles…",
    "Doing a maiden flight in 30 km/h wind…",
    "Pretending the crash was a 'controlled landing'…",
    "Reflow-soldering a motor pad at midnight…",
    "Searching for the micro SD card in the grass…",
    "Contemplating DJI O3 vs Walksnail again…",
    "Tuning RPM filter until it sounds perfect…",
    "Joining yet another FPV Facebook group…",
    "Forgetting to arm before throwing quad…",
    "Downloading new font that fixes nothing…",
    "Rechecking blackbox logs for the 6th time…",
]


class SplashScreen(QWidget):
    closed = pyqtSignal()

    def __init__(self):
        super().__init__(None,
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(W, H)
        self._center_on_screen()

        self._prog         = 0.0
        self._target_prog  = 0.0
        self._nudge_speed  = 0.0005
        self._status       = "Starting…"
        self._msg_counter  = 0
        self._frame_pixmap = None

        # Pre-extract all GIF frames into QPixmaps for smooth manual cycling
        self._frames      = []
        self._frame_idx   = 0
        self._frame_delay = 50   # ms per frame (default)
        self._frame_accum = 0    # accumulated ms since last frame advance

        gif_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "splash_anim.gif")
        if os.path.exists(gif_path):
            try:
                from PIL import Image
                gif = Image.open(gif_path)
                frame_i = 0
                while True:
                    gif.seek(frame_i)
                    frame_delay = gif.info.get("duration", 50)
                    rgba = gif.convert("RGBA").resize(
                        (GIF_SIZE, GIF_SIZE), Image.LANCZOS)
                    data = rgba.tobytes("raw", "RGBA")
                    from PyQt6.QtGui import QImage
                    qi = QImage(data, GIF_SIZE, GIF_SIZE,
                                QImage.Format.Format_RGBA8888).copy()
                    self._frames.append((QPixmap.fromImage(qi), frame_delay))
                    frame_i += 1
            except EOFError:
                pass
            except Exception:
                self._frames = []

        ico = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.png")
        if os.path.exists(ico):
            self.setWindowIcon(QIcon(ico))

        # Single 33ms tick drives both frame advance AND progress nudge
        self._tick_timer = QTimer(self)
        self._tick_timer.setInterval(33)
        self._tick_timer.timeout.connect(self._tick)
        self._tick_timer.start()

    # ── Public API ─────────────────────────────────────────────────────────────

    def set_progress(self, value: float, status: str = ""):
        self._target_prog = max(self._target_prog, min(1.0, value))
        self._msg_counter += 1
        if status:
            if self._msg_counter % 4 == 0:
                self._status = random.choice(_FUNNY)
            else:
                self._status = status
        remaining = max(0.001, self._target_prog - self._prog)
        self._nudge_speed = max(0.0008, remaining * 0.12)
        self.update()

    def finish(self, main_window=None):
        self._target_prog = 1.0
        self._prog        = 1.0
        self._status      = "Ready"
        self.update()
        QTimer.singleShot(350, lambda: self._do_close(main_window))

    def _do_close(self, main_window):
        self._tick_timer.stop()
        self.close()
        if main_window is not None:
            main_window.show()
        self.closed.emit()

    # ── Internal ───────────────────────────────────────────────────────────────

    def _center_on_screen(self):
        screen = QApplication.primaryScreen()
        if screen:
            sg = screen.geometry()
            self.move(sg.center().x() - W // 2, sg.center().y() - H // 2)

    def _tick(self):
        """Called every 33ms. Advances GIF frame and nudges progress bar."""
        # Advance GIF frame
        if self._frames:
            self._frame_accum += 33
            _, delay = self._frames[self._frame_idx]
            if self._frame_accum >= delay:
                self._frame_accum -= delay
                self._frame_idx = (self._frame_idx + 1) % len(self._frames)

        # Nudge progress bar
        if self._prog < self._target_prog:
            self._prog = min(self._target_prog, self._prog + self._nudge_speed)
        elif self._prog < 0.97:
            self._prog = min(self._target_prog, self._prog + 0.00025)

        self.update()

    # ── Paint ──────────────────────────────────────────────────────────────────

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        path = QPainterPath()
        path.addRoundedRect(QRectF(0, 0, W, H), 14, 14)
        p.fillPath(path, BG)

        if self._frames:
            pixmap, _ = self._frames[self._frame_idx]
            x = (W - GIF_SIZE) // 2
            p.drawPixmap(x, GIF_Y, pixmap)

        ty = GIF_Y + GIF_SIZE + 8
        font_title = QFont("Segoe UI", 18, QFont.Weight.Light)
        font_title.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 4)
        p.setFont(font_title)
        p.setPen(TEXT_C)
        p.drawText(QRectF(0, ty, W, 30), Qt.AlignmentFlag.AlignHCenter, "ONYXFPV")

        font_sub = QFont("Segoe UI", 8)
        font_sub.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 6)
        p.setFont(font_sub)
        p.setPen(SUB_C)
        p.drawText(QRectF(0, ty + 28, W, 18),
                   Qt.AlignmentFlag.AlignHCenter, "OSD TOOL")

        font_st = QFont("Segoe UI", 8)
        p.setFont(font_st)
        p.setPen(STATUS_C)
        p.drawText(QRectF(16, PROG_Y - 22, W - 32, 18),
                   Qt.AlignmentFlag.AlignHCenter, self._status)

        p.setBrush(QBrush(PROG_BG))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRect(QRectF(0, PROG_Y, W, PROG_H))

        if self._prog > 0.001:
            fill_w = max(PROG_H * 2, self._prog * W)
            grad = QLinearGradient(0, 0, fill_w, 0)
            grad.setColorAt(0.0, PROG_A)
            grad.setColorAt(1.0, PROG_B)
            p.setBrush(QBrush(grad))
            p.drawRect(QRectF(0, PROG_Y, fill_w, PROG_H))

        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(BORDER_C, 1))
        p.drawRoundedRect(QRectF(0.5, 0.5, W - 1, H - 1), 14, 14)

        p.end()
