"""OpenAI-compatible coach provider (Phase 6).

Only used when ``AI_PROVIDER`` is ``openai_compatible`` and a key/base URL are
configured. Talks CHAT completion dialect over HTTP (httpx); the prompt is built
by ``prompt_builder`` from aggregate data only - raw logs are never sent.
"""

from __future__ import annotations

import httpx

from app.ai.base_provider import CoachContext, CoachProvider
from app.ai.safety_guard import sanitize_coach_reply
from app.core.config import get_settings


class OpenAICompatibleProvider(CoachProvider):
    name = "openai_compatible"

    def __init__(self, *, api_key: str | None = None, base_url: str | None = None, model: str | None = None) -> None:
        settings = get_settings()
        self.api_key = api_key or settings.ai_api_key
        self.base_url = (base_url or settings.ai_base_url or "https://api.openai.com/v1").rstrip("/")
        self.model = model or settings.ai_model
        self.timeout = settings.ai_request_timeout_seconds

    def generate(self, messages: list[dict], context: CoachContext) -> str:
        url = f"{self.base_url}/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.4,
            "max_tokens": 500,
        }
        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(url, headers=headers, json=payload)
            response.raise_for_status()
        data = response.json()
        text = data["choices"][0]["message"]["content"]
        reply = sanitize_coach_reply(text, role="coach")
        return reply