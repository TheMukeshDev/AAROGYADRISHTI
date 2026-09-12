"""phase 4 - experiment evaluation tables

Revision ID: 0003
Revises: 0002
Create Date: 2026-09-12
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "experiment_metric_results",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("experiment_id", sa.Integer(), sa.ForeignKey("experiments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("metric_name", sa.String(length=40), nullable=False),
        sa.Column("baseline_mean", sa.Float(), nullable=True),
        sa.Column("experiment_mean", sa.Float(), nullable=True),
        sa.Column("difference", sa.Float(), nullable=True),
        sa.Column("percentage_change", sa.Float(), nullable=True),
        sa.Column("baseline_median", sa.Float(), nullable=True),
        sa.Column("experiment_median", sa.Float(), nullable=True),
        sa.Column("sample_size", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("valid_observations", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("direction", sa.String(length=20), nullable=False, server_default="no_change"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_experiment_metric_results_exp", "experiment_metric_results", ["experiment_id"])

    op.create_table(
        "experiment_evidence",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("experiment_id", sa.Integer(), sa.ForeignKey("experiments.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("data_completeness", sa.Float(), nullable=False, server_default="0"),
        sa.Column("target_adherence", sa.Float(), nullable=True),
        sa.Column("consistency_score", sa.Float(), nullable=True),
        sa.Column("evidence_level", sa.String(length=40), nullable=False, server_default="INSUFFICIENT"),
        sa.Column("reason", sa.Text(), nullable=False, server_default=""),
        sa.Column("limitations", sa.Text(), nullable=False, server_default=""),
        sa.Column("causality_proven", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_experiment_evidence_experiment_id", "experiment_evidence", ["experiment_id"])

    op.create_table(
        "learning_candidates",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("experiment_id", sa.Integer(), sa.ForeignKey("experiments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("pattern_type", sa.String(length=60), nullable=False),
        sa.Column("intervention", sa.String(length=60), nullable=False),
        sa.Column("observed_change", sa.JSON(), nullable=False),
        sa.Column("evidence_level", sa.String(length=40), nullable=False, server_default="EARLY_OBSERVATION"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="candidate"),
        sa.Column("causality_proven", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_learning_candidates_user_id", "learning_candidates", ["user_id"])
    op.create_index("ix_learning_candidates_experiment_id", "learning_candidates", ["experiment_id"])
    op.create_index("ix_learning_candidates_user_status", "learning_candidates", ["user_id", "status"])


def downgrade() -> None:
    op.drop_table("learning_candidates")
    op.drop_table("experiment_evidence")
    op.drop_table("experiment_metric_results")