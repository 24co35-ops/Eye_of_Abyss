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
    case_id: UUID
    module_id: Literal["voiceguard", "shadowtrace", "chaineye"]
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str  # Officer ID

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
    submitted_by: str
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
