"""SQLAlchemy 2.0 models (data-engineer). No logic here: see docs/data/DATA_MODEL.md.

Importing this package registers every table on Base.metadata (Alembic and tests rely on it).
"""

from app.models.attempts import (
    ATTEMPT_STATUSES,
    MAYA_DECISIONS,
    OPEN_STATUSES,
    STEP_EVENTS,
    Attempt,
    AttemptAnswer,
    AttemptSkillScore,
    AttemptStep,
)
from app.models.base import Base
from app.models.coach import CoachFeedback, CoachMemory
from app.models.content import (
    ITEM_TYPES,
    AcceptedAnswer,
    Mission,
    MissionVersion,
    Question,
    QuestionOption,
)
from app.models.identity import ROLES, ClassMember, SchoolClass, User
from app.models.reference import CefrLevel, Skill

__all__ = [
    "ATTEMPT_STATUSES",
    "ITEM_TYPES",
    "MAYA_DECISIONS",
    "OPEN_STATUSES",
    "ROLES",
    "STEP_EVENTS",
    "AcceptedAnswer",
    "Attempt",
    "AttemptAnswer",
    "AttemptSkillScore",
    "AttemptStep",
    "Base",
    "CefrLevel",
    "ClassMember",
    "CoachFeedback",
    "CoachMemory",
    "Mission",
    "MissionVersion",
    "Question",
    "QuestionOption",
    "SchoolClass",
    "Skill",
    "User",
]
