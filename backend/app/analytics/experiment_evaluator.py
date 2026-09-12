"""Experiment evaluation orchestrator (Phase 4, analytics module #1).

Pure deterministic pipeline over pre-loaded numeric series:

    comparisons  ->  consistency  ->  adherence  ->  evidence  ->  summary

The DB/service layer loads and converts the raw daily logs; this module never
touches a database and never invents values.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.analytics.adherence_analyzer import AdherenceResult, analyze_adherence
from app.analytics.consistency_analyzer import ConsistencyResult, analyze_consistency
from app.analytics.evidence_assessor import EvidenceAssessment, EvidenceConfig, assess_evidence
from app.analytics.learning_candidate_generator import LearningCandidateData, generate_candidate
from app.analytics.metric_comparator import MetricComparison, compare_metric


@dataclass
class EvaluationResult:
    experiment_id: int | None = None
    experiment_type: str = ""
    metrics: list[MetricComparison] = field(default_factory=list)
    primary_metric: str | None = None
    primary_difference: float | None = None
    effect_direction: str = "no_change"   # improved | no_change | worsened
    data_completeness: float = 0.0
    sample_size: int = 0
    adherence: AdherenceResult | None = None
    consistency: ConsistencyResult | None = None
    evidence: EvidenceAssessment = field(default_factory=lambda: EvidenceAssessment("INSUFFICIENT", ""))
    summary: str = ""
    target_definition: str | None = None
    learning_candidate: LearningCandidateData | None = None

    def metric_by_name(self, name: str) -> MetricComparison | None:
        for m in self.metrics:
            if m.metric == name:
                return m
        return None


def _fmt(value: float | None, metric: str) -> str:
    if value is None:
        return "n/a"
    if metric in ("steps", "active_minutes", "screen_time_minutes"):
        return f"{value:,.0f}"
    return f"{value:.1f}"


def _primary_direction(difference: float | None, higher_is_better: bool) -> str:
    if difference is None or abs(difference) <= 1e-9:
        return "no_change"
    rising = difference > 0
    if (rising and higher_is_better) or (not rising and not higher_is_better):
        return "improved"
    return "worsened"


def _build_summary(*, primary_metric: str, primary_direction: str, comparisons: list[MetricComparison],
                   target_adherence: str | None, sample_size: int, data_completeness: float) -> str:
    improve_verb = {
        "energy": "was higher", "mood": "was higher", "sleep_hours": "was longer",
        "steps": "was higher", "active_minutes": "was higher", "screen_time_minutes": "was lower",
        "stress": "was lower",
    }
    primary = next((m for m in comparisons if m.metric == primary_metric), None)
    parts: list[str] = []
    if primary is not None and primary.experiment_mean is not None:
        verb = improve_verb.get(primary_metric, "changed")
        if primary_direction == "improved":
            out = verb if verb in ("was longer", "was lower") else f"{verb}"
        elif primary_direction == "worsened":
            out = "was lower" if verb in ("was longer", "was higher") else "moved in the opposite direction"
        else:
            out = "stayed around the same"
        parts.append(
            f"Your {primary_metric.replace('_', ' ')} {out} during the experiment period "
            f"({_fmt(primary.baseline_mean, primary_metric)} -> {_fmt(primary.experiment_mean, primary_metric)})."
        )
    else:
        parts.append("We do not have enough checked-in data for this experiment period.")
    if target_adherence:
        parts.append(target_adherence)
    if sample_size > 0 and data_completeness < 0.6:
        parts.append("Some days were missed, so the comparison is based on partial data.")
    return " ".join(parts)


def evaluate_experiment(
    *,
    baseline_values: dict[str, list[float | None]],
    experiment_values: dict[str, list[float | None]],
    track_metrics: list[str],
    primary_metric: str,
    higher_is_better: bool,
    experiment_days_total: int,
    target_met_flags: list[bool | None],
    previous_similar_experiments: int = 0,
    evidence_config: EvidenceConfig | None = None,
    experiment_id: int | None = None,
    experiment_type: str = "",
    target_definition: str | None = None,
    data_completeness: float | None = None,
) -> EvaluationResult:
    config = evidence_config or EvidenceConfig()

    comparisons = [
        compare_metric(metric, baseline_values.get(metric, []), experiment_values.get(metric, []), higher_is_better)
        for metric in track_metrics
    ]

    primary_diff = next(
        (m.difference for m in comparisons if m.metric == primary_metric), None
    )
    direction = _primary_direction(primary_diff, higher_is_better)

    primary_series = experiment_values.get(primary_metric, [])
    baseline_series = baseline_values.get(primary_metric, [])
    baseline_mean = next(
        (m.baseline_mean for m in comparisons if m.metric == primary_metric), None
    )
    consistency = analyze_consistency(baseline_mean, primary_series)

    adherence = analyze_adherence(experiment_days_total, target_met_flags)

    primary_sample = next(
        (m.sample_size for m in comparisons if m.metric == primary_metric), 0
    )
    if data_completeness is None:
        data_completeness = round(
            primary_sample / experiment_days_total, 4) if experiment_days_total else 0.0
    data_completeness = max(0.0, min(1.0, float(data_completeness)))

    evidence = assess_evidence(
        sample_size=primary_sample,
        data_completeness=data_completeness,
        primary_difference=primary_diff,
        consistency_score=consistency.score,
        primary_direction=direction,
        previous_similar_experiments=previous_similar_experiments,
        config=config,
    )

    summary = _build_summary(
        primary_metric=primary_metric,
        primary_direction=direction,
        comparisons=comparisons,
        target_adherence=(adherence.text if adherence.adherence is not None else None),
        sample_size=primary_sample,
        data_completeness=data_completeness,
    )

    observed_change = {m.metric: m.difference for m in comparisons}
    candidate = generate_candidate(
        pattern_type=experiment_type,
        intervention=experiment_type,
        observed_change=observed_change,
        evidence_level=evidence.evidence_level,
        user_id=0,                 # filled by the service layer
        source_experiment_id=experiment_id or 0,
    )

    return EvaluationResult(
        experiment_id=experiment_id,
        experiment_type=experiment_type,
        metrics=comparisons,
        primary_metric=primary_metric,
        primary_difference=primary_diff,
        effect_direction=direction,
        data_completeness=data_completeness,
        sample_size=primary_sample,
        adherence=adherence,
        consistency=consistency,
        evidence=evidence,
        summary=summary,
        target_definition=target_definition,
        learning_candidate=candidate,
    )