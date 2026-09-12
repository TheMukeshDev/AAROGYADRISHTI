"""Shared response schemas: pagination and empty response."""

from __future__ import annotations

from pydantic import BaseModel


class Message(BaseModel):
    message: str