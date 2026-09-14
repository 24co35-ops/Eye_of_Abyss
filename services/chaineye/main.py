"""ChainEye -- Cryptocurrency forensics service. Port 8003."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="ChainEye", version="0.1.0", description="Cryptocurrency forensics")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.get("/health")
def health():
    return {"status": "ok", "service": "chaineye"}


# ponytail: stubs -- implement when GNN and blockchain APIs are wired

@app.post("/trace/wallet")
async def trace_wallet():
    return {"status": "not_implemented"}


@app.post("/trace/transaction")
async def trace_transaction():
    return {"status": "not_implemented"}


@app.get("/trace/{job_id}")
async def get_trace(job_id: str):
    return {"job_id": job_id, "status": "not_implemented"}


@app.get("/attribution/{address}")
async def get_attribution(address: str):
    return {"address": address, "status": "not_implemented"}


@app.post("/predict/withdrawal")
async def predict_withdrawal():
    return {"status": "not_implemented"}


@app.get("/graph/{wallet_id}")
async def get_graph(wallet_id: str):
    return {"wallet_id": wallet_id, "status": "not_implemented"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
