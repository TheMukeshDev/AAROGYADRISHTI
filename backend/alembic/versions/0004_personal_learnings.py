"""phase 5 - personal learning profile tables

Revision ID: 0004
Revises: 0003
Create Date: 2026-09-12
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "personal_learnings",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("pattern_type", sa.String(length=60), nullable=False),
        sa.Column("intervention", sa.String(length=120), nullable=False),
        sa.Column("target_metric", sa.String(length=40), nullable=True),
        sa.Column("state", sa.String(length=20), nullable=False, server_default="proposed"),
        sa.Column("evidence_level", sa.String(length=40), nullable=False, server_default="INSUFFICIENT"),
        sa.Column("evidence_state", sa.String(length=20), nullable=False, server_default="insufficient"),
        sa.Column("consistency_score", sa.Float(), nullable=True),
        sa.Column("sample_size", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("hypothesis", sa.Text(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("causality_proven", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("user_id", "pattern_type", "intervention", name="uq_personal_learning_key"),
    )
    op.create_index("ix_personal_learning_user_id", "personal_learnings", ["user_id"])
    op.create_index("ix_personal_learning_user_state", "personal_learnings", ["user_id", "state"])

    op.create_table(
        "personal_learning_evidence",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "learning_id",
            sa.Integer(),
            sa.ForeignKey("personal_learnings.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("experiment_id", sa.Integer(), nullable=True),
        sa.Column("source", sa.String(length=20), nullable=False, server_default="candidate"),
        sa.Column("evidence_level", sa.String(length=40), nullable=False, server_default="INSUFFICIENT"),
        sa.Column("direction", sa.String(length=12), nullable=False, server_default="no_change"),
        sa.Column("effect_magnitude", sa.Float(), nullable=True),
        sa.Column("data_completeness", sa.Float(), nullable=True),
        sa.Column("target_adherence", sa.Float(), nullable=True),
        sa.Column("observed_change", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["learning_id"], ["personal_learnings.id"]),
    )
    op.create_index("ix_ple_learning_id", "personal_learning_evidence", ["learning_id"])


def downgrade() -> None:
    op.drop_table("personal_learning_evidence")
    op.drop_table("personal_learnings")