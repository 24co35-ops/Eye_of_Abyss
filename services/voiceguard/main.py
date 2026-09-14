"""VoiceGuard — Voice deepfake detection service. Port 8001."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="VoiceGuard", version="0.1.0", description="Voice deepfake detection")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.get("/health")
def health():
    return {"status": "ok", "service": "voiceguard"}


# ponytail: API stubs below — implement when models are ready

@app.post("/analyze/file")
async def analyze_file():
    return {"status": "not_implemented"}


@app.get("/analysis/{job_id}")
async def get_analysis(job_id: str):
    return {"job_id": job_id, "status": "not_implemented"}


@app.get("/analysis/{job_id}/artifacts")
async def get_artifacts(job_id: str):
    return {"job_id": job_id, "artifacts": []}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
