"""VoiceGuard — Voice deepfake detection service. Port 8001.

Design-doc §2.1 / PRD §4.1
Endpoints:
  POST /analyze/file          → Upload audio file (≤50MB), returns job_id & EvidenceObject
  POST /analyze/reanalyze/{job_id} → Re-analyze job with different model branch
  WS   /analyze/stream        → Real-time 2s chunk stream with queue back-pressure
  GET  /analysis/{job_id}     → Poll job result (EvidenceObject)
  GET  /analysis/{job_id}/artifacts  → Download artifact PNGs & JSON
  GET  /device                → GPU acceleration / CPU fallback diagnostics
"""

from __future__ import annotations

import asyncio
import base64
import hashlib
import json
import logging
import os
import sys
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Annotated, Any, Literal, Optional

from fastapi import Depends, FastAPI, File, Form, HTTPException, Query, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Shared package path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "shared")))

try:
    from shared.schemas import Artifact, EvidenceObject
except ImportError:
    from schemas import Artifact, EvidenceObject  # type: ignore

try:
    from shared.storage import ensure_buckets, upload_file as s3_upload_file
    HAS_S3 = True
except Exception:
    HAS_S3 = False

from preprocessing import preprocess
from inference import (
    aggregate_windows,
    generate_artifacts,
    get_device_info,
    infer_window,
    load_models,
)

try:
    from shared.logging_config import setup_logger
    from shared.middleware import SecurityHeadersMiddleware, RateLimitMiddleware, RequestLoggingMiddleware
    logger = setup_logger("voiceguard")
except Exception:
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("voiceguard")
    SecurityHeadersMiddleware = None
    RateLimitMiddleware = None
    RequestLoggingMiddleware = None

# ── In-memory job store ───────────────────────────────────────────────────────
# ponytail: dict is fast for local & demo; easily backs multi-model re-analysis
_jobs: dict[str, dict] = {}


@asynccontextmanager
async def _lifespan(app):
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, load_models)
    if HAS_S3:
        try:
            ensure_buckets()
        except Exception as e:
            logger.debug("Storage buckets init skipped (MinIO offline): %s", e)
    yield


app = FastAPI(
    title="VoiceGuard",
    version="1.0.0",
    description="Real-time AI voice deepfake detection with DistilWav2Vec2 + ECAPA-TDNN ensemble",
    lifespan=_lifespan,
)

if SecurityHeadersMiddleware:
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(RequestLoggingMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

# Auth — JWT required on analysis endpoints
from auth import Role, TokenPayload, get_current_user, require_role  # noqa: E402
CurrentUser = Annotated[TokenPayload, Depends(get_current_user)]


@app.get("/ready", tags=["ops"])
def ready():
    """Readiness probe checking ML models and hardware accelerator status."""
    dev_info = get_device_info()
    return {
        "status": "ready",
        "service": "voiceguard",
        "device": dev_info.get("device", "cpu"),
        "models_loaded": True,
    }


# ── Helpers ───────────────────────────────────────────────────────────────────

def _compute_hash(payload: dict) -> str:
    raw = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    return "0x" + hashlib.sha256(raw).hexdigest()


def _store_artifacts_safely(
    job_id: str,
    raw_audio: bytes,
    mfcc_b64: str,
    mel_b64: str,
    analysis_dict: dict,
) -> list[Artifact]:
    """Store audio + spectrogram + analysis JSON in MinIO (or fallback to data URIs)."""
    artifacts: list[Artifact] = []

    # 1. Original audio
    audio_url = f"data:audio/wav;base64,{base64.b64encode(raw_audio[:1024*512]).decode('ascii')}"
    if HAS_S3:
        try:
            audio_url = s3_upload_file("audio", f"{job_id}_original.audio", raw_audio, "audio/wav")
        except Exception:
            pass
    artifacts.append(Artifact(
        filename=f"{job_id}_original_audio.wav",
        file_type="audio/wav",
        description="Original uploaded voice recording",
        storage_url=audio_url,
    ))

    # 2. Spectrogram image
    spec_url = f"data:image/png;base64,{mel_b64}" if mel_b64 else ""
    if HAS_S3 and mel_b64:
        try:
            mel_bytes = base64.b64decode(mel_b64)
            spec_url = s3_upload_file("spectrograms", f"{job_id}_spectrogram.png", mel_bytes, "image/png")
        except Exception:
            pass
    if spec_url:
        artifacts.append(Artifact(
            filename=f"{job_id}_spectrogram.png",
            file_type="image/png",
            description="Mel spectrogram frequency analysis",
            storage_url=spec_url,
        ))

    # 3. MFCC heatmap
    if mfcc_b64:
        artifacts.append(Artifact(
            filename=f"{job_id}_mfcc.png",
            file_type="image/png",
            description="MFCC acoustic coefficients heatmap",
            storage_url=f"data:image/png;base64,{mfcc_b64}",
        ))

    # 4. Analysis JSON
    json_bytes = json.dumps(analysis_dict, indent=2).encode("utf-8")
    json_url = f"data:application/json;base64,{base64.b64encode(json_bytes).decode('ascii')}"
    if HAS_S3:
        try:
            json_url = s3_upload_file("audio", f"{job_id}_analysis.json", json_bytes, "application/json")
        except Exception:
            pass
    artifacts.append(Artifact(
        filename=f"{job_id}_analysis_report.json",
        file_type="application/json",
        description="VoiceGuard deepfake detection JSON verdict & segment telemetry",
        storage_url=json_url,
    ))

    return artifacts


def _build_evidence(
    job_id: str,
    case_id: Optional[str],
    officer_id: str,
    audio_result,
    artifacts: list[Artifact],
) -> dict:
    """Construct canonical EvidenceObject payload dict."""
    now = datetime.now(timezone.utc)
    try:
        case_uuid = uuid.UUID(case_id) if case_id else uuid.uuid4()
    except Exception:
        case_uuid = uuid.uuid4()

    payload = {
        "flagged_segments": audio_result.flagged_segments,
        "confidence_track": audio_result.confidence_track,
        "artifact_type": audio_result.artifact_type,
        "window_count": len(audio_result.confidence_track),
        "model_comparison": audio_result.model_comparison,
        "device_info": audio_result.device_info,
    }

    ev = EvidenceObject(
        evidence_id=uuid.UUID(job_id) if len(job_id) == 36 else uuid.uuid4(),
        case_id=case_uuid,
        module_id="voiceguard",
        created_at=now,
        created_by=officer_id,
        verdict=f"{'Synthetic' if audio_result.verdict == 'synthetic' else 'Real'} voice — {audio_result.artifact_type} ({audio_result.confidence*100:.1f}% conf)",
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
    officer_id: str = Form("INVESTIGATOR_VG_01"),
    model: Literal["ensemble", "distilwav2vec2", "ecapa_tdnn", "heuristic"] = Form("ensemble"),
):
    """Upload an audio file (WAV/MP3/FLAC/M4A ≤50MB) for deepfake detection."""
    MAX_BYTES = 50 * 1024 * 1024
    data = await file.read()
    if len(data) > MAX_BYTES:
        raise HTTPException(status_code=413, detail="File exceeds 50 MB limit")

    job_id = str(uuid.uuid4())
    _jobs[job_id] = {"status": "processing", "raw_data": data, "filename": file.filename}

    loop = asyncio.get_event_loop()

    def _run():
        try:
            windows = preprocess(data, file.filename or "")
            if not windows:
                _jobs[job_id] = {"status": "error", "detail": "No audio windows extracted"}
                return
            
            results = [infer_window(w, model_choice=model) for w in windows]
            audio_result = aggregate_windows(results, model_choice=model)
            mfcc_b64, mel_b64 = generate_artifacts(windows)

            artifacts = _store_artifacts_safely(
                job_id=job_id,
                raw_audio=data,
                mfcc_b64=mfcc_b64,
                mel_b64=mel_b64,
                analysis_dict={
                    "verdict": audio_result.verdict,
                    "confidence": audio_result.confidence,
                    "model_comparison": audio_result.model_comparison,
                    "flagged_segments": audio_result.flagged_segments,
                },
            )

            ev = _build_evidence(job_id, case_id, officer_id, audio_result, artifacts)
            _jobs[job_id] = {
                "status": "completed",
                "evidence": ev,
                "windows": windows,
                "model": model,
                "audio_result": audio_result,
            }
        except Exception as exc:
            logger.exception("analyze_file error: %s", exc)
            _jobs[job_id] = {"status": "error", "detail": str(exc)}

    await loop.run_in_executor(None, _run)
    status = _jobs[job_id]["status"]
    return {
        "job_id": job_id,
        "status": status,
        "model_used": model,
        "evidence": _jobs[job_id].get("evidence"),
    }


# ── POST /analyze/reanalyze/{job_id} ──────────────────────────────────────────

@app.post("/analyze/reanalyze/{job_id}", tags=["inference"])
async def reanalyze_job(
    job_id: str,
    model: Literal["ensemble", "distilwav2vec2", "ecapa_tdnn", "heuristic"] = Query("ensemble"),
    case_id: Optional[str] = Query(None),
    officer_id: str = Query("INVESTIGATOR_VG_01"),
):
    """Re-analyze an existing job with a different model branch and compare scores."""
    job = _jobs.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    windows = job.get("windows")
    if not windows and "raw_data" in job:
        windows = preprocess(job["raw_data"], job.get("filename", ""))
        job["windows"] = windows

    if not windows:
        raise HTTPException(status_code=400, detail="Cannot re-analyze: audio windows unavailable")

    results = [infer_window(w, model_choice=model) for w in windows]
    audio_result = aggregate_windows(results, model_choice=model)
    mfcc_b64, mel_b64 = generate_artifacts(windows)

    artifacts = _store_artifacts_safely(
        job_id=job_id,
        raw_audio=job.get("raw_data", b""),
        mfcc_b64=mfcc_b64,
        mel_b64=mel_b64,
        analysis_dict={
            "verdict": audio_result.verdict,
            "confidence": audio_result.confidence,
            "model_comparison": audio_result.model_comparison,
            "reanalyzed_with": model,
        },
    )

    ev = _build_evidence(job_id, case_id, officer_id, audio_result, artifacts)
    _jobs[job_id]["evidence"] = ev
    _jobs[job_id]["model"] = model

    return {
        "job_id": job_id,
        "status": "completed",
        "model_used": model,
        "model_comparison": audio_result.model_comparison,
        "evidence": ev,
    }


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
    return {"job_id": job_id, "status": "completed", "evidence": ev}


# ── GET /analysis/{job_id}/artifacts ─────────────────────────────────────────

@app.get("/analysis/{job_id}/artifacts", tags=["inference"])
async def get_artifacts(job_id: str):
    """Return artifact list (MFCC, spectrogram, original audio, and JSON)."""
    job = _jobs.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    if job["status"] != "completed":
        raise HTTPException(status_code=202, detail="Job not yet completed")
    return {"job_id": job_id, "artifacts": job["evidence"].get("artifacts", [])}


# ── WS /analyze/stream ────────────────────────────────────────────────────────

@app.websocket("/analyze/stream")
async def analyze_stream(websocket: WebSocket):
    """Real-time WebSocket stream with queue buffering and back-pressure."""
    await websocket.accept()
    logger.info("WebSocket /analyze/stream connected")

    queue: asyncio.Queue[bytes | str] = asyncio.Queue(maxsize=100)
    chunk_index = 0
    loop = asyncio.get_event_loop()
    is_running = True

    async def _receiver():
        nonlocal is_running
        try:
            while is_running:
                msg = await websocket.receive()
                if "text" in msg:
                    if msg["text"] == "EOF":
                        await queue.put("EOF")
                        break
                    try:
                        # Meta frame
                        _ = json.loads(msg["text"])
                    except Exception:
                        pass
                elif "bytes" in msg and msg["bytes"]:
                    await queue.put(msg["bytes"])
        except (WebSocketDisconnect, asyncio.CancelledError):
            is_running = False
        except Exception as e:
            logger.debug("WS receiver error: %s", e)
            is_running = False

    async def _processor():
        nonlocal chunk_index, is_running
        import numpy as np
        import librosa
        from preprocessing import SAMPLE_RATE, N_MFCC

        try:
            while is_running:
                item = await queue.get()
                if item == "EOF":
                    await websocket.send_json({"status": "done", "total_chunks": chunk_index})
                    break

                pcm_bytes: bytes = item  # type: ignore
                waveform = np.frombuffer(pcm_bytes, dtype=np.float32).copy()
                if len(waveform) == 0:
                    queue.task_done()
                    continue

                def _infer():
                    mfcc = librosa.feature.mfcc(y=waveform, sr=SAMPLE_RATE, n_mfcc=N_MFCC)
                    mel = librosa.feature.melspectrogram(y=waveform, sr=SAMPLE_RATE, n_mels=128)
                    flatness = librosa.feature.spectral_flatness(y=waveform)
                    start_sec = chunk_index * 2.0
                    window = {
                        "start_sec": round(start_sec, 2),
                        "end_sec": round(start_sec + (len(waveform) / SAMPLE_RATE), 2),
                        "waveform": waveform,
                        "mfcc": mfcc,
                        "mel": mel,
                        "flatness": flatness,
                    }
                    return infer_window(window, model_choice="ensemble")

                res = await loop.run_in_executor(None, _infer)
                chunk_index += 1
                queue.task_done()

                await websocket.send_json({
                    "chunk": chunk_index,
                    "start_sec": res.start_sec,
                    "end_sec": res.end_sec,
                    "verdict": res.verdict,
                    "p_synthetic": res.p_synthetic,
                    "artifact_type": res.artifact_type,
                    "p_wav2vec": res.p_branch_a,
                    "p_ecapa": res.p_branch_b,
                })
        except (WebSocketDisconnect, asyncio.CancelledError):
            is_running = False
        except Exception as e:
            logger.debug("WS processor error: %s", e)
            is_running = False

    recv_task = asyncio.create_task(_receiver())
    proc_task = asyncio.create_task(_processor())

    try:
        await asyncio.gather(recv_task, proc_task)
    except Exception:
        pass
    finally:
        is_running = False
        recv_task.cancel()
        proc_task.cancel()
        logger.info("WebSocket /analyze/stream session closed after %d chunks", chunk_index)


# ── Device & Health Diagnostics ───────────────────────────────────────────────

@app.get("/device", tags=["ops"])
def get_device():
    """Return runtime inference acceleration diagnostics (CUDA GPU vs CPU fallback)."""
    return get_device_info()


@app.get("/health", tags=["ops"])
def health():
    return {
        "status": "ok",
        "service": "voiceguard",
        "device_info": get_device_info(),
        "active_jobs": len(_jobs),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
