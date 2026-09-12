"""Coach provider selection (Phase 6).

Returns a deterministic, offline provider unless a remote provider is explicitly
configured AND has the needed credentials. Errors selecting a remote provider
never break the chat API - the fallback is always available.
"""

from __future__ import annotations

from app.ai.base_provider import CoachProvider
from app.ai.deterministic_provider import DeterministicCoachProvider
from app.ai.openai_compatible_provider import OpenAICompatibleProvider
from app.core.config import get_settings


def get_coach_provider(hint: str | None = None) -> CoachProvider:
    """Return the active provider; never raises for configuration issues."""
    settings = get_settings()
    chosen = (hint or settings.ai_provider or "deterministic").lower()
    if chosen in ("openai", "openai_compatible") and settings.ai_api_key:
        return OpenAICompatibleProvider(
            api_key=settings.ai_api_key,
            base_url=settings.ai_base_url,
            model=settings.ai_model,
        )
    return DeterministicCoachProvider()