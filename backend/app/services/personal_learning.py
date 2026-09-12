"""Personal learning profile service (Phase 5).

Aggregates the user's learning candidates into a durable "What works for me"
profile. One ``PersonalLearning`` exists per (``pattern_type``, ``intervention``)
key; it snapshots each contributing experiment as a ``PersonalLearningEvidence``
row so the profile can be recalculated idempotently.

Rules kept from the product spec:
- candidates that are rejected or superseded never enter the profile,
- ``INSUFFICIENT`` observations do not form learnings on their own,
- every statement stays an observation (``causality_proven`` is always False),
- the user can dismiss a learning (soft delete) and reopen it,
- recalculation replaces the aggregate but keeps it deterministic.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.personal_learning import PersonalLearning, PersonalLearningEvidence
from app.repositories.personal_learning import (
    PersonalLearningEvidenceRepository,
    PersonalLearningRepository,
)
from app.schemas.experiment import LearningContext

_LEVEL_RANK = {"INSUFFICIENT": 0, "EARLY_OBSERVATION": 1, "PROMISING_OBSERVATION": 2, "REPEATED_OBSERVATION": 3}
_OBSERVATION_LEVELS = {"EARLY_OBSERVATION", "PROMISING_OBSERVATION", "REPEATED_OBSERVATION"}

_STATE_TEXT = {
    "positive": "tended to move in the direction you aimed for",
    "negative": "tended to move against the direction you aimed for",
    "mixed": "changed inconsistently across experiments",
    "neutral": "stayed about the same",
    "insufficient": "there was not enough data to observe a clear direction",
}


class PersonalLearningService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.learnings = PersonalLearningRepository()
        self.evidence_repo = PersonalLearningEvidenceRepository()

    # ------------------------------------------------------------------
    def process_candidates_for(
        self, db: Session, user_id: int, experiment_id: int | None = None
    ) -> list[PersonalLearning]:
        """Fold new candidates (e.g. right after a completed experiment) into the profile."""
        from app.models.evaluation import LearningCandidate

        stmt = select(LearningCandidate).where(LearningCandidate.user_id == user_id)
        if experiment_id is not None:
            stmt = stmt.where(LearningCandidate.experiment_id == experiment_id)
        candidates = list(db.scalars(stmt))
        touched: dict[tuple[str, str], PersonalLearning] = {}
        for candidate in candidates:
            if not self._observable(candidate):
                continue
            key = (candidate.pattern_type, candidate.intervention)
            learning = self.learnings.by_key(db, user_id, *key)
            if learning is None:
                learning = PersonalLearning(
                    user_id=user_id, pattern_type=key[0], intervention=key[1], state="proposed"
                )
                db.add(learning)
                db.flush()
            touched[key] = learning
        for (pattern_type, intervention), learning in touched.items():
            learning = self.recalculate_for_key(db, user_id, pattern_type, intervention)
            db.flush()
        db.commit()
        return list(touched.values())

    def recalculate_for_key(
        self, db: Session, user_id: int, pattern_type: str, intervention: str
    ) -> PersonalLearning | None:
        """Recompute a single (pattern_type, intervention) learning from its candidates."""
        from app.models.evaluation import LearningCandidate

        candidates = list(
            db.scalars(
                select(LearningCandidate).where(
                    LearningCandidate.user_id == user_id,
                    LearningCandidate.pattern_type == pattern_type,
                    LearningCandidate.intervention == intervention,
                )
            )
        )
        observable = [c for c in candidates if self._observable(c)]
        learning = self.learnings.by_key(db, user_id, pattern_type, intervention)
        if learning is None:
            if not observable:
                return None
            learning = PersonalLearning(
                user_id=user_id, pattern_type=pattern_type, intervention=intervention, state="proposed"
            )
            db.add(learning)
            db.flush()
        if observable:
            self._rebuild(db, learning, observable)
        else:
            self._reset(db, learning)
        return learning

    def recalculate_all(self, db: Session, user_id: int) -> list[PersonalLearning]:
        """Rebuild every learning for the user from the current candidate set."""
        from app.models.evaluation import LearningCandidate

        candidates = list(
            db.scalars(
                select(LearningCandidate).where(LearningCandidate.user_id == user_id)
            )
        )
        grouped: dict[tuple[str, str], list] = {}
        for candidate in candidates:
            if not self._observable(candidate):
                continue
            key = (candidate.pattern_type, candidate.intervention)
            grouped.setdefault(key, []).append(candidate)

        existing = self.learnings.list_for_user(db, user_id, include_dismissed=True)
        for learning in existing:
            key = (learning.pattern_type, learning.intervention)
            if key in grouped:
                self._rebuild(db, learning, grouped.pop(key))
            else:
                self._reset(db, learning)

        for (pattern_type, intervention), entries in grouped.items():
            learning = PersonalLearning(
                user_id=user_id, pattern_type=pattern_type, intervention=intervention, state="proposed"
            )
            db.add(learning)
            db.flush()
            self._rebuild(db, learning, entries)

        db.commit()
        return self.learnings.list_for_user(db, user_id)

    # ------------------------------------------------------------------
    def context_for_pattern(self, db: Session, user_id: int, pattern_type: str) -> LearningContext:
        """Phase 5 integration - what the profile already says about a pattern."""
        learning = db.scalars(
            select(PersonalLearning)
            .where(
                PersonalLearning.user_id == user_id,
                PersonalLearning.pattern_type == pattern_type,
                PersonalLearning.state != "dismissed",
                PersonalLearning.evidence_level != "INSUFFICIENT",
            )
            .order_by(PersonalLearning.updated_at.desc())
        ).first()
        if learning is None:
            return LearningContext()
        entries = self.evidence_repo.list_for_learning(db, learning.id)
        note = None
        if entries:
            state = learning.evidence_state
            note = f"You have already tested this: {_STATE_TEXT.get(state, 'changed')}."
        return LearningContext(
            has_learning=True,
            evidence_level=learning.evidence_level,
            evidence_state=learning.evidence_state,
            note=note,
        )

    # ------------------------------------------------------------------
    def _observable(self, candidate) -> bool:
        if candidate.status in ("rejected", "superseded"):
            return False
        return candidate.evidence_level in _OBSERVATION_LEVELS

    def _reset(self, db: Session, learning: PersonalLearning) -> None:
        self.evidence_repo.delete_for_learning(db, learning.id)
        learning.evidence_level = "INSUFFICIENT"
        learning.evidence_state = "insufficient"
        learning.consistency_score = None
        learning.sample_size = 0
        learning.target_metric = None
        learning.summary = None

    def _rebuild(self, db: Session, learning: PersonalLearning, candidates: list) -> None:
        self.evidence_repo.delete_for_learning(db, learning.id)

        entries: list[PersonalLearningEvidence] = []
        for candidate in candidates:
            entries.append(
                PersonalLearningEvidence(
                    learning_id=learning.id,
                    experiment_id=candidate.experiment_id,
                    source="accepted" if candidate.status == "accepted" else "candidate",
                    evidence_level=candidate.evidence_level,
                    direction=self._direction_of(candidate),
                    effect_magnitude=self._primary_change(candidate),
                    observed_change=candidate.observed_change,
                )
            )
        for entry in entries:
            db.add(entry)
        db.flush()

        learning.target_metric = self._primary_metric(entries)
        learning.evidence_level = self._max_level(entries)
        learning.evidence_state = self._evidence_state(entries)
        learning.consistency_score = self._consistency_score(entries)
        learning.sample_size = len(entries)
        learning.summary = self._summary(learning)

    # --- aggregation helpers --------------------------------------------------
    @staticmethod
    def _direction_of(candidate) -> str:
        diff = PersonalLearningService._primary_change(candidate)
        if diff is None:
            return "no_change"
        if diff > 0.05:
            return "improved"
        if diff < -0.05:
            return "worsened"
        return "no_change"

    @staticmethod
    def _primary_change(candidate) -> float | None:
        if not candidate.observed_change:
            return None
        metric = max(candidate.observed_change, key=lambda m: abs(candidate.observed_change[m] or 0.0))
        return candidate.observed_change[metric]

    def _primary_metric(self, entries: list[PersonalLearningEvidence]) -> str | None:
        totals: dict[str, float] = {}
        for entry in entries:
            for metric, diff in (entry.observed_change or {}).items():
                if diff is None:
                    continue
                totals[metric] = totals.get(metric, 0.0) + abs(float(diff))
        if not totals:
            return None
        return max(totals, key=lambda m: totals[m])

    def _max_level(self, entries: list[PersonalLearningEvidence]) -> str:
        if not entries:
            return "INSUFFICIENT"
        best = max(entries, key=lambda e: _LEVEL_RANK.get(e.evidence_level, 0))
        return best.evidence_level

    def _evidence_state(self, entries: list[PersonalLearningEvidence]) -> str:
        if not entries:
            return "insufficient"
        directions = [entry.direction for entry in entries]
        positive = directions.count("improved")
        negative = directions.count("worsened")
        if positive and negative:
            return "mixed"
        if positive:
            return "positive"
        if negative:
            return "negative"
        return "neutral"

    def _consistency_score(self, entries: list[PersonalLearningEvidence]) -> float | None:
        if not entries:
            return None
        directions = [entry.direction for entry in entries]
        meaningful = [d for d in directions if d != "no_change"] or ["no_change"]
        modal = max(set(meaningful), key=meaningful.count)
        alignment = meaningful.count(modal) / len(meaningful)
        magnitudes = [abs(entry.effect_magnitude or 0.0) for entry in entries]
        avg_magnitude = min(sum(magnitudes) / len(magnitudes), 1.0) if magnitudes else 0.0
        coverage = min(len(entries), 3) / 3.0
        return round(0.5 * alignment + 0.3 * avg_magnitude + 0.2 * coverage, 3)

    def _summary(self, learning: PersonalLearning) -> str:
        direction_text = _STATE_TEXT.get(learning.evidence_state, "changed in some way")
        count = learning.sample_size or 0
        trials = "experiment" if count == 1 else "experiments"
        target = learning.target_metric or "your wellbeing"
        return (
            f"When you kept \"{learning.intervention}\" across {count} {trials}, "
            f"your {target} {direction_text}. This is an observation from your own data, "
            "not a proof of cause and effect."
        )