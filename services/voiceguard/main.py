"""VoiceGuard — Voice deepfake detection service. Port 8001."""

import os
import sys
import uuid
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Shared package import path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "shared")))

try:
    from shared.schemas import Artifact, EvidenceObject, ModuleEvidence
except ImportError:
    from schemas import Artifact, EvidenceObject, ModuleEvidence  # type: ignore

app = FastAPI(title="VoiceGuard", version="0.1.0", description="Voice deepfake detection")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.get("/health", tags=["ops"])
def health():
    return {"status": "ok", "service": "voiceguard"}


# ponytail: API stubs below — implement when models are ready

@app.post("/analyze/file", tags=["inference"])
async def analyze_file():
    job_id = str(uuid.uuid4())
    return {
        "job_id": job_id,
        "status": "queued",
        "service": "voiceguard",
    }


@app.get("/analysis/{job_id}", tags=["inference"])
async def get_analysis(job_id: str):
    return {
        "job_id": job_id,
        "verdict": "SYNTHETIC_TTS",
        "confidence": 0.914,
        "confidence_tier": "high",
        "status": "completed",
    }


@app.get("/analysis/{job_id}/artifacts", tags=["inference"])
async def get_artifacts(job_id: str):
    return {
        "job_id": job_id,
        "artifacts": [
            Artifact(filename="waveform.json", file_type="application/json", description="Waveform timeline").model_dump(),
            Artifact(filename="spectrogram.png", file_type="image/png", description="Mel spectrogram heatmap").model_dump(),
        ],
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
