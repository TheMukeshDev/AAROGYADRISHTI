"""initial schema

Revision ID: 0001
Revises:
Create Date: 2025-01-01
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("email_verified", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("password_hash", sa.String(length=255), nullable=True),
        sa.Column("name", sa.String(length=120), nullable=True),
        sa.Column("auth_provider", sa.String(length=20), nullable=False, server_default="jwt"),
        sa.Column("token_version", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("is_demo", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_index("ix_users_email", "users", ["email"])

    op.create_table(
        "user_profiles",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("age_group", sa.String(length=30), nullable=True),
        sa.Column("gender", sa.String(length=30), nullable=True),
        sa.Column("height_cm", sa.Float(), nullable=True),
        sa.Column("weight_kg", sa.Float(), nullable=True),
        sa.Column("activity_level", sa.String(length=30), nullable=True),
        sa.Column("primary_goal", sa.String(length=40), nullable=True),
        sa.Column("onboarding_completed", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("timeframe_start", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_user_profiles_user_id", "user_profiles", ["user_id"])

    op.create_table(
        "daily_logs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("sleep_hours", sa.Float(), nullable=True),
        sa.Column("sleep_quality", sa.String(), nullable=True),
        sa.Column("steps", sa.Integer(), nullable=True),
        sa.Column("active_minutes", sa.Integer(), nullable=True),
        sa.Column("exercise_minutes", sa.Integer(), nullable=True),
        sa.Column("exercise_level", sa.String(), nullable=True),
        sa.Column("water_liters", sa.Float(), nullable=True),
        sa.Column("meal_quality", sa.String(), nullable=True),
        sa.Column("screen_time_minutes", sa.Integer(), nullable=True),
        sa.Column("late_night_screen", sa.Boolean(), nullable=True),
        sa.Column("caffeine", sa.String(), nullable=True),
        sa.Column("mood", sa.String(), nullable=True),
        sa.Column("energy", sa.Integer(), nullable=True),
        sa.Column("stress", sa.Integer(), nullable=True),
        sa.Column("source", sa.String(), nullable=False, server_default="manual"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("user_id", "date", name="uq_daily_logs_user_date"),
    )
    op.create_index("ix_daily_logs_user_date", "daily_logs", ["user_id", "date"])
    op.create_index("ix_daily_logs_user_created", "daily_logs", ["user_id", "created_at"])

    op.create_table(
        "health_connections",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("provider", sa.String(), nullable=False),
        sa.Column("steps_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("sleep_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("activity_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("connected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("user_id", "provider", name="uq_health_connections_user_provider"),
    )
    op.create_index("ix_health_connections_user", "health_connections", ["user_id"])

    op.create_table(
        "daily_health_data",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("steps", sa.Integer(), nullable=True),
        sa.Column("active_minutes", sa.Integer(), nullable=True),
        sa.Column("sleep_minutes", sa.Integer(), nullable=True),
        sa.Column("synced_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("user_id", "date", "source", name="uq_daily_health_user_date_source"),
    )
    op.create_index("ix_daily_health_user_date", "daily_health_data", ["user_id", "date"])

    op.create_table(
        "consent_records",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("data_type", sa.String(length=40), nullable=False),
        sa.Column("consent_given", sa.Boolean(), nullable=False),
        sa.Column("revoked", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_consent_records_user_id", "consent_records", ["user_id"])
    op.create_index("ix_consent_user_type", "consent_records", ["user_id", "data_type"])


def downgrade() -> None:
    op.drop_table("consent_records")
    op.drop_table("daily_health_data")
    op.drop_table("health_connections")
    op.drop_table("daily_logs")
    op.drop_table("user_profiles")
    op.drop_table("users")