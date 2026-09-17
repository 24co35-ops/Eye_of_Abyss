"""Cross-module convergence computation — Eye of Abyss.

Called inline after evidence submission (no Celery needed for ≤3 modules).
Writes CrossModuleSignals back to cases.convergence column.
"""

from __future__ import annotations

import logging
import os
from typing import Optional

logger = logging.getLogger("case_engine.convergence")

NEO4J_URI      = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER     = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "changeme")


# ── Helpers ───────────────────────────────────────────────────────────────────

def _jaccard(a: list[int], b: list[int]) -> float:
    """Hour-set Jaccard similarity."""
    if not a or not b:
        return 0.0
    sa, sb = set(a), set(b)
    return len(sa & sb) / len(sa | sb)


def _cosine(a: list[float], b: list[float]) -> float:
    """Cosine similarity of two equal-length vectors."""
    if len(a) != len(b) or not a:
        return 0.0
    dot  = sum(x * y for x, y in zip(a, b))
    norm = (sum(x**2 for x in a) ** 0.5) * (sum(y**2 for y in b) ** 0.5)
    return dot / norm if norm else 0.0


def _neo4j_actor_link(wallet: Optional[str], handle: Optional[str]) -> Optional[str]:
    """Query Neo4j for a shared actor node between a wallet address and a handle."""
    if not wallet and not handle:
        return None
    try:
        from neo4j import GraphDatabase
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD), connection_timeout=1.0)
        with driver.session() as session:
            if wallet and handle:
                result = session.run(
                    """
                    MATCH (w:Wallet {address: $wallet})<-[:OWNS]-(a:Actor)-[:USES]->(h:Handle {name: $handle})
                    RETURN a.id AS actor_id LIMIT 1
                    """,
                    wallet=wallet.lower(), handle=handle,
                )
            elif wallet:
                result = session.run(
                    "MATCH (w:Wallet {address: $wallet})<-[:OWNS]-(a:Actor) RETURN a.id AS actor_id LIMIT 1",
                    wallet=wallet.lower(),
                )
            else:
                result = session.run(
                    "MATCH (h:Handle {name: $handle})<-[:USES]-(a:Actor) RETURN a.id AS actor_id LIMIT 1",
                    handle=handle,
                )
            record = result.single()
            driver.close()
            return str(record["actor_id"]) if record else None
    except Exception as exc:
        logger.debug("Neo4j actor link query failed (offline?): %s", exc)
        return None


# ── Main computation ──────────────────────────────────────────────────────────

def compute_signals(evidence_list: list[dict]) -> dict:
    """
    Given a list of evidence payload dicts (one per module), compute CrossModuleSignals.

    Expected payload keys (optional, graceful degradation):
      ShadowTrace: payload.active_hours  (list[int] 0-23)
                   payload.top_match.handle
      ChainEye:    payload.active_hours  (list[int] 0-23)
                   payload.wallet_address
      VoiceGuard:  payload.active_hours  (not always present)
    """
    all_hours: list[list[int]] = []
    wallet: Optional[str]      = None
    handle: Optional[str]      = None

    for ev in evidence_list:
        p = ev.get("payload", {}) or {}

        hours = p.get("active_hours") or p.get("temporal_profile", {}).get("active_hours")
        if hours:
            all_hours.append([int(h) for h in hours])

        if not wallet:
            wallet = p.get("wallet_address") or p.get("top_wallet")
        if not handle:
            handle = (p.get("top_match") or {}).get("handle") or p.get("handle")

    # ── Timezone match ────────────────────────────────────────────────────────
    if len(all_hours) >= 2:
        timezone_match = round(_jaccard(all_hours[0], all_hours[1]), 4)
    elif len(all_hours) == 1:
        timezone_match = 0.5  # one source, partial signal
    else:
        timezone_match = None

    # ── Activity overlap (cosine over 24-bin histogram) ───────────────────────
    def _to_hist(hours: list[int]) -> list[float]:
        h = [0.0] * 24
        for hr in hours:
            if 0 <= hr < 24:
                h[hr] += 1.0
        return h

    if len(all_hours) >= 2:
        activity_overlap = round(_cosine(_to_hist(all_hours[0]), _to_hist(all_hours[1])), 4)
    else:
        activity_overlap = None

    # ── Actor graph link ──────────────────────────────────────────────────────
    actor_graph_link = _neo4j_actor_link(wallet, handle)
    if not actor_graph_link and wallet:
        actor_graph_link = f"wallet_{wallet}"  # fallback label

    # ── Convergence confidence ────────────────────────────────────────────────
    scores = [s for s in [timezone_match, activity_overlap] if s is not None]
    graph_bonus = 0.05 if actor_graph_link else 0.0
    convergence_confidence = round((sum(scores) / len(scores) + graph_bonus) if scores else 0.0, 4)
    convergence_confidence = min(convergence_confidence, 1.0)

    return {
        "timezone_match":        timezone_match,
        "activity_overlap":      activity_overlap,
        "actor_graph_link":      actor_graph_link,
        "convergence_confidence": convergence_confidence,
    }


async def compute_and_save(case_id: str) -> dict:
    """Pull evidence from DB, compute signals, write back. Returns the signals dict."""
    from db import Case, Evidence, SessionLocal
    from sqlalchemy import select

    async with SessionLocal() as db:
        import uuid as _uuid
        cid = _uuid.UUID(case_id)
        case = (await db.execute(select(Case).where(Case.case_id == cid))).scalar_one_or_none()
        if not case:
            logger.warning("convergence: case %s not found", case_id)
            return {}

        rows = (await db.execute(select(Evidence).where(Evidence.case_id == cid))).scalars().all()
        ev_list = [{"module_id": r.module_id, "payload": r.payload or {}} for r in rows]

        if len(ev_list) < 2:
            return case.convergence or {}

        signals = compute_signals(ev_list)
        case.convergence = signals
        await db.commit()
        logger.info("convergence computed for case %s: %s", case_id, signals)
        return signals
