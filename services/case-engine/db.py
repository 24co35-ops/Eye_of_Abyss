"""SQLAlchemy async models and engine for Case Engine."""

import os
from datetime import datetime
from uuid import uuid4

from sqlalchemy import JSON, Column, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://eyeofabyss:changeme@localhost:5432/eyeofabyss")
# asyncpg driver — swap prefix if using sync psycopg2
_async_url = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

engine = create_async_engine(_async_url, echo=False, pool_pre_ping=True)
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class Case(Base):
    __tablename__ = "cases"

    case_id       = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    status        = Column(String(40), nullable=False, default="CREATED")
    created_at    = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at    = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by    = Column(String(120), nullable=False)
    complainant_type = Column(String(120), default="")
    reported_loss = Column(String(80), nullable=True)
    modules_assigned = Column(JSON, default=list)        # ["voiceguard", ...]
    convergence   = Column(JSON, nullable=True)          # CrossModuleSignals dict
    anchor_tx_hashes = Column(JSON, default=list)        # Polygon tx hashes
    audit_log     = Column(JSON, default=list)           # [{ts, actor, action}, ...]


class Evidence(Base):
    __tablename__ = "evidence"

    evidence_id   = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    case_id       = Column(UUID(as_uuid=True), ForeignKey("cases.case_id"), nullable=False, index=True)
    module_id     = Column(String(20), nullable=False)   # voiceguard | shadowtrace | chaineye
    created_at    = Column(DateTime, default=datetime.utcnow, nullable=False)
    submitted_at  = Column(DateTime, default=datetime.utcnow, nullable=False)
    submitted_by  = Column(String(120), nullable=False)
    created_by    = Column(String(120), nullable=False)
    verdict       = Column(Text, nullable=False)
    verdict_code  = Column(String(60), nullable=False)
    confidence    = Column(Float, nullable=False)
    confidence_tier = Column(String(10), nullable=False)  # high|medium|low
    payload       = Column(JSON, default=dict)
    artifacts     = Column(JSON, default=list)
    hash_sha256   = Column(String(64), nullable=False, unique=True)
    chain_anchor  = Column(String(90), nullable=True)    # Polygon tx hash
    ipfs_cid      = Column(String(80), nullable=True)


async def get_db():
    async with SessionLocal() as session:
        yield session


async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
