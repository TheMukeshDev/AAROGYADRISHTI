"""Coach provider abstraction (Phase 6, section 4).

A provider turns a list of chat messages (plus a structured, aggregate-only
``CoachContext``) into a coaching reply. The deterministic provider works with
zero configuration; remote LLM providers can be plugged in behind the same
interface. Providers NEVER receive raw daily-log rows or health vitals - only
the derived aggregates assembled by ``prompt_builder``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class CoachContext:
    """Derived, aggregate-only information the coach is allowed to see."""

    user_name: str | None = None
    patterns: list[dict] = field(default_factory=list)          # pattern snapshot dicts
    active_experiment: dict | None = None
    recent_experiments: list[dict] = field(default_factory=list)
    learnings: list[dict] = field(default_factory=list)         # top personal learnings
    next_action: dict | None = None
    has_daily_data: bool = False
    days_tracked: int = 0

    def to_dict(self) -> dict:
        return {
            "user_name": self.user_name,
            "patterns": self.patterns,
            "active_experiment": self.active_experiment,
            "recent_experiments": self.recent_experiments,
            "learnings": self.learnings,
            "next_action": self.next_action,
            "has_daily_data": self.has_daily_data,
            "days_tracked": self.days_tracked,
        }


class CoachProvider(ABC):
    """Interface every coach backend implements."""

    name: str = "base"

    @abstractmethod
    def generate(self, messages: list[dict], context: CoachContext) -> str:
        """Return the coach reply text for the given message history."""


def provider_name(provider: CoachProvider) -> str:
    return getattr(provider, "name", type(provider).__name__.lower())