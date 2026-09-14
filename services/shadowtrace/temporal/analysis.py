"""ShadowTrace — Temporal activity profiling and timezone inference.

Design-doc §2.2 & PRD §4.2:
  - Extract posting hour UTC
  - Build activity distribution (24-bin histogram)
  - FFT for periodicity detection
  - Infer most likely timezone
"""

from __future__ import annotations

import datetime as dt
from typing import Sequence, Union
import numpy as np

TimestampType = Union[str, dt.datetime, int, float]


def _parse_timestamp(ts: TimestampType) -> dt.datetime:
    """Parse various timestamp representations into UTC datetime."""
    if isinstance(ts, dt.datetime):
        return ts if ts.tzinfo is not None else ts.replace(tzinfo=dt.timezone.utc)
    if isinstance(ts, (int, float)):
        return dt.datetime.fromtimestamp(ts, tz=dt.timezone.utc)
    if isinstance(ts, str):
        ts_clean = ts.replace("Z", "+00:00")
        try:
            parsed = dt.datetime.fromisoformat(ts_clean)
            return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=dt.timezone.utc)
        except ValueError:
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
                try:
                    return dt.datetime.strptime(ts, fmt).replace(tzinfo=dt.timezone.utc)
                except ValueError:
                    continue
            raise ValueError(f"Unrecognized timestamp format: {ts}")
    raise TypeError(f"Unsupported timestamp type: {type(ts)}")


def build_activity_histogram(timestamps: Sequence[TimestampType]) -> np.ndarray:
    """Build 24-bin normalized hourly activity histogram in UTC (0..23)."""
    counts = np.zeros(24, dtype=np.float32)
    if not timestamps:
        return counts

    for ts in timestamps:
        try:
            parsed = _parse_timestamp(ts)
            utc_dt = parsed.astimezone(dt.timezone.utc)
            counts[utc_dt.hour] += 1.0
        except Exception:
            continue

    total = counts.sum()
    if total > 0:
        counts /= total
    return counts


def fft_periodicity(histogram: np.ndarray) -> dict:
    """Perform FFT on 24-hour activity histogram to detect diurnal periodicity.

    Returns dict with dominant_period_hours, diurnal_strength (0..1), and spectrum.
    """
    if len(histogram) != 24 or histogram.sum() == 0:
        return {
            "dominant_period_hours": 24.0,
            "diurnal_strength": 0.0,
            "spectrum": [0.0] * 12,
        }

    # 24-point FFT
    fft_vals = np.fft.rfft(histogram)
    magnitudes = np.abs(fft_vals)

    # Exclude DC component (index 0)
    ac_mags = magnitudes[1:]  # frequencies 1..12 cycles/day
    if len(ac_mags) == 0 or ac_mags.sum() == 0:
        return {
            "dominant_period_hours": 24.0,
            "diurnal_strength": 0.0,
            "spectrum": magnitudes.tolist(),
        }

    diurnal_mag = ac_mags[0]
    total_ac = ac_mags.sum()
    diurnal_strength = float(diurnal_mag / total_ac) if total_ac > 0 else 0.0

    dom_idx = int(np.argmax(ac_mags)) + 1  # 1-indexed freq
    dom_period_hours = float(24.0 / dom_idx)

    return {
        "dominant_period_hours": round(dom_period_hours, 2),
        "diurnal_strength": round(min(max(diurnal_strength, 0.0), 1.0), 4),
        "spectrum": [round(float(m), 4) for m in magnitudes],
    }


def infer_timezone(histogram: np.ndarray) -> str:
    """Infer timezone from 24-bin UTC activity histogram.

    Heuristic: Peak activity typically occurs in afternoon/evening (~15:00 local time).
    Calculates circular mean to find center of activity and maps to UTC offset.
    """
    if len(histogram) != 24 or histogram.sum() == 0:
        return "UTC+0"

    peak_utc = int(np.argmax(histogram))
    
    angles = np.arange(24) * (2 * np.pi / 24)
    sin_sum = np.sum(histogram * np.sin(angles))
    cos_sum = np.sum(histogram * np.cos(angles))
    
    if abs(sin_sum) > 1e-6 or abs(cos_sum) > 1e-6:
        mean_angle = np.arctan2(sin_sum, cos_sum)
        if mean_angle < 0:
            mean_angle += 2 * np.pi
        center_utc = (mean_angle * 24 / (2 * np.pi))
    else:
        center_utc = float(peak_utc)

    ASSUMED_LOCAL_PEAK = 15.0
    offset_raw = ASSUMED_LOCAL_PEAK - center_utc
    offset = (offset_raw + 12) % 24 - 12
    offset_int = int(round(offset))

    if offset_int == 0:
        return "UTC+0"
    elif offset_int > 0:
        return f"UTC+{offset_int}"
    else:
        return f"UTC{offset_int}"


def temporal_profile(timestamps: Sequence[TimestampType]) -> dict:
    """Compute full temporal profile from a list of timestamps."""
    hist = build_activity_histogram(timestamps)
    fft_res = fft_periodicity(hist)
    tz = infer_timezone(hist)

    peak_hour = int(np.argmax(hist)) if hist.sum() > 0 else 0
    trough_hour = int(np.argmin(hist)) if hist.sum() > 0 else 0

    return {
        "histogram": [round(float(v), 4) for v in hist],
        "peak_hour_utc": peak_hour,
        "trough_hour_utc": trough_hour,
        "dominant_period_hours": fft_res["dominant_period_hours"],
        "diurnal_strength": fft_res["diurnal_strength"],
        "timezone_estimate": tz,
        "sample_count": len(timestamps),
    }
