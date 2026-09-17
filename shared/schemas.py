"""Shared Pydantic schemas for Eye of Abyss — copied from design-doc.md."""

from datetime import datetime
from typing import Literal, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class Artifact(BaseModel):
    filename: str
    file_type: str  # e.g. "image/png", "application/json"
    description: str
    storage_url: Optional[str] = None


class CrossModuleSignals(BaseModel):
    timezone_match: Optional[float] = None
    activity_overlap: Optional[float] = None
    actor_graph_link: Optional[str] = None  # Neo4j node ID
    convergence_confidence: Optional[float] = None


class EvidenceObject(BaseModel):
    # Identity
    evidence_id: UUID = Field(default_factory=uuid4)
    case_id: Optional[UUID] = None
    module_id: str = Field(..., description="Module identifier (voiceguard, shadowtrace, chaineye, or custom plugin)")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str = "SYSTEM"  # Officer ID or service

    # Verdict
    verdict: str
    verdict_code: str
    confidence: float  # 0.0–1.0
    confidence_tier: Literal["high", "medium", "low"]

    # Module-specific payload
    payload: dict = Field(default_factory=dict)

    # Artifacts
    artifacts: list[Artifact] = Field(default_factory=list)

    # Chain of custody
    submitted_by: str = "SYSTEM"
    submitted_at: datetime = Field(default_factory=datetime.utcnow)
    hash_sha256: str = ""
    chain_anchor: Optional[str] = None  # Polygon tx hash
    ipfs_cid: Optional[str] = None

    # Cross-module signals (populated by Case Engine)
    cross_signals: Optional[CrossModuleSignals] = None


class CriminalActorProfile(BaseModel):
    """Shared schema for the synthetic data pipeline — same actor across modules."""
    actor_id: UUID = Field(default_factory=uuid4)
    archetype: str  # e.g. "investment_fraudster", "darknet_vendor"
    handles: list[str] = Field(default_factory=list)
    platforms: list[str] = Field(default_factory=list)
    timezone: str = "UTC"
    active_hours: list[int] = Field(default_factory=list)  # 0–23
    wallet_addresses: list[str] = Field(default_factory=list)
    linguistic_features: dict = Field(default_factory=dict)
    transaction_features: dict = Field(default_factory=dict)
    data_source: Literal["synthetic", "gwern", "academic"] = "synthetic"


class CaseFile(BaseModel):
    case_id: UUID = Field(default_factory=uuid4)
    status: Literal[
        "CREATED", "ACTIVE", "EVIDENCE_SUBMITTED",
        "CONVERGENCE_COMPUTED", "READY_TO_ANCHOR",
        "ANCHORED", "FILED", "CLOSED"
    ] = "CREATED"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str
    complainant_type: str = ""
    reported_loss: Optional[str] = None
    modules_assigned: list[str] = Field(default_factory=list)
    evidence: list[EvidenceObject] = Field(default_factory=list)
    convergence: Optional[CrossModuleSignals] = None
    anchor_tx_hashes: list[str] = Field(default_factory=list)


class ModuleEvidence(BaseModel):
    """Inter-service contract: what each module posts to Case Engine."""
    module_id: str = Field(..., description="Module identifier (voiceguard, shadowtrace, chaineye, or custom plugin)")
    case_id: UUID
    evidence_id: UUID = Field(default_factory=uuid4)
    confidence: float        # 0.0 – 1.0
    verdict: str             # Human-readable
    artifacts: list[Artifact] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    chain_anchor: Optional[str] = None  # Polygon tx hash, once anchored


# ── Request / Response helpers used by Case Engine endpoints ──────────────────

class CreateCaseRequest(BaseModel):
    complainant_type: str
    reported_loss: Optional[str] = None
    modules_assigned: list[str] = Field(default_factory=list)
    notes: str = ""


class CaseResponse(BaseModel):
    case_id: UUID
    status: str
    created_at: datetime
    updated_at: datetime
    complainant_type: str
    reported_loss: Optional[str]
    modules_assigned: list[str]
    convergence: Optional[CrossModuleSignals]
    anchor_tx_hashes: list[str]
    evidence_count: int


# ── Auth request / response schemas ───────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: str
    password: str
    role: str = "VIEWER"   # default; OWNER can promote later


class LoginRequest(BaseModel):
    email: str
    password: str


class WalletLoginRequest(BaseModel):
    wallet_address: str   # 0x...
    message: str          # challenge string shown to user
    signature: str        # eth_sign result


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    user_id: UUID
    email: str
    role: str
    wallet_address: Optional[str]
    is_active: bool
    created_at: datetime


class UpdateUserRequest(BaseModel):
    role: Optional[str] = None
    is_active: Optional[bool] = None

