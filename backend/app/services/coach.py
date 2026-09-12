"""Coach orchestration service (Phase 6).

Owns conversations/messages persistence and the reply pipeline:
context -> provider -> safety guard -> persist. Ownership is enforced for every
conversation access.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.deterministic_provider import generate_deterministic_reply
from app.ai.prompt_builder import build_context, build_messages
from app.ai.provider_factory import get_coach_provider
from app.ai.safety_guard import is_prohibited_user_question, sanitize_coach_reply
from app.core.errors import NotFoundError
from app.models.coach import CoachConversation, CoachMessage
from app.services.next_action import determine_next_action


def _owned_conversation(db: Session, user_id: int, conversation_id: int) -> CoachConversation:
    row = db.scalars(
        select(CoachConversation).where(
            CoachConversation.id == conversation_id, CoachConversation.user_id == user_id
        )
    ).first()
    if row is None:
        raise NotFoundError("Conversation not found.")
    return row


class CoachService:
    def start_conversation(self, db: Session, user, title: str = "Coach chat") -> CoachConversation:
        row = CoachConversation(user_id=user.id, title=title or "Coach chat")
        db.add(row)
        db.commit()
        db.refresh(row)
        return row

    def list_conversations(self, db: Session, user_id: int) -> list[CoachConversation]:
        return list(
            db.scalars(
                select(CoachConversation)
                .where(CoachConversation.user_id == user_id)
                .order_by(CoachConversation.created_at.desc())
            )
        )

    def list_messages(self, db: Session, user_id: int, conversation_id: int) -> list[CoachMessage]:
        _owned_conversation(db, user_id, conversation_id)
        return list(
            db.scalars(
                select(CoachMessage)
                .where(CoachMessage.conversation_id == conversation_id)
                .order_by(CoachMessage.created_at, CoachMessage.id)
            )
        )

    def reply(self, db: Session, user, conversation_id: int, content: str) -> CoachMessage:
        conversation = _owned_conversation(db, user.id, conversation_id)

        db.add(CoachMessage(conversation_id=conversation.id, role="user", content=content, provider="user"))
        db.flush()

        next_action = determine_next_action(db, user)
        context = build_context(db, user, next_action=next_action)
        provider = get_coach_provider()

        reply_text = None
        if provider.name == "deterministic":
            reply_text = generate_deterministic_reply(context, content)
        else:
            messages = build_messages(content, context)
            reply_text = provider.generate(messages, context)

        reply_text = sanitize_coach_reply(reply_text, role="coach")

        if is_prohibited_user_question(content):
            reply_text = (
                "I want to flag this honestly: medical questions (medication, diagnosis, "
                "treatment) are outside what I can help with. I only work with lifestyle "
                "observations - for anything medical, please talk to a clinician.\n\n"
                f"{reply_text}"
            )

        coach_msg = CoachMessage(
            conversation_id=conversation.id,
            role="coach",
            content=reply_text,
            provider=provider.name,
            safety_applied=True,
        )
        db.add(coach_msg)
        db.commit()
        db.refresh(coach_msg)
        return coach_msg


# keep a single importable instance (mirrors the api module pattern)
coach_service = CoachService()