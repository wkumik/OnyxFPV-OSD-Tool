# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2025 OnyxFPV — https://github.com/onyxfpv
"""
srt_parser.py  –  Parse OnyxFPV SRT telemetry subtitle files.

SRT files are standard subtitle files containing custom telemetry lines.
From the Ruby firmware (rx_video_recording_data.cpp), the SRT content
can include any combination of:

  Line 1 (if MAVLink enabled and data available):
    D: <dist>m/ft  H: <alt>m/ft  <lat>, <lon>  <voltage> V
    (or "No MAVLink telemetry" if FC has no MAVLink)

  Line 2 (second text line, optional per settings):
    <MM:SS>  Radio 1: <dBm> dBm  <SNR> SNR  Radio 2: ...   <Mbps> Mbps

The format is flexible and varies per system configuration.
We parse generically: extract any recognisable values, skip
"No MAVLink telemetry" lines, and show everything else in the
status bar.
"""

import re
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class TelemetryData:
    raw_lines:     list[str]       = field(default_factory=list)
    flight_time:   str             = ""
    radio1_dbm:    Optional[int]   = None
    radio1_snr:    Optional[int]   = None
    radio2_dbm:    Optional[int]   = None
    radio2_snr:    Optional[int]   = None
    link_mbps:     Optional[float] = None
    distance_m:    Optional[float] = None
    altitude_m:    Optional[float] = None
    voltage_v:     Optional[float] = None
    gps_lat:       Optional[float] = None
    gps_lon:       Optional[float] = None

    def status_line(self) -> str:
        """Build a compact one-line status string for the bottom overlay bar."""
        parts = []
        if self.flight_time:
            parts.append(self.flight_time)
        if self.radio1_dbm is not None:
            s = f"R1:{self.radio1_dbm:+d}dBm"
            if self.radio1_snr is not None:
                s += f" {self.radio1_snr}SNR"
            parts.append(s)
        if self.radio2_dbm is not None:
            s = f"R2:{self.radio2_dbm:+d}dBm"
            if self.radio2_snr is not None:
                s += f" {self.radio2_snr}SNR"
            parts.append(s)
        if self.link_mbps is not None:
            parts.append(f"{self.link_mbps:.1f}Mbps")
        if self.voltage_v is not None:
            parts.append(f"{self.voltage_v:.1f}V")
        if self.altitude_m is not None:
            parts.append(f"H:{self.altitude_m:.0f}m")
        if self.distance_m is not None:
            parts.append(f"D:{self.distance_m:.0f}m")
        return "  ".join(parts)


@dataclass
class SrtEntry:
    index:     int
    start_ms:  int
    end_ms:    int
    telemetry: TelemetryData


@dataclass
class SrtFile:
    entries:     list[SrtEntry] = field(default_factory=list)
    duration_ms: int = 0

    def get_data_at_time(self, timestamp_ms: int) -> Optional[TelemetryData]:
        """Return telemetry for the SRT entry active at timestamp_ms."""
        # Binary-search-friendly: entries are in order
        for e in self.entries:
            if e.start_ms <= timestamp_ms < e.end_ms:
                return e.telemetry
        return None


# ── Regexes ────────────────────────────────────────────────────────────────────

_TS_RE      = re.compile(
    r"(\d{2}):(\d{2}):(\d{2}),(\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2}),(\d{3})"
)
_SKIP_RE    = re.compile(r"No MAVLink telemetry", re.IGNORECASE)

# Radio: "Radio 1: -65 dBm  12 SNR" or "Radio 1: -65 dBm  12 SNR  "
_RADIO_RE   = re.compile(
    r"Radio\s+(\d+):\s*(-?\d+)\s*dBm(?:\s+(-?\d+)\s*SNR)?", re.IGNORECASE
)
_MBPS_RE    = re.compile(r"([\d.]+)\s*Mbps", re.IGNORECASE)
_TIME_RE    = re.compile(r"^\s*(\d{2}):(\d{2})\b")
_DIST_RE    = re.compile(r"D:\s*([\d.]+)\s*(m|ft)", re.IGNORECASE)
_ALT_RE     = re.compile(r"H:\s*([\d.]+)\s*(m|ft)", re.IGNORECASE)
_VOLT_RE    = re.compile(r"([\d.]+)\s*V\b")
_GPS_RE     = re.compile(r"(-?\d+\.\d+)\s*,\s*(-?\d+\.\d+)")


def _ft_to_m(ft: float) -> float:
    return ft / 3.28084


def _parse_lines(lines: list[str]) -> TelemetryData:
    t = TelemetryData(raw_lines=list(lines))

    for line in lines:
        if _SKIP_RE.search(line):
            continue

        # Flight time MM:SS at start of line
        tm = _TIME_RE.match(line)
        if tm and not t.flight_time:
            t.flight_time = f"{tm.group(1)}:{tm.group(2)}"

        # Radio interfaces
        for m in _RADIO_RE.finditer(line):
            idx  = int(m.group(1))
            dbm  = int(m.group(2))
            snr  = int(m.group(3)) if m.group(3) is not None else None
            if idx == 1:
                t.radio1_dbm = dbm
                if snr is not None:
                    t.radio1_snr = snr
            elif idx == 2:
                t.radio2_dbm = dbm
                if snr is not None:
                    t.radio2_snr = snr

        # Bitrate
        mb = _MBPS_RE.search(line)
        if mb:
            t.link_mbps = float(mb.group(1))

        # Distance
        d = _DIST_RE.search(line)
        if d:
            v = float(d.group(1))
            t.distance_m = _ft_to_m(v) if d.group(2).lower() == 'ft' else v

        # Altitude
        h = _ALT_RE.search(line)
        if h:
            v = float(h.group(1))
            t.altitude_m = _ft_to_m(v) if h.group(2).lower() == 'ft' else v

        # GPS
        gps = _GPS_RE.search(line)
        if gps:
            t.gps_lat = float(gps.group(1))
            t.gps_lon = float(gps.group(2))

        # Voltage (only if no GPS on same line to avoid false matches)
        if not gps:
            volt = _VOLT_RE.search(line)
            if volt:
                t.voltage_v = float(volt.group(1))

    return t


def _to_ms(h: str, m: str, s: str, ms: str) -> int:
    return int(h)*3_600_000 + int(m)*60_000 + int(s)*1_000 + int(ms)


def parse_srt(path: str) -> SrtFile:
    srt = SrtFile()
    idx: Optional[int] = None
    start_ms = end_ms = 0
    data_lines: list[str] = []

    def _flush():
        if idx is not None:
            srt.entries.append(SrtEntry(
                index=idx, start_ms=start_ms, end_ms=end_ms,
                telemetry=_parse_lines(data_lines),
            ))

    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        for raw_line in f:
            line = raw_line.rstrip('\n').strip()

            if not line:
                _flush()
                idx = None
                data_lines = []
                continue

            # Sequence number
            if idx is None and line.isdigit():
                idx = int(line)
                continue

            # Timestamp line
            ts = _TS_RE.match(line)
            if ts and idx is not None and not data_lines:
                g = ts.groups()
                start_ms = _to_ms(*g[:4])
                end_ms   = _to_ms(*g[4:])
                continue

            data_lines.append(line)

    _flush()  # handle file without trailing blank line

    if srt.entries:
        srt.duration_ms = srt.entries[-1].end_ms

    return srt
