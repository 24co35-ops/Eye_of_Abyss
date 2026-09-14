"""SQLAlchemy async models and engine for Case Engine.

All tables live in the same PostgreSQL DB.
Alembic manages schema migrations (see alembic/ directory).
"""

from __future__ import annotations

import os
from datetime import datetime
from uuid import uuid4

from sqlalchemy import JSON, Boolean, Column, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://eyeofabyss:changeme@localhost:5432/eyeofabyss")
_async_url   = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

engine       = create_async_engine(_async_url, echo=False, pool_pre_ping=True)
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


# ── Users ─────────────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    user_id         = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    email           = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=True)   # NULL for wallet-only users
    role            = Column(String(20),  nullable=False, default="VIEWER")
    wallet_address  = Column(String(42),  unique=True, nullable=True)
    is_active       = Column(Boolean, default=True, nullable=False)
    created_at      = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at      = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ── Cases ─────────────────────────────────────────────────────────────────────

class Case(Base):
    __tablename__ = "cases"

    case_id          = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    status           = Column(String(40), nullable=False, default="CREATED")
    created_at       = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at       = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by       = Column(String(120), nullable=False)
    complainant_type = Column(String(120), default="")
    reported_loss    = Column(String(80), nullable=True)
    modules_assigned = Column(JSON, default=list)
    convergence      = Column(JSON, nullable=True)
    anchor_tx_hashes = Column(JSON, default=list)
    audit_log        = Column(JSON, default=list)


# ── Evidence ──────────────────────────────────────────────────────────────────

class Evidence(Base):
    __tablename__ = "evidence"

    evidence_id     = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    case_id         = Column(UUID(as_uuid=True), ForeignKey("cases.case_id"), nullable=False, index=True)
    module_id       = Column(String(20), nullable=False)
    created_at      = Column(DateTime, default=datetime.utcnow, nullable=False)
    submitted_at    = Column(DateTime, default=datetime.utcnow, nullable=False)
    submitted_by    = Column(String(120), nullable=False)
    created_by      = Column(String(120), nullable=False)
    verdict         = Column(Text, nullable=False)
    verdict_code    = Column(String(60), nullable=False)
    confidence      = Column(Float, nullable=False)
    confidence_tier = Column(String(10), nullable=False)
    payload         = Column(JSON, default=dict)
    artifacts       = Column(JSON, default=list)
    hash_sha256     = Column(String(64), nullable=False, unique=True)
    chain_anchor    = Column(String(90), nullable=True)
    ipfs_cid        = Column(String(80), nullable=True)


# ── Actor Profiles ────────────────────────────────────────────────────────────

class ActorProfile(Base):
    __tablename__ = "actor_profiles"

    actor_id             = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    archetype            = Column(String(80), nullable=False)
    handles              = Column(JSON, default=list)
    platforms            = Column(JSON, default=list)
    timezone             = Column(String(40), default="UTC")
    active_hours         = Column(JSON, default=list)
    wallet_addresses     = Column(JSON, default=list)
    linguistic_features  = Column(JSON, default=dict)
    transaction_features = Column(JSON, default=dict)
    data_source          = Column(String(20), default="synthetic")
    created_at           = Column(DateTime, default=datetime.utcnow, nullable=False)


# ── Audit Log ─────────────────────────────────────────────────────────────────

class AuditLog(Base):
    __tablename__ = "audit_log"

    log_id     = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    case_id    = Column(UUID(as_uuid=True), ForeignKey("cases.case_id"), nullable=True, index=True)
    actor      = Column(String(255), nullable=False)   # email or user_id
    action     = Column(String(120), nullable=False)
    detail     = Column(JSON, default=dict)
    timestamp  = Column(DateTime, default=datetime.utcnow, nullable=False)


# ── DB helpers ────────────────────────────────────────────────────────────────

async def get_db():
    async with SessionLocal() as session:
        yield session


async def create_tables():
    """Fallback for dev — Alembic handles prod migrations."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
