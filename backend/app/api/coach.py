"""AI preventive lifestyle coach endpoints (Phase 6).

The coach only works from aggregate data. All conversation/message access is
user-scoped via the service's ownership checks.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession
from app.schemas.coach import (
    CoachConversationCreateRequest,
    CoachConversationListResponse,
    CoachConversationResponse,
    CoachMessageListResponse,
    CoachMessageResponse,
    CoachReplyRequest,
    CoachReplyResponse,
    NextActionResponse,
    WeeklySummaryResponse,
)
from app.services.coach import coach_service
from app.services.next_action import determine_next_action
from app.services.weekly_summary import build_weekly_summary, build_weekly_summary_text

router = APIRouter(tags=["coach"])


@router.post("/coach/conversations", response_model=CoachConversationResponse, status_code=201)
def create_conversation(payload: CoachConversationCreateRequest, db: DbSession, user: CurrentUser):
    return coach_service.start_conversation(db, user, payload.title)


@router.get("/coach/conversations", response_model=CoachConversationListResponse)
def list_conversations(db: DbSession, user: CurrentUser):
    rows = coach_service.list_conversations(db, user.id)
    return CoachConversationListResponse(
        conversations=[CoachConversationResponse.model_validate(row) for row in rows],
        count=len(rows),
    )


@router.get("/coach/conversations/{conversation_id}/messages", response_model=CoachMessageListResponse)
def list_messages(conversation_id: int, db: DbSession, user: CurrentUser):
    rows = coach_service.list_messages(db, user.id, conversation_id)
    return CoachMessageListResponse(
        messages=[CoachMessageResponse.model_validate(row) for row in rows],
        count=len(rows),
    )


@router.post("/coach/conversations/{conversation_id}/messages", response_model=CoachReplyResponse)
def send_message(conversation_id: int, payload: CoachReplyRequest, db: DbSession, user: CurrentUser):
    reply = coach_service.reply(db, user, conversation_id, payload.content)
    return CoachReplyResponse(
        conversation_id=conversation_id,
        reply=CoachMessageResponse.model_validate(reply),
        provider=reply.provider,
    )


@router.get("/coach/next-action", response_model=NextActionResponse)
def next_action(db: DbSession, user: CurrentUser):
    return determine_next_action(db, user)


@router.get("/coach/weekly-summary", response_model=WeeklySummaryResponse)
def weekly_summary(db: DbSession, user: CurrentUser):
    summary = build_weekly_summary(db, user.id)
    summary["narrative"] = build_weekly_summary_text(summary)
    return summary