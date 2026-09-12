"""Insight generator (Phase 2, section 15).

Turns a structured :class:`PatternResult` into a human-readable, cautiously
worded insight shown on the dashboard and the My Patterns screen.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.analytics.explain import (
    DISCLAIMER,
    build_description,
    build_evidence,
    build_limitations,
)
from app.analytics.patterns import PatternResult

# Allowed phrasing (section 15):
ALLOWED = {"associated with", "tends to", "observed pattern", "may be related", "appears connected"}
# Words that must never appear in generated copy:
FORBIDDEN = ["causes", "will cause", "prevents disease", "at risk", "you have", "diagnosis"]


@dataclass
class InsightResult:
    pattern_type: str
    title: str
    description: str
    evidence: str
    strength: str
    strength_label: str
    sample_size: int
    direction: str | None
    correlation: float | None
    limitations: str
    disclaimer: str
    pattern_id: str | None = None
    pattern: PatternResult | None = field(default=None, repr=False)

    def to_dict(self) -> dict:
        return {
            "pattern_type": self.pattern_type,
            "title": self.title,
            "description": self.description,
            "evidence": self.evidence,
            "strength": self.strength,
            "strength_label": self.strength_label,
            "sample_size": self.sample_size,
            "direction": self.direction,
            "correlation": None if self.correlation is None else round(self.correlation, 4),
            "limitations": self.limitations,
            "disclaimer": self.disclaimer,
        }


class InsightGenerator:
    """Build human-readable insights from pattern results."""

    def generate(self, pattern: PatternResult) -> InsightResult:
        description = build_description(pattern)
        evidence = build_evidence(pattern)
        limitations = build_limitations(pattern)

        # Safety net: drop any generated copy that slipped past the cautious
        # language boundary.
        safe_desc = _ensure_cautious(description)
        safe_ev = _ensure_cautious(evidence)

        return InsightResult(
            pattern_type=pattern.pattern_type,
            title=pattern.title,
            description=safe_desc,
            evidence=safe_ev,
            strength=pattern.strength,
            strength_label=pattern.strength_label,
            sample_size=pattern.n,
            direction=pattern.direction,
            correlation=pattern.correlation,
            limitations=limitations,
            disclaimer=DISCLAIMER,
            pattern=pattern,
        )


def _ensure_cautious(text: str) -> str:
    lowered = text.lower()
    for word in FORBIDDEN:
        if word in lowered:
            return "A personal pattern is being monitored in your recent data."
    return text