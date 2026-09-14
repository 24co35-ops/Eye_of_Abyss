"""VoiceGuard — audio preprocessing pipeline.

Design-doc §2.1:
  Resample → 16kHz, normalize amplitude, split 2s overlapping windows (50%),
  apply noisereduce.
"""

from __future__ import annotations

import io
from typing import Generator

import librosa
import numpy as np
try:
    import noisereduce as nr
except Exception:
    nr = None

# Design-doc constants
SAMPLE_RATE = 16_000
WINDOW_SEC = 2.0
OVERLAP = 0.5  # 50 % overlap
WINDOW_SAMPLES = int(WINDOW_SEC * SAMPLE_RATE)
HOP_SAMPLES = int(WINDOW_SAMPLES * (1 - OVERLAP))
N_MFCC = 40


def load_audio(data: bytes, filename: str = "") -> np.ndarray:
    """Load audio bytes → mono float32 @ 16 kHz."""
    buf = io.BytesIO(data)
    waveform, sr = librosa.load(buf, sr=SAMPLE_RATE, mono=True)
    return waveform


def normalize(waveform: np.ndarray) -> np.ndarray:
    peak = np.max(np.abs(waveform))
    return waveform / (peak + 1e-9)


def reduce_noise(waveform: np.ndarray) -> np.ndarray:
    if nr is None:
        return waveform
    # ponytail: stationary=True is fast; set to False for adaptive (slower)
    return nr.reduce_noise(y=waveform, sr=SAMPLE_RATE, stationary=True)


def window_audio(waveform: np.ndarray) -> Generator[tuple[int, np.ndarray], None, None]:
    """Yield (start_sample, window) with 50% overlap."""
    n = len(waveform)
    start = 0
    while start + WINDOW_SAMPLES <= n:
        yield start, waveform[start : start + WINDOW_SAMPLES]
        start += HOP_SAMPLES
    # trailing partial window — pad if >= 0.5s
    if start < n and (n - start) >= SAMPLE_RATE // 2:
        pad = np.zeros(WINDOW_SAMPLES, dtype=np.float32)
        pad[: n - start] = waveform[start:]
        yield start, pad


def preprocess(data: bytes, filename: str = "") -> list[dict]:
    """Full pipeline. Returns list of window dicts ready for inference."""
    waveform = load_audio(data, filename)
    waveform = normalize(waveform)
    waveform = reduce_noise(waveform)

    windows = []
    for start_sample, win in window_audio(waveform):
        mfcc = librosa.feature.mfcc(y=win, sr=SAMPLE_RATE, n_mfcc=N_MFCC)
        mel = librosa.feature.melspectrogram(y=win, sr=SAMPLE_RATE, n_mels=128)
        flatness = librosa.feature.spectral_flatness(y=win)
        windows.append({
            "start_sec": round(start_sample / SAMPLE_RATE, 3),
            "end_sec": round((start_sample + WINDOW_SAMPLES) / SAMPLE_RATE, 3),
            "waveform": win,
            "mfcc": mfcc,           # (N_MFCC, T)
            "mel": mel,             # (128, T)
            "flatness": flatness,   # (1, T)
        })
    return windows
