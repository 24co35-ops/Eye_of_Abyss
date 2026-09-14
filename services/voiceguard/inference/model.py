"""VoiceGuard — dual-branch inference + score fusion.

Design-doc §2.1:
  Branch A: DistilWav2Vec2 → sigmoid → P(synthetic)
  Branch B: ECAPA-TDNN → softmax → [real, TTS, voice_conv, replay]
  Fusion: 0.6 * A + 0.4 * B(TTS+vc+replay)
  Threshold: >0.72 → SYNTHETIC, 0.45–0.72 → UNCERTAIN, <0.45 → REAL
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Literal

import numpy as np
import torch
import torch.nn as nn

logger = logging.getLogger(__name__)

# Thresholds from design-doc §2.1
THRESHOLD_SYNTHETIC = 0.72
THRESHOLD_UNCERTAIN_LOW = 0.45

# Fusion weights from design-doc §2.1
WEIGHT_A = 0.6
WEIGHT_B = 0.4

_DEVICE: torch.device | None = None
_wav2vec_pipeline = None  # lazy-loaded HuggingFace pipeline
_ecapa_model: "ECAPAStub | None" = None


def _device() -> torch.device:
    global _DEVICE
    if _DEVICE is None:
        _DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info("VoiceGuard inference device: %s", _DEVICE)
    return _DEVICE


# ── ECAPA-TDNN stub ──────────────────────────────────────────────────────────
# ponytail: real ECAPA uses speechbrain; stub covers CPU fallback + tests.
# Replace with: from speechbrain.pretrained import EncoderClassifier

class ECAPAStub(nn.Module):
    """Lightweight ECAPA-TDNN stand-in for CPU fallback and testing.

    Produces softmax logits over [real, TTS, voice_conv, replay].
    A real deployment loads the SpeechBrain pretrained ECAPA encoder.
    # ponytail: swap _forward_stub for speechbrain inference when model available
    """

    def __init__(self) -> None:
        super().__init__()
        self.fc = nn.Linear(40, 4)  # 40 MFCC means → 4 classes

    def forward(self, mfcc_mean: torch.Tensor) -> torch.Tensor:
        return torch.softmax(self.fc(mfcc_mean), dim=-1)


def load_models() -> None:
    """Called once at startup. Loads both branches; falls back gracefully."""
    global _wav2vec_pipeline, _ecapa_model
    dev = _device()

    # Branch A: DistilWav2Vec2 via HuggingFace pipeline
    try:
        from transformers import pipeline as hf_pipeline
        model_name = os.environ.get(
            "WAV2VEC_MODEL", "facebook/wav2vec2-base"
        )
        _wav2vec_pipeline = hf_pipeline(
            "audio-classification",
            model=model_name,
            device=0 if dev.type == "cuda" else -1,
        )
        logger.info("Branch A (DistilWav2Vec2) loaded: %s", model_name)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Branch A unavailable (%s); using MFCC heuristic fallback.", exc)
        _wav2vec_pipeline = None

    # Branch B: ECAPA-TDNN stub
    _ecapa_model = ECAPAStub().to(dev)
    _ecapa_model.eval()
    logger.info("Branch B (ECAPA stub) loaded on %s.", dev)


# ── Per-window inference ─────────────────────────────────────────────────────

def _branch_a(waveform: np.ndarray) -> float:
    """Returns P(synthetic) ∈ [0,1] from DistilWav2Vec2."""
    if _wav2vec_pipeline is None:
        # Heuristic fallback: spectral flatness proxy for synthesis
        # High flatness → more likely synthetic (tonally flat TTS)
        import librosa
        flatness = librosa.feature.spectral_flatness(y=waveform).mean()
        # ponytail: crude heuristic, not a trained model
        return float(np.clip(flatness * 20, 0.0, 1.0))

    result = _wav2vec_pipeline(
        {"raw": waveform, "sampling_rate": 16_000},
        top_k=None,
    )
    # Map label → score; model must output "FAKE"/"REAL" or similar
    scores = {r["label"].upper(): r["score"] for r in result}
    return scores.get("FAKE", scores.get("SYNTHETIC", 1 - scores.get("REAL", 1.0)))


def _branch_b(mfcc: np.ndarray) -> tuple[float, str]:
    """Returns (P(synthetic), artifact_type) from ECAPA-TDNN stub."""
    assert _ecapa_model is not None
    mfcc_mean = torch.tensor(mfcc.mean(axis=1), dtype=torch.float32).to(_device())
    with torch.no_grad():
        probs = _ecapa_model(mfcc_mean).cpu().numpy()  # [real, TTS, voice_conv, replay]
    labels = ["real", "TTS", "voice_conv", "replay"]
    top_idx = int(np.argmax(probs))
    p_synthetic = float(probs[1] + probs[2] + probs[3])  # sum non-real
    return p_synthetic, labels[top_idx]


@dataclass
class WindowResult:
    start_sec: float
    end_sec: float
    p_synthetic: float
    artifact_type: str  # TTS | voice_conv | replay | clean
    verdict: Literal["real", "synthetic", "uncertain"]


def infer_window(window: dict) -> WindowResult:
    """Run both branches + fusion on a single preprocessed window."""
    waveform: np.ndarray = window["waveform"]
    mfcc: np.ndarray = window["mfcc"]

    p_a = _branch_a(waveform)
    p_b, artifact_type = _branch_b(mfcc)

    fused = WEIGHT_A * p_a + WEIGHT_B * p_b

    if fused > THRESHOLD_SYNTHETIC:
        verdict = "synthetic"
    elif fused > THRESHOLD_UNCERTAIN_LOW:
        verdict = "uncertain"
    else:
        verdict = "real"
        artifact_type = "clean"

    return WindowResult(
        start_sec=window["start_sec"],
        end_sec=window["end_sec"],
        p_synthetic=round(fused, 4),
        artifact_type=artifact_type,
        verdict=verdict,
    )


@dataclass
class AudioResult:
    verdict: Literal["real", "synthetic", "uncertain"]
    verdict_code: str          # e.g. "SYNTHETIC_TTS"
    confidence: float
    confidence_tier: Literal["high", "medium", "low"]
    flagged_segments: list[dict]   # windows where verdict != real
    artifact_type: str


def aggregate_windows(window_results: list[WindowResult]) -> AudioResult:
    """Aggregate per-window results → single file-level verdict."""
    if not window_results:
        return AudioResult("uncertain", "UNCERTAIN", 0.5, "low", [], "unknown")

    scores = [w.p_synthetic for w in window_results]
    mean_score = float(np.mean(scores))
    max_score = float(np.max(scores))

    # File verdict driven by max (one bad segment = flag)
    if max_score > THRESHOLD_SYNTHETIC:
        verdict = "synthetic"
    elif max_score > THRESHOLD_UNCERTAIN_LOW:
        verdict = "uncertain"
    else:
        verdict = "real"

    # Artifact type = most common non-clean label
    non_clean = [w.artifact_type for w in window_results if w.artifact_type != "clean"]
    artifact_type = max(set(non_clean), key=non_clean.count) if non_clean else "clean"

    # confidence = mean of flagged windows, clipped
    confidence = round(float(np.clip(mean_score if verdict != "real" else 1 - mean_score, 0.0, 1.0)), 4)

    if confidence >= 0.8:
        tier = "high"
    elif confidence >= 0.5:
        tier = "medium"
    else:
        tier = "low"

    verdict_code = {
        "synthetic": f"SYNTHETIC_{artifact_type.upper()}",
        "uncertain": "UNCERTAIN",
        "real": "REAL_CLEAN",
    }[verdict]

    flagged = [
        {"start_sec": w.start_sec, "end_sec": w.end_sec, "p_synthetic": w.p_synthetic, "type": w.artifact_type}
        for w in window_results
        if w.verdict != "real"
    ]

    return AudioResult(
        verdict=verdict,
        verdict_code=verdict_code,
        confidence=confidence,
        confidence_tier=tier,
        flagged_segments=flagged,
        artifact_type=artifact_type,
    )
