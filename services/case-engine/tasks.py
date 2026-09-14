"""Celery task stubs for async anchoring and PDF export."""

import os
from celery import Celery

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

celery_app = Celery("case_engine", broker=REDIS_URL, backend=REDIS_URL)
celery_app.conf.task_serializer = "json"


@celery_app.task(name="tasks.anchor_evidence")
def anchor_evidence_task(evidence_id: str, case_id: str):
    """
    TODO: Wire anchoring.anchor_on_polygon() here.
    Runs async from the /anchor endpoint so the HTTP response is immediate.
    """
    # ponytail: stub — log and return until web3 is wired
    print(f"[anchor_evidence] evidence={evidence_id} case={case_id} — stub, not yet anchored")
    return {"status": "stub", "evidence_id": evidence_id}


@celery_app.task(name="tasks.generate_pdf")
def generate_pdf_task(case_id: str):
    """
    TODO: Use reportlab to render case file PDF and upload to Supabase Storage.
    Target: < 10s generation time (design-doc acceptance criteria).
    """
    print(f"[generate_pdf] case={case_id} — stub, PDF not yet generated")
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
    print(f"[compute_convergence] case={case_id} — stub")
    return {"status": "stub", "case_id": case_id}
