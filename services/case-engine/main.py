"""Case Engine — Investigation orchestrator + blockchain anchoring. Port 8000."""

from __future__ import annotations

import io
import json
import os
import sys
import uuid
from datetime import datetime
from typing import Annotated

from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI, File, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Make shared package and local service directory importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "shared")))
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

try:
    from shared.schemas import (
        CaseResponse,
        CreateCaseRequest,
        CrossModuleSignals,
        EvidenceObject,
        ModuleEvidence,
    )
    from shared.logging_config import setup_logger
    from shared.middleware import SecurityHeadersMiddleware, RateLimitMiddleware, RequestLoggingMiddleware
    from shared.webhooks import register_webhook, list_webhooks, remove_webhook, dispatch_webhook_event, WebhookSubscription
    from shared.plugins import register_module, list_modules, get_module, check_module_health, ModuleManifest
    from shared.case_transfer import export_case_package, import_case_package
    from shared.blockchain_adapters import get_blockchain_adapter
except ImportError:
    from schemas import (  # type: ignore
        CaseResponse,
        CreateCaseRequest,
        CrossModuleSignals,
        EvidenceObject,
        ModuleEvidence,
    )
    from logging_config import setup_logger  # type: ignore
    from middleware import SecurityHeadersMiddleware, RateLimitMiddleware, RequestLoggingMiddleware  # type: ignore
    from webhooks import register_webhook, list_webhooks, remove_webhook, dispatch_webhook_event, WebhookSubscription  # type: ignore
    from plugins import register_module, list_modules, get_module, check_module_health, ModuleManifest  # type: ignore
    from case_transfer import export_case_package, import_case_package  # type: ignore
    from blockchain_adapters import get_blockchain_adapter  # type: ignore

logger = setup_logger("case-engine")

from anchoring import anchor_on_polygon, compute_hash, pin_to_ipfs

try:
    from auth import router as auth_router, users_router
except (ImportError, AttributeError):
    import importlib.util as _importlib_util
    _auth_spec = _importlib_util.spec_from_file_location("case_engine_auth", os.path.join(os.path.dirname(__file__), "auth.py"))
    _auth_mod = _importlib_util.module_from_spec(_auth_spec)
    _auth_spec.loader.exec_module(_auth_mod)
    auth_router, users_router = _auth_mod.router, _auth_mod.users_router
from convergence import compute_and_save as compute_convergence_inline
from db import AuditLog, Case, Evidence, create_tables, get_db
from pdf_export import generate as generate_pdf, generate_freeze_json
from state_machine import InvalidTransition, auto_advance, transition
from tasks import anchor_evidence_task, compute_convergence_task, generate_pdf_task

# shared auth — re-export for route dependencies
from shared.auth import Role, TokenPayload, get_current_user, require_role


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables and init components
    logger.info("Initializing Case Engine tables and database pool...")
    await create_tables()
    logger.info("Case Engine startup complete.")
    yield
    # Shutdown: graceful cleanup
    logger.info("Case Engine shutting down cleanly...")


app = FastAPI(
    title="Case Engine",
    version="1.0.0",
    description="Investigation orchestrator & evidence ledger — Eye of Abyss",
    lifespan=lifespan,
)

# Hardened middlewares
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

app.include_router(auth_router)
app.include_router(users_router)

DB = Annotated[AsyncSession, Depends(get_db)]
CurrentUser = Annotated[TokenPayload, Depends(get_current_user)]


# ── Health & Readiness Probes ─────────────────────────────────────────────────

@app.get("/health", tags=["ops"])
def health():
    return {"status": "ok", "service": "case-engine", "version": "1.0.0"}


@app.get("/ready", tags=["ops"])
async def ready(db: DB):
    """Deep readiness probe verifying DB connectivity."""
    try:
        await db.execute(select(Case).limit(1))
        return {
            "status": "ready",
            "database": "connected",
            "service": "case-engine",
            "blockchain": os.getenv("BLOCKCHAIN_NETWORK", "polygon"),
        }
    except Exception as exc:
        logger.error(f"Readiness probe failed: {exc}")
        raise HTTPException(status_code=503, detail=f"Database unavailable: {exc}")



# ── Cases ─────────────────────────────────────────────────────────────────────

@app.post("/cases", status_code=status.HTTP_201_CREATED, tags=["cases"])
async def create_case(
    body: CreateCaseRequest,
    db: DB,
    user: Annotated[TokenPayload, Depends(require_role(Role.INVESTIGATOR, Role.SUPERVISOR, Role.OWNER))],
):
    case = Case(
        case_id=uuid.uuid4(),
        status="CREATED",
        created_by=user.sub,
        complainant_type=body.complainant_type,
        reported_loss=body.reported_loss,
        modules_assigned=body.modules_assigned,
        audit_log=[{"ts": datetime.utcnow().isoformat(), "actor": user.sub, "action": "CREATED"}],
    )
    db.add(case)
    await db.commit()
    await db.refresh(case)
    return _case_response(case, evidence_count=0)


@app.get("/cases", tags=["cases"])
async def list_cases(db: DB, user: CurrentUser):
    rows = (await db.execute(select(Case))).scalars().all()
    results = []
    for c in rows:
        ev_count = len((await db.execute(
            select(Evidence).where(Evidence.case_id == c.case_id)
        )).scalars().all())
        results.append(_case_response(c, ev_count))
    return results


@app.get("/cases/{case_id}", tags=["cases"])
async def get_case(case_id: str, db: DB, user: CurrentUser):
    case = await _get_case_or_404(case_id, db)
    ev_count = len((await db.execute(
        select(Evidence).where(Evidence.case_id == case.case_id)
    )).scalars().all())
    return _case_response(case, ev_count)


# ── Evidence submission ───────────────────────────────────────────────────────

@app.post("/cases/{case_id}/evidence", status_code=status.HTTP_201_CREATED, tags=["evidence"])
async def submit_evidence(
    case_id: str,
    body: ModuleEvidence,
    db: DB,
    user: CurrentUser,
):
    case = await _get_case_or_404(case_id, db)

    # Build canonical dict and hash it
    ev_dict = body.model_dump(mode="json")
    ev_hash = compute_hash(ev_dict)

    # Reject duplicate evidence
    existing = (await db.execute(
        select(Evidence).where(Evidence.hash_sha256 == ev_hash)
    )).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail="Evidence already submitted (duplicate hash)")

    confidence_tier = (
        "high" if body.confidence >= 0.75
        else "medium" if body.confidence >= 0.45
        else "low"
    )

    ev = Evidence(
        evidence_id=body.evidence_id,
        case_id=case.case_id,
        module_id=body.module_id,
        submitted_by=user.sub,
        created_by=user.sub,
        verdict=body.verdict,
        verdict_code=f"{body.module_id.upper()}_VERDICT",
        confidence=body.confidence,
        confidence_tier=confidence_tier,
        artifacts=[a.model_dump() for a in body.artifacts],
        hash_sha256=ev_hash,
    )
    db.add(ev)

    # Auto-advance state machine
    all_ev = (await db.execute(
        select(Evidence).where(Evidence.case_id == case.case_id)
    )).scalars().all()
    submitted_modules = [e.module_id for e in all_ev] + [body.module_id]

    next_status = auto_advance(case.status, submitted_modules, case.modules_assigned or [])
    if next_status:
        case.status = next_status
        case.updated_at = datetime.utcnow()
        _append_audit(case, user.sub, f"AUTO_ADVANCE -> {next_status}")

    await db.commit()

    # Trigger convergence inline when 2+ modules have submitted
    if len(set(submitted_modules)) >= 2:
        try:
            import asyncio
            asyncio.create_task(compute_convergence_inline(str(case.case_id)))
        except Exception:
            try:
                compute_convergence_task.delay(str(case.case_id))
            except Exception:
                pass  # Celery optional in local dev

    return {
        "evidence_id": str(ev.evidence_id),
        "hash_sha256": ev_hash,
        "case_status": case.status,
    }


# ── Convergence ───────────────────────────────────────────────────────────────

@app.get("/cases/{case_id}/convergence", tags=["convergence"])
async def get_convergence(case_id: str, db: DB, user: CurrentUser):
    case = await _get_case_or_404(case_id, db)
    if not case.convergence:
        return {"case_id": case_id, "convergence": None, "note": "Not yet computed"}
    return {"case_id": case_id, "convergence": case.convergence}


# ── Anchoring ─────────────────────────────────────────────────────────────────

@app.post("/cases/{case_id}/anchor", tags=["blockchain"])
async def anchor_case(
    case_id: str,
    db: DB,
    user: Annotated[TokenPayload, Depends(require_role(Role.SUPERVISOR, Role.OWNER))],
):
    """SUPERVISOR+ — triggers Polygon anchoring for all unanchored evidence."""
    case = await _get_case_or_404(case_id, db)

    if case.status not in ("READY_TO_ANCHOR", "CONVERGENCE_COMPUTED", "EVIDENCE_SUBMITTED"):
        raise HTTPException(status_code=400, detail=f"Cannot anchor from status '{case.status}'. Approve first.")

    unanchored = (await db.execute(
        select(Evidence).where(
            Evidence.case_id == case.case_id,
            Evidence.chain_anchor.is_(None),
        )
    )).scalars().all()

    if not unanchored:
        raise HTTPException(status_code=400, detail="No unanchored evidence found")

    # Demo mode: sync anchor one item directly
    demo_mode = os.getenv("DEMO_MODE", "0") == "1"
    queued = 0
    for ev in unanchored:
        try:
            if demo_mode:
                anchor_evidence_task(str(ev.evidence_id), case_id)
            else:
                anchor_evidence_task.delay(str(ev.evidence_id), case_id)
            queued += 1
        except Exception:
            pass

    case.status = "READY_TO_ANCHOR"
    case.updated_at = datetime.utcnow()
    await _audit(db, case, user.sub, "ANCHOR_TRIGGERED", {"evidence_queued": queued})
    await db.commit()

    return {
        "case_id": case_id,
        "status": case.status,
        "evidence_queued": queued,
        "note": "Anchoring tasks queued — poll /cases/{id} for ANCHORED status",
    }


@app.get("/cases/{case_id}/evidence/{evidence_id}/verify", tags=["blockchain"])
async def verify_evidence(case_id: str, evidence_id: str, db: DB, user: CurrentUser):
    """Verifies on-chain anchoring status of an evidence item against EvidenceRegistry."""
    case = await _get_case_or_404(case_id, db)
    try:
        ev_uid = uuid.UUID(evidence_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid evidence_id format")

    ev = (await db.execute(
        select(Evidence).where(Evidence.case_id == case.case_id, Evidence.evidence_id == ev_uid)
    )).scalar_one_or_none()
    if not ev:
        raise HTTPException(status_code=404, detail="Evidence not found")

    try:
        from anchoring.anchor import verify_evidence_onchain
    except ImportError:
        from services.case_engine.anchoring.anchor import verify_evidence_onchain
    verification = verify_evidence_onchain(ev.hash_sha256)
    return {
        "evidence_id": str(ev.evidence_id),
        "case_id": str(case.case_id),
        "hash_sha256": ev.hash_sha256,
        "chain_anchor": ev.chain_anchor,
        "ipfs_cid": ev.ipfs_cid,
        "onchain_verification": verification,
    }



# ── Supervisor approval ───────────────────────────────────────────────────────

@app.post("/cases/{case_id}/approve", tags=["cases"])
async def approve_case(
    case_id: str,
    db: DB,
    user: Annotated[TokenPayload, Depends(require_role(Role.SUPERVISOR, Role.OWNER))],
):
    """SUPERVISOR/OWNER approves case for anchoring → transitions to READY_TO_ANCHOR."""
    case = await _get_case_or_404(case_id, db)
    allowed = {"ACTIVE", "EVIDENCE_SUBMITTED", "CONVERGENCE_COMPUTED"}
    if case.status not in allowed:
        raise HTTPException(status_code=400, detail=f"Cannot approve from status '{case.status}'")
    case.status = "READY_TO_ANCHOR"
    case.updated_at = datetime.utcnow()
    await _audit(db, case, user.sub, "APPROVED_FOR_ANCHORING")
    await db.commit()
    return {"case_id": case_id, "status": case.status}


# ── Export (real PDF, streaming) ──────────────────────────────────────────────

@app.get("/cases/{case_id}/export", tags=["export"])
async def export_case(
    case_id: str,
    db: DB,
    user: CurrentUser,
):
    """Return PDF bytes directly as a streaming response."""
    case = await _get_case_or_404(case_id, db)
    rows = (await db.execute(select(Evidence).where(Evidence.case_id == case.case_id))).scalars().all()
    audit_rows = (await db.execute(
        select(AuditLog).where(AuditLog.case_id == case.case_id)
    )).scalars().all()

    case_dict = {
        "case_id":          str(case.case_id),
        "status":           case.status,
        "complainant_type": case.complainant_type,
        "reported_loss":    case.reported_loss,
        "created_at":       case.created_at.isoformat() if case.created_at else None,
        "updated_at":       case.updated_at.isoformat() if case.updated_at else None,
        "anchor_tx_hashes": case.anchor_tx_hashes or [],
        "convergence":      case.convergence or {},
    }
    ev_list = [
        {"module_id": r.module_id, "verdict": r.verdict, "confidence": r.confidence,
         "confidence_tier": r.confidence_tier, "hash_sha256": r.hash_sha256,
         "chain_anchor": r.chain_anchor, "ipfs_cid": r.ipfs_cid, "payload": r.payload or {}}
        for r in rows
    ]
    audit_log = [
        {"ts": a.timestamp.isoformat(), "actor": a.actor, "action": a.action}
        for a in audit_rows
    ] + (case.audit_log or [])

    pdf_bytes = generate_pdf(case_dict, ev_list, audit_log)
    await _audit(db, case, user.sub, "EXPORTED_PDF")
    await db.commit()

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="case_{case_id[:8]}.pdf"'},
    )


# ── Freeze request ────────────────────────────────────────────────────────────

@app.get("/cases/{case_id}/freeze-request", tags=["export"])
async def freeze_request(
    case_id: str,
    db: DB,
    user: CurrentUser,
    fmt: str = "json",
):
    """Return freeze-request draft as JSON or PDF."""
    case = await _get_case_or_404(case_id, db)
    rows = (await db.execute(select(Evidence).where(Evidence.case_id == case.case_id))).scalars().all()
    audit_rows = (await db.execute(select(AuditLog).where(AuditLog.case_id == case.case_id))).scalars().all()

    case_dict = {
        "case_id": str(case.case_id), "status": case.status,
        "complainant_type": case.complainant_type, "reported_loss": case.reported_loss,
        "created_at": case.created_at.isoformat() if case.created_at else None,
        "updated_at": case.updated_at.isoformat() if case.updated_at else None,
        "anchor_tx_hashes": case.anchor_tx_hashes or [], "convergence": case.convergence or {},
    }
    ev_list = [
        {"module_id": r.module_id, "verdict": r.verdict, "confidence": r.confidence,
         "confidence_tier": r.confidence_tier, "hash_sha256": r.hash_sha256,
         "chain_anchor": r.chain_anchor, "ipfs_cid": r.ipfs_cid, "payload": r.payload or {}}
        for r in rows
    ]

    await _audit(db, case, user.sub, "FREEZE_REQUEST_GENERATED", {"fmt": fmt})
    await db.commit()

    if fmt == "pdf":
        audit_log = [{"ts": a.timestamp.isoformat(), "actor": a.actor, "action": a.action} for a in audit_rows]
        pdf_bytes = generate_pdf(case_dict, ev_list, audit_log, freeze_mode=True)
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="freeze_request_{case_id[:8]}.pdf"'},
        )

    return generate_freeze_json(case_dict, ev_list)


# ── Audit log endpoint ────────────────────────────────────────────────────────

@app.get("/cases/{case_id}/audit", tags=["cases"])
async def get_audit_log(case_id: str, db: DB, user: CurrentUser):
    """Return full audit trail from AuditLog table."""
    case = await _get_case_or_404(case_id, db)
    rows = (await db.execute(
        select(AuditLog).where(AuditLog.case_id == case.case_id)
    )).scalars().all()
    return [
        {"log_id": str(r.log_id), "actor": r.actor, "action": r.action,
         "detail": r.detail, "timestamp": r.timestamp.isoformat()}
        for r in rows
    ]


# ── Manual state transition (supervisor override) ─────────────────────────────

@app.post("/cases/{case_id}/transition", tags=["cases"])
async def manual_transition(
    case_id: str,
    target_status: str,
    db: DB,
    user: Annotated[TokenPayload, Depends(require_role(Role.SUPERVISOR, Role.OWNER))],
):
    case = await _get_case_or_404(case_id, db)
    try:
        new_status = transition(case.status, target_status)
    except InvalidTransition as e:
        raise HTTPException(status_code=400, detail=str(e))

    case.status = new_status
    case.updated_at = datetime.utcnow()
    _append_audit(case, user.sub, f"MANUAL -> {new_status}")
    await db.commit()
    return {"case_id": case_id, "status": case.status}


# ── Module Plugins ────────────────────────────────────────────────────────────

@app.get("/modules", tags=["plugins"])
async def get_modules(user: CurrentUser):
    """List all registered investigation modules and their live connectivity."""
    modules = list_modules()
    results = []
    for m in modules:
        health = check_module_health(m.module_id)
        results.append({**m.model_dump(), "live_status": health["status"]})
    return results


@app.post("/modules/register", status_code=status.HTTP_201_CREATED, tags=["plugins"])
async def register_new_module(
    manifest: ModuleManifest,
    user: Annotated[TokenPayload, Depends(require_role(Role.SUPERVISOR, Role.OWNER))],
):
    """Register a new investigation plugin module dynamically."""
    registered = register_module(manifest)
    return {"status": "registered", "module": registered.model_dump()}


# ── Webhook Subscriptions ─────────────────────────────────────────────────────

class WebhookCreateRequest(BaseModel):
    url: str
    secret: str | None = None
    events: list[str] = ["*"]


@app.get("/webhooks", tags=["webhooks"])
async def get_webhooks(user: Annotated[TokenPayload, Depends(require_role(Role.SUPERVISOR, Role.OWNER))]):
    """List all registered webhook subscriptions."""
    return list_webhooks()


@app.post("/webhooks/subscribe", status_code=status.HTTP_201_CREATED, tags=["webhooks"])
async def subscribe_webhook(
    req: WebhookCreateRequest,
    user: Annotated[TokenPayload, Depends(require_role(Role.SUPERVISOR, Role.OWNER))],
):
    """Subscribe an external URL to case lifecycle and threat alerts."""
    sub = register_webhook(url=req.url, secret=req.secret, events=req.events)
    return sub


@app.delete("/webhooks/{webhook_id}", tags=["webhooks"])
async def delete_webhook(
    webhook_id: str,
    user: Annotated[TokenPayload, Depends(require_role(Role.SUPERVISOR, Role.OWNER))],
):
    """Unsubscribe a webhook."""
    removed = remove_webhook(webhook_id)
    if not removed:
        raise HTTPException(status_code=404, detail="Webhook subscription not found")
    return {"status": "removed", "id": webhook_id}


# ── Full Case Package Transfer (Export/Import) ────────────────────────────────

@app.get("/cases/{case_id}/package", tags=["export"])
async def download_case_package(case_id: str, db: DB, user: CurrentUser):
    """Export complete case package (metadata + evidence + proofs + artifacts) as a signed ZIP archive."""
    case = await _get_case_or_404(case_id, db)
    rows = (await db.execute(select(Evidence).where(Evidence.case_id == case.case_id))).scalars().all()
    
    case_dict = {
        "case_id": str(case.case_id),
        "status": case.status,
        "complainant_type": case.complainant_type,
        "reported_loss": case.reported_loss,
        "modules_assigned": case.modules_assigned or [],
        "convergence": case.convergence or {},
        "anchor_tx_hashes": case.anchor_tx_hashes or [],
        "created_at": case.created_at.isoformat() if case.created_at else None,
        "updated_at": case.updated_at.isoformat() if case.updated_at else None,
        "created_by": case.created_by,
        "audit_log": case.audit_log or [],
    }
    
    ev_list = [
        {
            "evidence_id": str(r.evidence_id),
            "module_id": r.module_id,
            "verdict": r.verdict,
            "verdict_code": r.verdict_code,
            "confidence": r.confidence,
            "confidence_tier": r.confidence_tier,
            "hash_sha256": r.hash_sha256,
            "chain_anchor": r.chain_anchor,
            "ipfs_cid": r.ipfs_cid,
            "payload": r.payload or {},
            "artifacts": r.artifacts or [],
            "submitted_by": r.submitted_by,
            "submitted_at": r.submitted_at.isoformat() if r.submitted_at else None,
        }
        for r in rows
    ]
    
    zip_bytes = export_case_package(case_dict, ev_list)
    await _audit(db, case, user.sub, "EXPORTED_PACKAGE")
    await db.commit()
    
    return StreamingResponse(
        io.BytesIO(zip_bytes),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="eob_case_{case_id[:8]}.zip"'},
    )


@app.post("/cases/import", status_code=status.HTTP_201_CREATED, tags=["cases"])
async def import_case(
    db: DB,
    user: Annotated[TokenPayload, Depends(require_role(Role.INVESTIGATOR, Role.SUPERVISOR, Role.OWNER))],
    file: UploadFile = File(...),
):
    """Import a verified case package ZIP archive and restore into the database."""
    zip_content = await file.read()
    try:
        case_dict, evidence_list, artifacts = import_case_package(zip_content)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid package archive: {exc}")
        
    case_uid = uuid.UUID(case_dict.get("case_id", str(uuid.uuid4())))
    
    # Check if case already exists
    existing = (await db.execute(select(Case).where(Case.case_id == case_uid))).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail=f"Case {case_uid} already exists in database")
        
    case = Case(
        case_id=case_uid,
        status=case_dict.get("status", "CREATED"),
        created_by=case_dict.get("created_by", user.sub),
        complainant_type=case_dict.get("complainant_type", ""),
        reported_loss=case_dict.get("reported_loss"),
        modules_assigned=case_dict.get("modules_assigned", []),
        convergence=case_dict.get("convergence"),
        anchor_tx_hashes=case_dict.get("anchor_tx_hashes", []),
        audit_log=case_dict.get("audit_log", []) + [{"ts": datetime.utcnow().isoformat(), "actor": user.sub, "action": "IMPORTED_PACKAGE"}],
    )
    db.add(case)
    
    for ev in evidence_list:
        db_ev = Evidence(
            evidence_id=uuid.UUID(ev["evidence_id"]) if "evidence_id" in ev else uuid.uuid4(),
            case_id=case_uid,
            module_id=ev["module_id"],
            submitted_by=ev.get("submitted_by", user.sub),
            created_by=ev.get("created_by", user.sub),
            verdict=ev.get("verdict", ""),
            verdict_code=ev.get("verdict_code", "MATCH"),
            confidence=float(ev.get("confidence", 1.0)),
            confidence_tier=ev.get("confidence_tier", "high"),
            artifacts=ev.get("artifacts", []),
            hash_sha256=ev.get("hash_sha256", ""),
            chain_anchor=ev.get("chain_anchor"),
            ipfs_cid=ev.get("ipfs_cid"),
            payload=ev.get("payload", {}),
        )
        db.add(db_ev)
        
    await db.commit()
    await db.refresh(case)
    logger.info(f"Successfully imported case {case_uid} with {len(evidence_list)} evidence items")
    return _case_response(case, len(evidence_list))


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _get_case_or_404(case_id: str, db: AsyncSession) -> Case:
    try:
        uid = uuid.UUID(case_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid case_id format")
    row = (await db.execute(select(Case).where(Case.case_id == uid))).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")
    return row


def _case_response(case: Case, evidence_count: int) -> dict:
    return {
        "case_id":          str(case.case_id),
        "status":           case.status,
        "created_at":       case.created_at.isoformat() if case.created_at else None,
        "updated_at":       case.updated_at.isoformat() if case.updated_at else None,
        "created_by":       case.created_by,
        "complainant_type": case.complainant_type,
        "reported_loss":    case.reported_loss,
        "modules_assigned": case.modules_assigned or [],
        "convergence":      case.convergence,
        "anchor_tx_hashes": case.anchor_tx_hashes or [],
        "evidence_count":   evidence_count,
    }


def _append_audit(case: Case, actor: str, action: str):
    log = list(case.audit_log or [])
    log.append({"ts": datetime.utcnow().isoformat(), "actor": actor, "action": action})
    case.audit_log = log


async def _audit(db: AsyncSession, case: Case, actor: str, action: str, detail: dict = None):
    """Write to both the JSON column and the AuditLog table."""
    _append_audit(case, actor, action)
    db.add(AuditLog(
        case_id=case.case_id,
        actor=actor,
        action=action,
        detail=detail or {},
        timestamp=datetime.utcnow(),
    ))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
