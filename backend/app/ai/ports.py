"""The coach port: what any LLM adapter receives (CoachContext) and must return (CoachFeedback).

The planner (app.engine) decides WHAT Maya does during a mission. This layer only decides HOW she
speaks after it has been graded, and what she remembers. Nothing here can change a score, a level
or an unlock: the context is built from values that are already committed, and the output must
echo the deterministic strength / challenge and pick a next mission from the given candidates.

Adding a provider = one file implementing CoachProvider + one entry in factory.PROVIDERS.
"""

import re
from dataclasses import dataclass
from typing import Annotated, Any, Literal, Protocol, Self, runtime_checkable

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    PrivateAttr,
    StringConstraints,
    ValidationInfo,
    field_validator,
    model_validator,
)

SCORED_SKILLS: tuple[str, ...] = ("grammar", "listening", "reading", "vocabulary")
Skill = Literal["grammar", "listening", "reading", "vocabulary"]
AnySkill = Literal["grammar", "listening", "reading", "vocabulary", "speaking"]
Cefr = Literal["PRE_A1", "A1", "A2", "B1", "B2", "C1"]
Stage = Literal["first_meeting", "getting_to_know", "familiar"]

MAX_NOTES = 5
# Field limits of CoachFeedback (characters). The prompt asks for 1-3 short sentences per field.
LIMITS: dict[str, int] = {
    "summary": 600,
    "recommendation": 300,
    "memory_note": 200,
    "next_greeting": 240,
}

# MAYA.md §8.2 / §8.3: never shame, never game-reward language. Checked on every LLM output.
_BANNED = re.compile(
    r"\b(wrong|fail\w*|mistakes?|careless|easy (questions?|ones?)|stupid|xp|points?|"
    r"level[- ]up|streaks?|combos?|badges?|achievements?|rewards?|high score)\b",
    re.IGNORECASE,
)
_URL = re.compile(r"https?://|www\.", re.IGNORECASE)
_NAME_CHARS = re.compile(r"[^A-Za-zÀ-ÖØ-öø-ÿ' -]")
_MISSION_ID = r"^[a-z0-9][a-z0-9-]{0,63}$"

Text = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


def _has_emoji(text: str) -> bool:
    return any(ord(ch) >= 0x1F000 or 0x2600 <= ord(ch) <= 0x27BF for ch in text)


def stage_for(sessions_count: int) -> Stage:
    """PD-021: 1 = first meeting, 2-3 = getting to know you, 4+ = familiar companion."""
    if sessions_count <= 1:
        return "first_meeting"
    return "getting_to_know" if sessions_count <= 3 else "familiar"


def safe_first_name(raw: str) -> str:
    """Only the first name, only name-like characters: a display name is user data and must not
    be able to carry instructions into a prompt."""
    cleaned = _NAME_CHARS.sub("", raw or "").strip()
    first = cleaned.split(" ")[0] if cleaned else ""
    return first[:24] or "there"


# --- input --------------------------------------------------------------------------------------


class _Frozen(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class SkillScore(_Frozen):
    skill: Skill
    correct: int = Field(ge=0)
    total: int = Field(gt=0)
    pct: int = Field(ge=0, le=100)


class MissedItem(_Frozen):
    """A checkpoint the student missed. Allowed only because the attempt is closed."""

    skill: AnySkill
    cefr: Cefr
    prompt: str = Field(max_length=400)
    explanation: str = Field(max_length=800)
    # The student's typed or chosen text, if the backend passes it. It is DATA: adapters must
    # place it inside the delimited data block, never in the instructions.
    student_answer: str | None = Field(default=None, max_length=120)


class CoachContext(_Frozen):
    """Everything the coach may know. No emails, no ids, no answer keys of an open attempt."""

    first_name: str
    suggested_cefr: Cefr
    score_pct: int = Field(ge=0, le=100)
    skills: tuple[SkillScore, ...] = Field(min_length=1, max_length=4)
    strength: Skill
    challenge: Skill
    missed: tuple[MissedItem, ...] = Field(default=(), max_length=10)
    ending_key: str = Field(default="", max_length=32)
    rescue_used: bool = False
    hints_received: int = Field(default=0, ge=0)
    # Sessions INCLUDING this one: 1 = the first mission with Maya.
    sessions_count: int = Field(ge=1)
    last_notes: tuple[str, ...] = Field(default=(), max_length=MAX_NOTES)  # newest first
    candidate_mission_ids: tuple[str, ...] = Field(min_length=1)
    default_next_mission_id: str

    @field_validator("first_name")
    @classmethod
    def _clean_name(cls, value: str) -> str:
        return safe_first_name(value)

    @field_validator("last_notes")
    @classmethod
    def _clean_notes(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(note.strip()[:300] for note in value if note and note.strip())

    @model_validator(mode="after")
    def _consistent(self) -> Self:
        if self.strength == self.challenge:
            raise ValueError("strength and challenge must be different skills")
        if self.default_next_mission_id not in self.candidate_mission_ids:
            raise ValueError("default_next_mission_id must be one of the candidates")
        return self

    @property
    def stage(self) -> Stage:
        return stage_for(self.sessions_count)

    @property
    def is_returning(self) -> bool:
        return self.sessions_count >= 2

    def pct(self, skill: str) -> int | None:
        return next((s.pct for s in self.skills if s.skill == skill), None)


# --- output -------------------------------------------------------------------------------------


@dataclass(frozen=True)
class TokenUsage:
    input_tokens: int
    output_tokens: int


class CoachFeedback(BaseModel):
    """The strict output (SHARED_CONTEXT §6). Validate with `CoachFeedback.validated(data, ctx)`
    so the cross-checks against the context run too; free text is never trusted blindly."""

    model_config = ConfigDict(extra="forbid")

    summary: Text
    strength: Skill
    challenge: Skill
    recommendation: Text
    next_mission_id: Annotated[str, StringConstraints(pattern=_MISSION_ID)]
    memory_note: Text
    next_greeting: Text

    # Filled by adapters that call a paid API; never serialized.
    _usage: TokenUsage | None = PrivateAttr(default=None)

    @field_validator("summary", "recommendation", "memory_note", "next_greeting")
    @classmethod
    def _safe_text(cls, value: str, info: ValidationInfo) -> str:
        limit = LIMITS[str(info.field_name)]
        if len(value) > limit:
            raise ValueError(f"longer than {limit} characters")
        if _BANNED.search(value):
            raise ValueError("uses a word Maya never says (MAYA.md §8)")
        if _has_emoji(value) or _URL.search(value) or "!!" in value:
            raise ValueError("emojis, links or exclamation chains are not allowed")
        return value

    @model_validator(mode="after")
    def _matches_context(self, info: ValidationInfo) -> Self:
        ctx = (info.context or {}).get("coach_context")
        if isinstance(ctx, CoachContext):
            if self.strength != ctx.strength or self.challenge != ctx.challenge:
                raise ValueError("strength and challenge must echo the deterministic values")
            if self.next_mission_id not in ctx.candidate_mission_ids:
                raise ValueError("next_mission_id must be one of the candidates")
        return self

    @classmethod
    def validated(cls, data: Any, context: CoachContext) -> "CoachFeedback":
        return cls.model_validate(data, context={"coach_context": context})

    @property
    def usage(self) -> TokenUsage | None:
        return self._usage

    def with_usage(self, usage: TokenUsage) -> "CoachFeedback":
        self._usage = usage
        return self


# --- the port -----------------------------------------------------------------------------------


class CoachProviderError(Exception):
    """Any provider failure (API error, refusal, malformed JSON). The service falls back."""


@runtime_checkable
class CoachProvider(Protocol):
    provider: str  # stored with every feedback row: "mock", "anthropic", ...
    label: str  # shown to the student (feedback_source.provider_label), e.g. "Claude"
    model: str | None
    prompt_version: str

    def generate(self, context: CoachContext) -> CoachFeedback: ...
