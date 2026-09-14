"""VoiceGuard — artifact generation.

Produces:
  - MFCC heatmap (base64 PNG via matplotlib)
  - Mel spectrogram (base64 PNG)
Both embedded in the EvidenceObject artifacts list.
"""

from __future__ import annotations

import base64
import io

import librosa
import librosa.display
import matplotlib
matplotlib.use("Agg")  # headless — no display needed
import matplotlib.pyplot as plt
import numpy as np


def _fig_to_b64(fig: plt.Figure) -> str:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=80)
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("ascii")


def make_mfcc_heatmap(mfcc: np.ndarray) -> str:
    """Return base64 PNG of the MFCC heatmap for the full audio."""
    fig, ax = plt.subplots(figsize=(10, 3))
    img = librosa.display.specshow(mfcc, x_axis="time", ax=ax, cmap="magma")
    ax.set_title("MFCC Heatmap")
    ax.set_ylabel("Coefficient")
    fig.colorbar(img, ax=ax, format="%+.1f")
    return _fig_to_b64(fig)


def make_mel_spectrogram(mel: np.ndarray, sr: int = 16_000) -> str:
    """Return base64 PNG of the mel spectrogram."""
    fig, ax = plt.subplots(figsize=(10, 3))
    mel_db = librosa.power_to_db(mel, ref=np.max)
    img = librosa.display.specshow(mel_db, x_axis="time", y_axis="mel", sr=sr, ax=ax, cmap="inferno")
    ax.set_title("Mel Spectrogram")
    fig.colorbar(img, ax=ax, format="%+.0f dB")
    return _fig_to_b64(fig)


def generate_artifacts(windows: list[dict]) -> tuple[str, str]:
    """Aggregate all windows → full-audio MFCC + mel, return (mfcc_b64, mel_b64)."""
    if not windows:
        return "", ""
    mfcc_full = np.concatenate([w["mfcc"] for w in windows], axis=1)
    mel_full = np.concatenate([w["mel"] for w in windows], axis=1)
    return make_mfcc_heatmap(mfcc_full), make_mel_spectrogram(mel_full)
