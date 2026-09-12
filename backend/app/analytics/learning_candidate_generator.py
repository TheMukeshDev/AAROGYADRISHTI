"""Learning candidate generation (Phase 4, analytics module #6).

Turns a completed experiment's evaluation into a structured learning candidate
for Phase 5. The candidate is an OBSERVATION; ``causality_proven`` is always
False at this stage.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class LearningCandidateData:
    pattern_type: str
    intervention: str
    observed_change: dict[str, float | None] = field(default_factory=dict)
    evidence_level: str = "INSUFFICIENT"
    causality_proven: bool = False
    user_id: int | None = None
    source_experiment_id: int | None = None

    def to_dict(self) -> dict:
        return {
            "pattern_type": self.pattern_type,
            "intervention": self.intervention,
            "observed_change": self.observed_change,
            "evidence_level": self.evidence_level,
            "causality_proven": self.causality_proven,
            "user_id": self.user_id,
            "source_experiment_id": self.source_experiment_id,
        }


def _round(value: float | None, ndigits: int = 2) -> float | None:
    return round(value, ndigits) if value is not None else None


def generate_candidate(
    *,
    pattern_type: str,
    intervention: str,
    observed_change: dict[str, float | None],
    evidence_level: str,
    user_id: int,
    source_experiment_id: int,
) -> LearningCandidateData:
    """Build an observation candidate keyed on the most meaningful metrics.

    Only metrics that actually changed are recorded, so the candidate reads as
    a change observation, never as a general truth.
    """
    meaningful = {
        metric: _round(diff) for metric, diff in observed_change.items()
        if diff is not None and abs(diff) >= 0.05
    }
    return LearningCandidateData(
        pattern_type=pattern_type,
        intervention=intervention,
        observed_change=meaningful,
        evidence_level=evidence_level,
        causality_proven=False,
        user_id=user_id,
        source_experiment_id=source_experiment_id,
    )