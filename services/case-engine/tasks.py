"""Celery tasks for async anchoring, convergence, and PDF export."""

import asyncio
import os
import logging
from celery import Celery

logger = logging.getLogger("case_engine.tasks")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

celery_app = Celery("case_engine", broker=REDIS_URL, backend=REDIS_URL)
celery_app.conf.task_serializer = "json"


@celery_app.task(name="tasks.anchor_evidence")
def anchor_evidence_task(evidence_id: str, case_id: str, evidence_data: dict = None):
    """
    Executes anchoring flow for an evidence record:
      1. Pin to Pinata -> IPFS CID
      2. Compute SHA-256 hash
      3. Submit to Polygon EvidenceRegistry contract
      4. Returns anchoring receipt
    try:
        from anchoring.anchor import anchor_evidence, compute_evidence_hash
    except ImportError:
        from services.case_engine.anchoring.anchor import anchor_evidence, compute_evidence_hash

    payload = evidence_data or {
        "evidence_id": evidence_id,
        "case_id": case_id,
        "module_id": "case-engine",
    }

    try:
        result = asyncio.run(anchor_evidence(payload))
        logger.info(f"[anchor_evidence] Anchored evidence {evidence_id}: tx={result.get('tx_hash')}")
        return result
    except Exception as e:
        logger.error(f"[anchor_evidence] Failed to anchor evidence {evidence_id}: {e}")
        return {"error": str(e), "evidence_id": evidence_id, "case_id": case_id}


@celery_app.task(name="tasks.generate_pdf")
def generate_pdf_task(case_id: str):
    """
    TODO: Use reportlab to render case file PDF and upload to Supabase Storage.
    Target: < 10s generation time (design-doc acceptance criteria).
    """
    logger.info(f"[generate_pdf] case={case_id} — stub, PDF not yet generated")
    return {"status": "stub", "case_id": case_id}


@celery_app.task(name="tasks.compute_convergence")
def compute_convergence_task(case_id: str):
    """
    TODO: Pull all evidence for case, compute CrossModuleSignals:
      1. Extract timezone from ShadowTrace temporal profile
      2. Extract withdrawal hours from ChainEye wallet profile
      3. Compute overlap score
      4. Check Neo4j for actor graph links
      5. Write CrossModuleSignals back to cases table
    """
    logger.info(f"[compute_convergence] case={case_id} — stub")
    return {"status": "stub", "case_id": case_id}
