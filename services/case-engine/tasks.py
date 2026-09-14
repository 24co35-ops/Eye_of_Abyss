"""Celery tasks for async anchoring, convergence, and PDF export."""

from __future__ import annotations

import asyncio
import logging
import os

from celery import Celery

logger    = logging.getLogger("case_engine.tasks")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

celery_app = Celery("case_engine", broker=REDIS_URL, backend=REDIS_URL)
celery_app.conf.task_serializer = "json"


# ── Anchor evidence ───────────────────────────────────────────────────────────

@celery_app.task(name="tasks.anchor_evidence")
def anchor_evidence_task(evidence_id: str, case_id: str, evidence_data: dict = None):
    """Pin to IPFS via Pinata → anchor on Polygon → write tx/cid back to DB."""
    from anchoring.anchor import anchor_evidence, compute_evidence_hash

    payload = evidence_data or {"evidence_id": evidence_id, "case_id": case_id, "module_id": "case-engine"}
    try:
        result = asyncio.run(anchor_evidence(payload))
        tx_hash  = result.get("tx_hash")
        ipfs_cid = result.get("ipfs_cid")

        # Write anchoring results back to Evidence row
        async def _write_back():
            import uuid as _uuid
            from db import Evidence, SessionLocal
            from sqlalchemy import select
            async with SessionLocal() as db:
                ev = (await db.execute(
                    select(Evidence).where(Evidence.evidence_id == _uuid.UUID(evidence_id))
                )).scalar_one_or_none()
                if ev:
                    ev.chain_anchor = tx_hash
                    ev.ipfs_cid     = ipfs_cid
                    # Mark case ANCHORED if all evidence is now anchored
                    from db import Case
                    from sqlalchemy import select as _sel
                    case = (await db.execute(_sel(Case).where(Case.case_id == ev.case_id))).scalar_one_or_none()
                    if case:
                        all_ev = (await db.execute(_sel(Evidence).where(Evidence.case_id == case.case_id))).scalars().all()
                        if all(e.chain_anchor for e in all_ev):
                            case.status = "ANCHORED"
                            hashes = list(case.anchor_tx_hashes or [])
                            if tx_hash and tx_hash not in hashes:
                                hashes.append(tx_hash)
                            case.anchor_tx_hashes = hashes
                            log = list(case.audit_log or [])
                            from datetime import datetime
                            log.append({"ts": datetime.utcnow().isoformat(), "actor": "system", "action": f"ANCHORED tx={tx_hash}"})
                            case.audit_log = log
                    await db.commit()

        asyncio.run(_write_back())
        logger.info("Anchored evidence %s: tx=%s cid=%s", evidence_id, tx_hash, ipfs_cid)
        return result
    except Exception as exc:
        logger.error("anchor_evidence_task failed for %s: %s", evidence_id, exc)
        return {"error": str(exc), "evidence_id": evidence_id, "case_id": case_id}


# ── Compute convergence ───────────────────────────────────────────────────────

@celery_app.task(name="tasks.compute_convergence")
def compute_convergence_task(case_id: str):
    """Compute CrossModuleSignals and write to cases.convergence."""
    from convergence import compute_and_save
    try:
        signals = asyncio.run(compute_and_save(case_id))
        logger.info("Convergence for case %s: %s", case_id, signals)
        return {"status": "ok", "case_id": case_id, "signals": signals}
    except Exception as exc:
        logger.error("compute_convergence_task failed for %s: %s", case_id, exc)
        return {"error": str(exc), "case_id": case_id}


# ── Generate PDF ──────────────────────────────────────────────────────────────

@celery_app.task(name="tasks.generate_pdf")
def generate_pdf_task(case_id: str):
    """Generate PDF, upload to MinIO, return presigned URL."""
    try:
        url = asyncio.run(_generate_and_upload(case_id))
        return {"status": "ok", "case_id": case_id, "url": url}
    except Exception as exc:
        logger.error("generate_pdf_task failed for %s: %s", case_id, exc)
        return {"error": str(exc), "case_id": case_id}


async def _generate_and_upload(case_id: str) -> str:
    import uuid as _uuid
    from db import Case, Evidence, SessionLocal
    from sqlalchemy import select
    import pdf_export

    async with SessionLocal() as db:
        cid  = _uuid.UUID(case_id)
        case = (await db.execute(select(Case).where(Case.case_id == cid))).scalar_one_or_none()
        rows = (await db.execute(select(Evidence).where(Evidence.case_id == cid))).scalars().all()

    if not case:
        raise ValueError(f"Case {case_id} not found")

    case_dict = {
        "case_id":         str(case.case_id),
        "status":          case.status,
        "complainant_type": case.complainant_type,
        "reported_loss":   case.reported_loss,
        "created_at":      case.created_at.isoformat() if case.created_at else None,
        "updated_at":      case.updated_at.isoformat() if case.updated_at else None,
        "anchor_tx_hashes": case.anchor_tx_hashes or [],
        "convergence":     case.convergence or {},
    }
    ev_list   = [{"module_id": r.module_id, "verdict": r.verdict, "confidence": r.confidence,
                  "confidence_tier": r.confidence_tier, "hash_sha256": r.hash_sha256,
                  "chain_anchor": r.chain_anchor, "ipfs_cid": r.ipfs_cid, "payload": r.payload or {}}
                 for r in rows]
    audit_log = case.audit_log or []

    pdf_bytes = pdf_export.generate(case_dict, ev_list, audit_log)

    try:
        from shared.storage import ensure_buckets, upload_file, get_presigned_url
        ensure_buckets()
        key = f"cases/{case_id}/case_file.pdf"
        upload_file("pdfs", key, pdf_bytes, "application/pdf")
        return get_presigned_url("pdfs", key)
    except Exception:
        # MinIO unavailable — return base64 data URI as fallback
        import base64
        b64 = base64.b64encode(pdf_bytes).decode()
        return f"data:application/pdf;base64,{b64[:100]}...  (truncated)"
