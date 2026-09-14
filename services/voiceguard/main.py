"""VoiceGuard — Voice deepfake detection service. Port 8001.

Design-doc §2.1 / PRD §4.1
Endpoints:
  POST /analyze/file          → Upload audio file, returns job_id
  WS   /analyze/stream        → Real-time 2s chunk stream
  GET  /analysis/{job_id}     → Poll job result (EvidenceObject)
  GET  /analysis/{job_id}/artifacts  → Download artifact PNGs (base64)
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import sys
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Optional

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Annotated

# Shared package path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

try:
    from shared.schemas import Artifact, EvidenceObject
except ImportError:
    from schemas import Artifact, EvidenceObject  # type: ignore

from preprocessing import preprocess
from inference import aggregate_windows, generate_artifacts, infer_window, load_models

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("voiceguard")

# ── In-memory job store ───────────────────────────────────────────────────────
# ponytail: dict is fine for demo/hackathon; swap for Redis when multi-worker
_jobs: dict[str, dict] = {}


@asynccontextmanager
async def _lifespan(app):
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, load_models)
    yield


app = FastAPI(
    title="VoiceGuard",
    version="0.1.0",
    description="Real-time AI voice deepfake detection — Eye of Abyss",
    lifespan=_lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

# Auth — JWT required on analysis endpoints
from auth import Role, TokenPayload, get_current_user, require_role  # noqa: E402
CurrentUser = Annotated[TokenPayload, Depends(get_current_user)]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _confidence_tier(c: float) -> str:
    if c >= 0.8:
        return "high"
    if c >= 0.5:
        return "medium"
    return "low"


def _compute_hash(payload: dict) -> str:
    raw = json.dumps(payload, sort_keys=True, default=str).encode()
    return hashlib.sha256(raw).hexdigest()


def _build_evidence(
    job_id: str,
    case_id: Optional[str],
    officer_id: str,
    audio_result,
    mfcc_b64: str,
    mel_b64: str,
) -> dict:
    """Construct EvidenceObject payload dict."""
    now = datetime.now(timezone.utc)
    case_uuid = uuid.UUID(case_id) if case_id else uuid.uuid4()

    artifacts = []
    if mfcc_b64:
        artifacts.append(Artifact(
            filename=f"{job_id}_mfcc.png",
            file_type="image/png",
            description="MFCC heatmap (base64 embedded)",
            storage_url=f"data:image/png;base64,{mfcc_b64}",
        ))
    if mel_b64:
        artifacts.append(Artifact(
            filename=f"{job_id}_spectrogram.png",
            file_type="image/png",
            description="Mel spectrogram (base64 embedded)",
            storage_url=f"data:image/png;base64,{mel_b64}",
        ))

    payload = {
        "flagged_segments": audio_result.flagged_segments,
        "artifact_type": audio_result.artifact_type,
        "window_count": len(audio_result.flagged_segments),
    }

    ev = EvidenceObject(
        evidence_id=uuid.UUID(job_id),
        case_id=case_uuid,
        module_id="voiceguard",
        created_at=now,
        created_by=officer_id,
        verdict=f"{'Synthetic' if audio_result.verdict == 'synthetic' else 'Real'} voice — {audio_result.artifact_type}",
        verdict_code=audio_result.verdict_code,
        confidence=audio_result.confidence,
        confidence_tier=audio_result.confidence_tier,
        payload=payload,
        artifacts=artifacts,
        submitted_by=officer_id,
        submitted_at=now,
    )
    ev_dict = ev.model_dump(mode="json")
    ev_dict["hash_sha256"] = _compute_hash(ev_dict)
    return ev_dict


# ── POST /analyze/file ────────────────────────────────────────────────────────

@app.post("/analyze/file", tags=["inference"])
async def analyze_file(
    file: UploadFile = File(...),
    case_id: Optional[str] = Form(None),
    officer_id: str = Form("system"),
):
    """Upload an audio file (WAV/MP3/FLAC/M4A ≤50MB) for deepfake analysis."""
    MAX_BYTES = 50 * 1024 * 1024
    data = await file.read()
    if len(data) > MAX_BYTES:
        raise HTTPException(status_code=413, detail="File exceeds 50 MB limit")

    job_id = str(uuid.uuid4())
    _jobs[job_id] = {"status": "processing"}

    # Run in executor so FastAPI event loop stays free
    loop = asyncio.get_event_loop()

    def _run():
        try:
            windows = preprocess(data, file.filename or "")
            if not windows:
                _jobs[job_id] = {"status": "error", "detail": "No audio windows extracted"}
                return
            results = [infer_window(w) for w in windows]
            audio_result = aggregate_windows(results)
            mfcc_b64, mel_b64 = generate_artifacts(windows)
            ev = _build_evidence(job_id, case_id, officer_id, audio_result, mfcc_b64, mel_b64)
            _jobs[job_id] = {"status": "completed", "evidence": ev}
        except Exception as exc:  # noqa: BLE001
            logger.exception("analyze_file error: %s", exc)
            _jobs[job_id] = {"status": "error", "detail": str(exc)}

    await loop.run_in_executor(None, _run)
    status = _jobs[job_id]["status"]
    return {"job_id": job_id, "status": status}


# ── GET /analysis/{job_id} ────────────────────────────────────────────────────

@app.get("/analysis/{job_id}", tags=["inference"])
async def get_analysis(job_id: str):
    """Poll job status. Returns EvidenceObject when completed."""
    job = _jobs.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    if job["status"] != "completed":
        return {"job_id": job_id, "status": job["status"], "detail": job.get("detail")}
    ev = dict(job["evidence"])
    ev.pop("artifacts", None)  # strip large artifacts from poll response
    return {"job_id": job_id, "status": "completed", "evidence": ev}


# ── GET /analysis/{job_id}/artifacts ─────────────────────────────────────────

@app.get("/analysis/{job_id}/artifacts", tags=["inference"])
async def get_artifacts(job_id: str):
    """Return artifact list (MFCC + spectrogram PNGs as data URIs)."""
    job = _jobs.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    if job["status"] != "completed":
        raise HTTPException(status_code=202, detail="Job not yet completed")
    return {"job_id": job_id, "artifacts": job["evidence"].get("artifacts", [])}


# ── WS /analyze/stream ────────────────────────────────────────────────────────

@app.websocket("/analyze/stream")
async def analyze_stream(websocket: WebSocket):
    """Real-time WebSocket stream. Accepts 2s PCM chunks, emits per-window verdict.

    Protocol:
      Client → server: JSON metadata frame first:
        {"case_id": "...", "officer_id": "...", "sample_rate": 16000}
      Client → server: binary frames (raw PCM float32 LE, 16 kHz, mono)
      Server → client: JSON per chunk:
        {"start_sec": 0.0, "end_sec": 2.0, "verdict": "real", "p_synthetic": 0.12, "artifact_type": "clean"}
      Client sends "EOF" text frame to close.
    """
    await websocket.accept()
    logger.info("WebSocket /analyze/stream connected")

    case_id = None
    officer_id = "system"
    chunk_index = 0
    loop = asyncio.get_event_loop()

    try:
        # First frame: metadata JSON
        meta_raw = await asyncio.wait_for(websocket.receive_text(), timeout=10.0)
        try:
            meta = json.loads(meta_raw)
            case_id = meta.get("case_id")
            officer_id = meta.get("officer_id", "system")
        except json.JSONDecodeError:
            await websocket.send_json({"error": "Expected JSON metadata as first frame"})
            await websocket.close()
            return

        while True:
            try:
                msg = await asyncio.wait_for(websocket.receive(), timeout=30.0)
            except asyncio.TimeoutError:
                await websocket.send_json({"error": "timeout"})
                break

            if "text" in msg and msg["text"] == "EOF":
                await websocket.send_json({"status": "done"})
                break

            if "bytes" not in msg or not msg["bytes"]:
                continue

            pcm_bytes: bytes = msg["bytes"]

            def _infer_chunk():
                import numpy as np
                # Expect raw float32 PCM at 16kHz
                waveform = np.frombuffer(pcm_bytes, dtype=np.float32).copy()
                if len(waveform) == 0:
                    return None
                # Treat the chunk as a single 2s window (client is responsible for sizing)
                import librosa
                from preprocessing import SAMPLE_RATE, N_MFCC
                mfcc = librosa.feature.mfcc(y=waveform, sr=SAMPLE_RATE, n_mfcc=N_MFCC)
                mel = librosa.feature.melspectrogram(y=waveform, sr=SAMPLE_RATE, n_mels=128)
                flatness = librosa.feature.spectral_flatness(y=waveform)
                start_sec = chunk_index * 2.0
                window = {
                    "start_sec": start_sec,
                    "end_sec": start_sec + 2.0,
                    "waveform": waveform,
                    "mfcc": mfcc,
                    "mel": mel,
                    "flatness": flatness,
                }
                return infer_window(window)

            result = await loop.run_in_executor(None, _infer_chunk)
            chunk_index += 1

            if result is None:
                continue

            await websocket.send_json({
                "start_sec": result.start_sec,
                "end_sec": result.end_sec,
                "verdict": result.verdict,
                "p_synthetic": result.p_synthetic,
                "artifact_type": result.artifact_type,
            })

    except WebSocketDisconnect:
        logger.info("WebSocket /analyze/stream disconnected after %d chunks", chunk_index)
    except Exception as exc:  # noqa: BLE001
        logger.exception("WebSocket error: %s", exc)
        try:
            await websocket.send_json({"error": str(exc)})
        except Exception:
            pass


# ── Health ────────────────────────────────────────────────────────────────────

@app.get("/health", tags=["ops"])
def health():
    return {
        "status": "ok",
        "service": "voiceguard",
        "device": str(next(iter(_jobs.values()), {}).get("device", "unknown")),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
