"""ShadowTrace — Dark web actor attribution & stylometry service. Port 8002."""

import os
import sys
import uuid

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Shared package import path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "shared")))

try:
    from shared.schemas import Artifact, CriminalActorProfile, EvidenceObject, ModuleEvidence
except ImportError:
    from schemas import Artifact, CriminalActorProfile, EvidenceObject, ModuleEvidence  # type: ignore

app = FastAPI(title="ShadowTrace", version="0.1.0", description="Dark web actor attribution")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.get("/health", tags=["ops"])
def health():
    return {"status": "ok", "service": "shadowtrace"}


# ponytail: API stubs below — implement when pipeline and models are ready

@app.post("/fingerprint", tags=["attribution"])
async def fingerprint_text(payload: dict):
    return {
        "fingerprint_id": str(uuid.uuid4()),
        "stylometric_vector_dim": 128,
        "status": "computed",
    }


@app.post("/attribute", tags=["attribution"])
async def attribute_actor(payload: dict):
    return {
        "matched_actor_id": str(uuid.uuid4()),
        "archetype": "darknet_vendor",
        "confidence": 0.88,
        "timezone_estimate": "UTC+3",
    }


@app.get("/actors/{actor_id}", tags=["attribution"])
async def get_actor(actor_id: str):
    return CriminalActorProfile(
        actor_id=uuid.UUID(actor_id) if len(actor_id) == 36 else uuid.uuid4(),
        archetype="investment_fraudster",
        handles=["@phantom_fx", "dark_broker_99"],
        platforms=["telegram", "dread", "exploit_in"],
        timezone="UTC+3",
        active_hours=[14, 15, 16, 17, 18, 19, 20, 21, 22],
        wallet_addresses=["0x71C...498B", "bc1q...9xyz"],
    ).model_dump()


@app.get("/graph/export", tags=["attribution"])
async def export_actor_graph():
    return {"nodes": [], "edges": []}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
