"""Initial migration — users, cases, evidence, actor_profiles, audit_log.

Revision ID: 0001_initial
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(255), nullable=True),
        sa.Column("role", sa.String(20), nullable=False, server_default="VIEWER"),
        sa.Column("wallet_address", sa.String(42), unique=True, nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=True, server_default=sa.func.now()),
    )
    op.create_index("ix_users_email", "users", ["email"])

    op.create_table(
        "cases",
        sa.Column("case_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("status", sa.String(40), nullable=False, server_default="CREATED"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("created_by", sa.String(120), nullable=False),
        sa.Column("complainant_type", sa.String(120), nullable=True, server_default=""),
        sa.Column("reported_loss", sa.String(80), nullable=True),
        sa.Column("modules_assigned", postgresql.JSON(), nullable=True),
        sa.Column("convergence", postgresql.JSON(), nullable=True),
        sa.Column("anchor_tx_hashes", postgresql.JSON(), nullable=True),
        sa.Column("audit_log", postgresql.JSON(), nullable=True),
    )

    op.create_table(
        "evidence",
        sa.Column("evidence_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("case_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("cases.case_id"), nullable=False),
        sa.Column("module_id", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("submitted_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("submitted_by", sa.String(120), nullable=False),
        sa.Column("created_by", sa.String(120), nullable=False),
        sa.Column("verdict", sa.Text(), nullable=False),
        sa.Column("verdict_code", sa.String(60), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("confidence_tier", sa.String(10), nullable=False),
        sa.Column("payload", postgresql.JSON(), nullable=True),
        sa.Column("artifacts", postgresql.JSON(), nullable=True),
        sa.Column("hash_sha256", sa.String(64), nullable=False, unique=True),
        sa.Column("chain_anchor", sa.String(90), nullable=True),
        sa.Column("ipfs_cid", sa.String(80), nullable=True),
    )
    op.create_index("ix_evidence_case_id", "evidence", ["case_id"])

    op.create_table(
        "actor_profiles",
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("archetype", sa.String(80), nullable=False),
        sa.Column("handles", postgresql.JSON(), nullable=True),
        sa.Column("platforms", postgresql.JSON(), nullable=True),
        sa.Column("timezone", sa.String(40), nullable=True, server_default="UTC"),
        sa.Column("active_hours", postgresql.JSON(), nullable=True),
        sa.Column("wallet_addresses", postgresql.JSON(), nullable=True),
        sa.Column("linguistic_features", postgresql.JSON(), nullable=True),
        sa.Column("transaction_features", postgresql.JSON(), nullable=True),
        sa.Column("data_source", sa.String(20), nullable=True, server_default="synthetic"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "audit_log",
        sa.Column("log_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("case_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("cases.case_id"), nullable=True),
        sa.Column("actor", sa.String(255), nullable=False),
        sa.Column("action", sa.String(120), nullable=False),
        sa.Column("detail", postgresql.JSON(), nullable=True),
        sa.Column("timestamp", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_audit_log_case_id", "audit_log", ["case_id"])


def downgrade() -> None:
    op.drop_table("audit_log")
    op.drop_table("actor_profiles")
    op.drop_table("evidence")
    op.drop_table("cases")
    op.drop_table("users")
