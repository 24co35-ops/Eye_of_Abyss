"""ChainEye — Crypto forensics & transaction tracking service. Port 8003."""

import os
import sys
import uuid

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Shared package import path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "shared")))

try:
    from shared.schemas import Artifact, EvidenceObject, ModuleEvidence
except ImportError:
    from schemas import Artifact, EvidenceObject, ModuleEvidence  # type: ignore

app = FastAPI(title="ChainEye", version="0.1.0", description="Crypto forensics & transaction tracking")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.get("/health", tags=["ops"])
def health():
    return {"status": "ok", "service": "chaineye"}


# ponytail: API stubs below — implement when GNN & on-chain data clients are ready

@app.post("/trace/wallet", tags=["forensics"])
async def trace_wallet(payload: dict):
    return {
        "wallet_address": payload.get("wallet_address", "0x71C83638379185a61142b19127765F14f0D6498B"),
        "total_volume_usd": 142500.00,
        "risk_score": 0.89,
        "cluster_tag": "Tornado.Cash Cashout",
        "hops": 3,
    }


@app.post("/trace/tx", tags=["forensics"])
async def trace_tx(payload: dict):
    return {
        "tx_hash": payload.get("tx_hash", "0xabc...123"),
        "status": "traced",
        "destination_entity": "Binance Hot Wallet 6",
    }


@app.post("/predict/withdrawal", tags=["forensics"])
async def predict_withdrawal(payload: dict):
    return {
        "predicted_window_utc": "18:00 - 22:00 UTC",
        "confidence": 0.84,
        "probable_destinations": ["Binance", "FixedFloat", "ChangeNOW"],
    }


@app.get("/graph", tags=["forensics"])
async def get_transaction_graph():
    return {"nodes": [], "edges": []}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
