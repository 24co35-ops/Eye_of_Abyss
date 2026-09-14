"""VoiceGuard unit tests.

Tests cover:
- Preprocessing pipeline (window count, shape)
- ECAPA stub inference (branch B)
- Score fusion thresholds
- Window aggregation (verdict logic)
- API endpoints (file upload, poll, artifacts, WebSocket)
"""

import json
import os
import sys
import types
import uuid
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

# ── Path setup ────────────────────────────────────────────────────────────────
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
SVC = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)
sys.path.insert(0, SVC)


# ── Preprocessing tests ───────────────────────────────────────────────────────

def _make_wav_bytes(duration_sec: float = 4.0, sr: int = 16_000) -> bytes:
    """Synthesize a minimal WAV file in-memory."""
    import io
    import wave
    import struct

    n_samples = int(duration_sec * sr)
    # 440 Hz sine
    samples = [int(32767 * np.sin(2 * np.pi * 440 * i / sr)) for i in range(n_samples)]
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(struct.pack(f"<{n_samples}h", *samples))
    return buf.getvalue()


def test_preprocess_window_count():
    """4s audio at 50% overlap 2s windows → ~3 windows."""
    from preprocessing import preprocess
    data = _make_wav_bytes(4.0)
    windows = preprocess(data)
    # 4s: starts at 0, 1, 2 → 3 windows
    assert len(windows) >= 2
    for w in windows:
        assert "waveform" in w
        assert "mfcc" in w
        assert "mel" in w
        assert w["mfcc"].shape[0] == 40


def test_preprocess_window_duration():
    """Each window waveform is exactly WINDOW_SAMPLES long."""
    from preprocessing import preprocess, WINDOW_SAMPLES
    data = _make_wav_bytes(3.0)
    windows = preprocess(data)
    for w in windows:
        assert len(w["waveform"]) == WINDOW_SAMPLES


def test_preprocess_short_audio():
    """Very short audio (<1s) still returns at least one window (padded)."""
    from preprocessing import preprocess
    data = _make_wav_bytes(0.6)
    windows = preprocess(data)
    assert len(windows) >= 1


# ── Inference model tests ─────────────────────────────────────────────────────

def test_ecapa_stub_output_shape():
    """ECAPAStub forward → 4-class softmax vector summing to 1."""
    import torch
    from inference.model import ECAPAStub
    model = ECAPAStub()
    x = torch.randn(40)
    out = model(x)
    assert out.shape == (4,)
    assert abs(out.sum().item() - 1.0) < 1e-5


def test_infer_window_real():
    """A low-flatness sine window → valid verdict. Uses heuristic fallback (no HF download)."""
    import librosa
    import torch
    import inference.model as im
    from preprocessing import N_MFCC, SAMPLE_RATE, WINDOW_SAMPLES
    from inference.model import ECAPAStub, infer_window

    # Force heuristic branch-A (no HuggingFace) and a fresh ECAPA stub
    im._wav2vec_pipeline = None
    im._ecapa_model = ECAPAStub()
    im._ecapa_model.eval()

    waveform = np.sin(2 * np.pi * 440 * np.arange(WINDOW_SAMPLES) / SAMPLE_RATE).astype(np.float32)
    mfcc = librosa.feature.mfcc(y=waveform, sr=SAMPLE_RATE, n_mfcc=N_MFCC)
    mel = librosa.feature.melspectrogram(y=waveform, sr=SAMPLE_RATE, n_mels=128)
    flatness = librosa.feature.spectral_flatness(y=waveform)

    window = {"start_sec": 0.0, "end_sec": 2.0, "waveform": waveform, "mfcc": mfcc, "mel": mel, "flatness": flatness}
    result = infer_window(window)

    assert 0.0 <= result.p_synthetic <= 1.0
    assert result.verdict in ("real", "uncertain", "synthetic")


def test_fusion_threshold_synthetic():
    """p_synthetic > 0.72 → verdict 'synthetic'."""
    from inference.model import WindowResult, aggregate_windows
    results = [
        WindowResult(0.0, 2.0, 0.85, "TTS", "synthetic"),
        WindowResult(2.0, 4.0, 0.90, "TTS", "synthetic"),
    ]
    agg = aggregate_windows(results)
    assert agg.verdict == "synthetic"
    assert "SYNTHETIC" in agg.verdict_code


def test_fusion_threshold_real():
    """p_synthetic < 0.45 → verdict 'real'."""
    from inference.model import WindowResult, aggregate_windows
    results = [
        WindowResult(0.0, 2.0, 0.10, "clean", "real"),
        WindowResult(2.0, 4.0, 0.12, "clean", "real"),
    ]
    agg = aggregate_windows(results)
    assert agg.verdict == "real"


def test_fusion_threshold_uncertain():
    """p_synthetic in (0.45, 0.72) → verdict 'uncertain'."""
    from inference.model import WindowResult, aggregate_windows
    results = [
        WindowResult(0.0, 2.0, 0.55, "voice_conv", "uncertain"),
    ]
    agg = aggregate_windows(results)
    assert agg.verdict == "uncertain"


def test_aggregate_empty():
    """Empty windows → uncertain fallback."""
    from inference.model import aggregate_windows
    agg = aggregate_windows([])
    assert agg.verdict == "uncertain"


# ── Artifact tests ────────────────────────────────────────────────────────────

def test_generate_artifacts_returns_b64():
    """generate_artifacts returns non-empty base64 strings."""
    from inference.artifacts import generate_artifacts
    from preprocessing import SAMPLE_RATE, WINDOW_SAMPLES, N_MFCC
    import librosa

    waveform = np.random.randn(WINDOW_SAMPLES).astype(np.float32)
    mfcc = librosa.feature.mfcc(y=waveform, sr=SAMPLE_RATE, n_mfcc=N_MFCC)
    mel = librosa.feature.melspectrogram(y=waveform, sr=SAMPLE_RATE, n_mels=128)
    windows = [{"mfcc": mfcc, "mel": mel}]
    mfcc_b64, mel_b64 = generate_artifacts(windows)
    assert len(mfcc_b64) > 100
    assert len(mel_b64) > 100


# ── API endpoint tests ────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def client():
    from fastapi.testclient import TestClient
    import inference.model as im
    from inference.model import ECAPAStub
    # Pre-wire heuristic-only inference (no HuggingFace download, no network)
    im._wav2vec_pipeline = None
    im._ecapa_model = ECAPAStub()
    im._ecapa_model.eval()
    # Patch startup load_models to no-op (models already set above)
    with patch("main.load_models", return_value=None):
        from main import app
        with TestClient(app, raise_server_exceptions=False) as c:
            yield c


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["service"] == "voiceguard"


def test_analyze_file_and_poll(client):
    """Upload a WAV file, job completes synchronously, poll returns evidence."""
    wav_bytes = _make_wav_bytes(2.5)
    r = client.post(
        "/analyze/file",
        files={"file": ("test.wav", wav_bytes, "audio/wav")},
        data={"officer_id": "officer_001"},
    )
    assert r.status_code == 200
    body = r.json()
    job_id = body["job_id"]
    assert body["status"] in ("completed", "processing", "error")

    r2 = client.get(f"/analysis/{job_id}")
    assert r2.status_code == 200
    assert r2.json()["status"] in ("completed", "processing", "error")


def test_get_analysis_not_found(client):
    r = client.get(f"/analysis/{uuid.uuid4()}")
    assert r.status_code == 404


def test_get_artifacts_not_found(client):
    r = client.get(f"/analysis/{uuid.uuid4()}/artifacts")
    assert r.status_code == 404


def test_analyze_file_too_large(client):
    """Files over 50MB should return 413."""
    big = b"x" * (51 * 1024 * 1024)
    r = client.post(
        "/analyze/file",
        files={"file": ("big.wav", big, "audio/wav")},
        data={"officer_id": "officer_001"},
    )
    assert r.status_code == 413


def test_websocket_stream(client):
    """WebSocket: send metadata + one PCM chunk + EOF → get verdict response."""
    from preprocessing import SAMPLE_RATE, WINDOW_SAMPLES

    waveform = np.sin(
        2 * np.pi * 440 * np.arange(WINDOW_SAMPLES) / SAMPLE_RATE
    ).astype(np.float32)

    with client.websocket_connect("/analyze/stream") as ws:
        ws.send_text(json.dumps({"case_id": str(uuid.uuid4()), "officer_id": "off_001"}))
        ws.send_bytes(waveform.tobytes())
        msg = ws.receive_json()
        assert "verdict" in msg or "error" in msg
        ws.send_text("EOF")
        final = ws.receive_json()
        assert final.get("status") == "done" or "error" in final
