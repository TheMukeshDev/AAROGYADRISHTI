"""AI coach conversation ORM models (Phase 6).

Conversations and messages are stored per user. The coach only ever sees
aggregated, derived context (patterns, evidence, learnings, summaries); raw
daily-log rows or health-sync vitals are never included in prompts.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin


class CoachConversation(Base, TimestampMixin):
    __tablename__ = "coach_conversations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False, server_default="Coach chat")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (Index("ix_coach_conversations_user_created", "user_id", "created_at"),)


class CoachMessage(Base, TimestampMixin):
    __tablename__ = "coach_messages"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    conversation_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("coach_conversations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # user | coach
    role: Mapped[str] = mapped_column(String(10), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    provider: Mapped[str] = mapped_column(String(20), nullable=False, server_default="deterministic")
    safety_applied: Mapped[bool] = mapped_column(default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        Index("ix_coach_messages_conversation_created", "conversation_id", "created_at"),
    )