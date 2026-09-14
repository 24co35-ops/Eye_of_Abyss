"""ShadowTrace — Dark web actor attribution service. Port 8002."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="ShadowTrace", version="0.1.0", description="Dark web actor attribution")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.get("/health")
def health():
    return {"status": "ok", "service": "shadowtrace"}


# ponytail: stubs — implement when corpus and models are ready

@app.post("/fingerprint")
async def fingerprint():
    return {"status": "not_implemented"}


@app.post("/attribute")
async def attribute():
    return {"status": "not_implemented"}


@app.get("/actors/{actor_id}")
async def get_actor(actor_id: str):
    return {"actor_id": actor_id, "status": "not_implemented"}


@app.post("/actors")
async def add_actor():
    return {"status": "not_implemented"}


@app.get("/graph/export")
async def export_graph():
    return {"status": "not_implemented"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
