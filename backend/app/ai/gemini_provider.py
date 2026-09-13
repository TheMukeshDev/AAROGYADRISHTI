"""Google Gemini REST provider for the aggregate-only lifestyle coach."""

from __future__ import annotations

import httpx

from app.ai.base_provider import CoachContext, CoachProvider
from app.ai.safety_guard import sanitize_coach_reply
from app.core.config import get_settings


class GeminiProvider(CoachProvider):
    name = "gemini"

    def __init__(self, *, api_key: str | None = None, base_url: str | None = None, model: str | None = None) -> None:
        settings = get_settings()
        self.api_key = api_key or settings.ai_api_key
        self.base_url = (base_url or settings.ai_base_url or "https://generativelanguage.googleapis.com/v1beta").rstrip("/")
        self.model = model or settings.ai_model
        self.timeout = settings.ai_request_timeout_seconds

    def generate(self, messages: list[dict], context: CoachContext) -> str:
        system_messages = [
            {"text": str(message.get("content", ""))}
            for message in messages
            if message.get("role") == "system"
        ]
        contents = [
            {
                "role": "model" if message.get("role") == "assistant" else "user",
                "parts": [{"text": str(message.get("content", ""))}],
            }
            for message in messages
            if message.get("role") in {"user", "assistant"}
        ]
        if not contents:
            contents = [{"role": "user", "parts": [{"text": "Give a brief lifestyle check-in."}]}]

        url = f"{self.base_url}/models/{self.model}:generateContent"
        payload = {
            "contents": contents,
            "generationConfig": {"temperature": 0.4, "maxOutputTokens": 500},
        }
        if system_messages:
            payload["systemInstruction"] = {"parts": system_messages}
        headers = {"Content-Type": "application/json", "x-goog-api-key": self.api_key}
        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(url, headers=headers, json=payload)
            response.raise_for_status()
        data = response.json()
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        return sanitize_coach_reply(text, role="coach")