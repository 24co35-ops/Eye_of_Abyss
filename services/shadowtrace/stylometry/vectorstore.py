"""ShadowTrace — pgvector fingerprint store with in-memory fallback.

Production: PostgreSQL + pgvector extension (vector similarity search).
Dev/test: in-memory dict (exact cosine search, O(n) — fine for <10k actors).

# ponytail: in-memory fallback; swap for pgvector when DATABASE_URL is set
"""

from __future__ import annotations

import logging
import os
import uuid
from dataclasses import dataclass, field
from typing import Optional

import numpy as np

from stylometry.features import cosine_similarity, FINGERPRINT_DIM

logger = logging.getLogger(__name__)

DATABASE_URL = os.environ.get("DATABASE_URL", "")

# ── In-memory store ───────────────────────────────────────────────────────────

@dataclass
class ActorRecord:
    actor_id: str
    handle: str
    platform: str
    vector: np.ndarray
    metadata: dict = field(default_factory=dict)


_store: dict[str, ActorRecord] = {}  # actor_id → ActorRecord


def upsert_actor(
    actor_id: str,
    handle: str,
    platform: str,
    vector: np.ndarray,
    metadata: dict | None = None,
) -> None:
    _store[actor_id] = ActorRecord(
        actor_id=actor_id,
        handle=handle,
        platform=platform,
        vector=vector.astype(np.float32),
        metadata=metadata or {},
    )


def knn_search(query: np.ndarray, k: int = 5) -> list[dict]:
    """Return top-k actor matches by cosine similarity."""
    if not _store:
        return []
    results = []
    q = query.astype(np.float32)
    for rec in _store.values():
        sim = cosine_similarity(q, rec.vector)
        results.append({
            "actor_id": rec.actor_id,
            "handle": rec.handle,
            "platform": rec.platform,
            "similarity": round(sim, 4),
            "metadata": rec.metadata,
        })
    results.sort(key=lambda x: x["similarity"], reverse=True)
    return results[:k]


def get_all_actors() -> list[ActorRecord]:
    return list(_store.values())


def get_actor(actor_id: str) -> Optional[ActorRecord]:
    return _store.get(actor_id)


def store_size() -> int:
    return len(_store)


# ── pgvector path (active when DATABASE_URL is set) ───────────────────────────
# ponytail: only connect when env var present; keeps tests and CI fast

def _try_pgvector_upsert(actor_id: str, handle: str, platform: str, vector: np.ndarray, metadata: dict) -> bool:
    """Attempt to write to PostgreSQL pgvector. Returns True on success."""
    try:
        import psycopg2
        from pgvector.psycopg2 import register_vector
        conn = psycopg2.connect(DATABASE_URL)
        register_vector(conn)
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS actor_fingerprints (
                    actor_id TEXT PRIMARY KEY,
                    handle TEXT,
                    platform TEXT,
                    vector vector(%s),
                    metadata JSONB
                )
            """, (FINGERPRINT_DIM,))
            import json
            cur.execute("""
                INSERT INTO actor_fingerprints (actor_id, handle, platform, vector, metadata)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (actor_id) DO UPDATE
                    SET handle=EXCLUDED.handle, platform=EXCLUDED.platform,
                        vector=EXCLUDED.vector, metadata=EXCLUDED.metadata
            """, (actor_id, handle, platform, vector.tolist(), json.dumps(metadata)))
        conn.commit()
        conn.close()
        return True
    except Exception as exc:  # noqa: BLE001
        logger.debug("pgvector upsert skipped: %s", exc)
        return False
