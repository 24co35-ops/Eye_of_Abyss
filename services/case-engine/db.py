"""SQLAlchemy async models and engine for Case Engine.

All tables live in the same PostgreSQL DB.
Alembic manages schema migrations (see alembic/ directory).
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import JSON, Boolean, Column, DateTime, Float, ForeignKey, String, Text, Uuid, event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

try:
    from shared.runtime_config import is_production, validate_secret
except ImportError:
    from runtime_config import is_production, validate_secret


def _get_database_url() -> str:
    url = os.getenv("DATABASE_URL", "").strip()
    pg_pwd = os.getenv("POSTGRES_PASSWORD", "").strip()
    if is_production():
        if pg_pwd:
            validate_secret("POSTGRES_PASSWORD", pg_pwd, min_length=12, required=True)
        if not url:
            if not pg_pwd:
                raise RuntimeError("Either DATABASE_URL or POSTGRES_PASSWORD must be configured in production")
            pg_user = os.getenv("POSTGRES_USER", "eyeofabyss")
            pg_db = os.getenv("POSTGRES_DB", "eyeofabyss")
            pg_host = os.getenv("POSTGRES_HOST", "postgres")
            url = f"postgresql://{pg_user}:{pg_pwd}@{pg_host}:5432/{pg_db}"
        validate_secret("DATABASE_URL", url, min_length=16, required=True)
        return url
    if not url:
        if pg_pwd:
            return f"postgresql://eyeofabyss:{pg_pwd}@localhost:5432/eyeofabyss"
        # Test / offline fallback
        return "sqlite+aiosqlite:///test_eob.db"
    return url


DATABASE_URL = _get_database_url()
if DATABASE_URL.startswith("postgresql://"):
    _async_url = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
elif DATABASE_URL.startswith("sqlite://") and not DATABASE_URL.startswith("sqlite+aiosqlite://"):
    _async_url = DATABASE_URL.replace("sqlite://", "sqlite+aiosqlite://", 1)
else:
    _async_url = DATABASE_URL

connect_args = {"timeout": 60} if "sqlite" in _async_url else {}
engine = create_async_engine(_async_url, echo=False, pool_pre_ping=True, connect_args=connect_args)


if "sqlite" in _async_url:
    @event.listens_for(engine.sync_engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record):
        try:
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA busy_timeout=60000")
            cursor.close()
        except Exception:
            pass

SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


# ── Users ─────────────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    user_id         = Column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    email           = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=True)   # NULL for wallet-only users
    role            = Column(String(20),  nullable=False, default="VIEWER")
    wallet_address  = Column(String(42),  unique=True, nullable=True)
    is_active       = Column(Boolean, default=True, nullable=False)
    created_at      = Column(DateTime, default=_utc_now, nullable=False)
    updated_at      = Column(DateTime, default=_utc_now, onupdate=_utc_now)


# ── Cases ─────────────────────────────────────────────────────────────────────

class Case(Base):
    __tablename__ = "cases"

    case_id          = Column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    status           = Column(String(40), nullable=False, default="CREATED")
    created_at       = Column(DateTime, default=_utc_now, nullable=False)
    updated_at       = Column(DateTime, default=_utc_now, onupdate=_utc_now, nullable=False)
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

    evidence_id     = Column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    case_id         = Column(Uuid(as_uuid=True), ForeignKey("cases.case_id"), nullable=False, index=True)
    module_id       = Column(String(20), nullable=False)
    created_at      = Column(DateTime, default=_utc_now, nullable=False)
    submitted_at    = Column(DateTime, default=_utc_now, nullable=False)
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

    actor_id             = Column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    archetype            = Column(String(80), nullable=False)
    handles              = Column(JSON, default=list)
    platforms            = Column(JSON, default=list)
    timezone             = Column(String(40), default="UTC")
    active_hours         = Column(JSON, default=list)
    wallet_addresses     = Column(JSON, default=list)
    linguistic_features  = Column(JSON, default=dict)
    transaction_features = Column(JSON, default=dict)
    data_source          = Column(String(20), default="synthetic")
    created_at           = Column(DateTime, default=_utc_now, nullable=False)


# ── Audit Log ─────────────────────────────────────────────────────────────────

class AuditLog(Base):
    __tablename__ = "audit_log"

    log_id     = Column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    case_id    = Column(Uuid(as_uuid=True), ForeignKey("cases.case_id"), nullable=True, index=True)
    actor      = Column(String(255), nullable=False)   # email or user_id
    action     = Column(String(120), nullable=False)
    detail     = Column(JSON, default=dict)
    timestamp  = Column(DateTime, default=_utc_now, nullable=False)


# ── DB helpers ────────────────────────────────────────────────────────────────

async def get_db():
    async with SessionLocal() as session:
        yield session


async def create_tables():
    """Fallback for dev — Alembic handles prod migrations."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
