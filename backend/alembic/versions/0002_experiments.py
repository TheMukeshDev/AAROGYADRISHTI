"""phase 3 - personal experiment engine tables

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-12
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "experiments",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("pattern_id", sa.String(length=60), nullable=True),
        sa.Column("experiment_type", sa.String(length=60), nullable=False),
        sa.Column("title", sa.String(length=160), nullable=False),
        sa.Column("hypothesis", sa.Text(), nullable=False),
        sa.Column("intervention", sa.Text(), nullable=False),
        sa.Column("duration_days", sa.Integer(), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="active"),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_experiments_user_id", "experiments", ["user_id"])
    op.create_index("ix_experiments_experiment_type", "experiments", ["experiment_type"])
    op.create_index("ix_experiments_user_status", "experiments", ["user_id", "status"])

    op.create_table(
        "experiment_templates",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("experiment_type", sa.String(length=60), nullable=False, unique=True),
        sa.Column("title", sa.String(length=160), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("hypothesis_template", sa.Text(), nullable=False),
        sa.Column("intervention", sa.Text(), nullable=False),
        sa.Column("duration_days", sa.Integer(), nullable=False, server_default="7"),
        sa.Column("required_metrics", sa.JSON(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "experiment_daily_logs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("experiment_id", sa.Integer(), sa.ForeignKey("experiments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("completed", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("target_met", sa.Boolean(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("day_number", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("experiment_id", "date", name="uq_experiment_daily_logs_exp_date"),
    )
    op.create_index("ix_experiment_daily_logs_experiment_id", "experiment_daily_logs", ["experiment_id"])

    op.create_table(
        "experiment_results",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("experiment_id", sa.Integer(), sa.ForeignKey("experiments.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("baseline_values", sa.JSON(), nullable=False),
        sa.Column("experiment_values", sa.JSON(), nullable=False),
        sa.Column("differences", sa.JSON(), nullable=False),
        sa.Column("effect_direction", sa.String(length=20), nullable=True),
        sa.Column("sample_size", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("confidence_level", sa.String(length=30), nullable=False, server_default="insufficient_data"),
        sa.Column("summary", sa.Text(), nullable=False, server_default=""),
        sa.Column("limitations", sa.Text(), nullable=False, server_default=""),
        sa.Column("learning", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_experiment_results_experiment_id", "experiment_results", ["experiment_id"])


def downgrade() -> None:
    op.drop_table("experiment_results")
    op.drop_table("experiment_daily_logs")
    op.drop_table("experiment_templates")
    op.drop_table("experiments")