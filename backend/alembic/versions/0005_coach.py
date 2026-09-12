"""phase 6 - ai coach conversation tables

Revision ID: 0005
Revises: 0004
Create Date: 2026-09-12
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "coach_conversations",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False, server_default="Coach chat"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_coach_conversations_user_id", "coach_conversations", ["user_id"])
    op.create_index("ix_coach_conversations_user_created", "coach_conversations", ["user_id", "created_at"])

    op.create_table(
        "coach_messages",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "conversation_id",
            sa.Integer(),
            sa.ForeignKey("coach_conversations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("role", sa.String(length=10), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "provider", sa.String(length=20), nullable=False, server_default="deterministic"
        ),
        sa.Column("safety_applied", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_coach_messages_conversation_id", "coach_messages", ["conversation_id"])
    op.create_index("ix_coach_messages_conversation_created", "coach_messages", ["conversation_id", "created_at"])


def downgrade() -> None:
    op.drop_table("coach_messages")
    op.drop_table("coach_conversations")