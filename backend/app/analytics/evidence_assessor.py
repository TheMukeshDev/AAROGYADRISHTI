"""Evidence classification (Phase 4, analytics module #5).

Describes the strength of a PERSONAL OBSERVATION. Never medical evidence.

Levels:

- INSUFFICIENT: not enough complete data.
- EARLY_OBSERVATION: single/short experiment, limited data.
- PROMISING_OBSERVATION: clear and reasonably consistent change.
- REPEATED_OBSERVATION: similar result across multiple experiments.

All thresholds are configurable via :class:`EvidenceConfig`.
"""

from __future__ import annotations

from dataclasses import dataclass, field

EVIDENCE_LEVELS = ("INSUFFICIENT", "EARLY_OBSERVATION", "PROMISING_OBSERVATION", "REPEATED_OBSERVATION")

LIMITATION_CAUSALITY = (
    "This is a personal observation based on your available data. It does not "
    "establish that the intervention caused the change."
)
LIMITATION_NO_DATA = "Not enough complete data to evaluate this experiment reliably."


@dataclass(frozen=True)
class EvidenceConfig:
    min_observations: int = 3
    min_completeness: float = 0.5
    min_effect_magnitude: float = 0.3   # absolute primary metric change deemed meaningful
    consistency_threshold: float = 0.6
    repeat_min_experiments: int = 2     # completed prior experiments of the same type

    @classmethod
    def from_settings(cls, settings) -> "EvidenceConfig":
        return cls(
            min_observations=getattr(settings, "evidence_min_observations", cls.min_observations),
            min_completeness=getattr(settings, "evidence_min_completeness", cls.min_completeness),
            min_effect_magnitude=getattr(settings, "evidence_min_effect_magnitude", cls.min_effect_magnitude),
            consistency_threshold=getattr(settings, "evidence_consistency_threshold", cls.consistency_threshold),
            repeat_min_experiments=getattr(settings, "evidence_repeat_min_experiments", cls.repeat_min_experiments),
        )


@dataclass
class EvidenceAssessment:
    evidence_level: str
    reason: str
    limitations: str = LIMITATION_CAUSALITY
    causality_proven: bool = False


def assess_evidence(
    *,
    sample_size: int,
    data_completeness: float,
    primary_difference: float | None,
    consistency_score: float | None,
    primary_direction: str,          # improved | worsened | no_change
    previous_similar_experiments: int,
    config: EvidenceConfig = field(default_factory=EvidenceConfig),
) -> EvidenceAssessment:
    """Return the evidence level for THIS single experiment's observation.

    ``previous_similar_experiments`` = count of earlier completed experiments of
    the same type for the same user.
    """
    if sample_size < config.min_observations or data_completeness < config.min_completeness:
        return EvidenceAssessment(
            evidence_level="INSUFFICIENT",
            reason=LIMITATION_NO_DATA,
            limitations=LIMITATION_NO_DATA,
        )

    effect = primary_difference if primary_difference is not None else 0.0
    meaningful = abs(effect) >= config.min_effect_magnitude
    consist = consistency_score if consistency_score is not None else 0.0

    # Repeated: a similar, consistent observation across multiple experiments.
    if (
        previous_similar_experiments >= config.repeat_min_experiments
        and primary_direction in ("improved", "no_change")
        and (primary_direction != "no_change" or not meaningful)
    ):
        return EvidenceAssessment(
            evidence_level="REPEATED_OBSERVATION",
            reason=(
                "A similar result has now been observed across multiple experiments. "
                "The observation repeats, but it still does not prove causation."
            ),
        )

    if primary_direction == "improved" and meaningful and consist >= config.consistency_threshold:
        return EvidenceAssessment(
            evidence_level="PROMISING_OBSERVATION",
            reason="A clear and reasonably consistent personal change was observed.",
        )

    if primary_direction == "worsened" and meaningful and consist >= config.consistency_threshold:
        return EvidenceAssessment(
            evidence_level="PROMISING_OBSERVATION",
            reason="A clear, consistent change was observed - worth paying attention to.",
        )

    return EvidenceAssessment(
        evidence_level="EARLY_OBSERVATION",
        reason="A single or short experiment with limited personal data.",
    )