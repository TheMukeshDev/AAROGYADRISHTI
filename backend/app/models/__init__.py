"""ORM model registry - import everything so Alembic autogenerate can see it."""

from app.database.base import Base
from app.models.consent import ConsentRecord
from app.models.coach import CoachConversation, CoachMessage
from app.models.daily_log import DailyLog
from app.models.evaluation import (
    ExperimentEvidence,
    ExperimentMetricResult,
    LearningCandidate,
)
from app.models.experiment import (
    Experiment,
    ExperimentDailyLog,
    ExperimentResult,
    ExperimentTemplate,
)
from app.models.health import DailyHealthData, HealthConnection
from app.models.personal_learning import PersonalLearning, PersonalLearningEvidence
from app.models.user import User, UserProfile

__all__ = [
    "Base",
    "CoachConversation",
    "CoachMessage",
    "ConsentRecord",
    "DailyHealthData",
    "DailyLog",
    "Experiment",
    "ExperimentDailyLog",
    "ExperimentEvidence",
    "ExperimentMetricResult",
    "ExperimentResult",
    "ExperimentTemplate",
    "HealthConnection",
    "LearningCandidate",
    "PersonalLearning",
    "PersonalLearningEvidence",
    "User",
    "UserProfile",
]