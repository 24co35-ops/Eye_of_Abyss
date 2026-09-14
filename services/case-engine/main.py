"""Case Engine -- Investigation orchestrator + blockchain anchoring. Port 8000."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Case Engine", version="0.1.0", description="Investigation case orchestrator")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.get("/health")
def health():
    return {"status": "ok", "service": "case-engine"}


# ponytail: stubs matching design-doc API contract

@app.post("/cases")
async def create_case():
    return {"status": "not_implemented"}


@app.get("/cases")
async def list_cases():
    return {"cases": [], "status": "not_implemented"}


@app.get("/cases/{case_id}")
async def get_case(case_id: str):
    return {"case_id": case_id, "status": "not_implemented"}


@app.post("/cases/{case_id}/evidence")
async def submit_evidence(case_id: str):
    return {"case_id": case_id, "status": "not_implemented"}


@app.get("/cases/{case_id}/convergence")
async def get_convergence(case_id: str):
    return {"case_id": case_id, "status": "not_implemented"}


@app.post("/cases/{case_id}/anchor")
async def anchor_case(case_id: str):
    return {"case_id": case_id, "status": "not_implemented"}


@app.get("/cases/{case_id}/export")
async def export_case(case_id: str):
    return {"case_id": case_id, "status": "not_implemented"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
