"""Coach schemas (Phase 6)."""

from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, ConfigDict, Field


class CoachConversationCreateRequest(BaseModel):
    title: str = Field(default="Coach chat", max_length=200)


class CoachConversationResponse(BaseModel):
    id: int
    user_id: int
    title: str
    created_at: dt.datetime

    model_config = ConfigDict(from_attributes=True)


class CoachMessageResponse(BaseModel):
    id: int
    conversation_id: int
    role: str
    content: str
    provider: str = "deterministic"
    safety_applied: bool = False
    created_at: dt.datetime

    model_config = ConfigDict(from_attributes=True)


class CoachReplyRequest(BaseModel):
    content: str = Field(min_length=1, max_length=4000)


class CoachReplyResponse(BaseModel):
    conversation_id: int
    reply: CoachMessageResponse
    provider: str


class CoachConversationListResponse(BaseModel):
    conversations: list[CoachConversationResponse]
    count: int


class CoachMessageListResponse(BaseModel):
    messages: list[CoachMessageResponse]
    count: int


class NextActionResponse(BaseModel):
    action_type: str
    heading: str
    reason: str


class WeeklySummaryResponse(BaseModel):
    window_days: int
    days_tracked: int
    completion_rate: float
    averages: dict
    experiments_completed_total: int
    generated_on: str
    narrative: str = ""