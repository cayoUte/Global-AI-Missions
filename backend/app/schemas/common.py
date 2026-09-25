"""Shared DTO types (api-contract §1 and §4). Response models only; requests live per feature."""

from typing import Literal

from pydantic import BaseModel, ConfigDict

Skill = Literal["grammar", "vocabulary", "reading", "listening", "speaking"]
Cefr = Literal["PRE_A1", "A1", "A2", "B1", "B2", "C1"]
Role = Literal["student", "teacher", "admin"]
ItemType = Literal["multiple_choice", "fill_blank", "comprehension", "vocabulary"]
NodeKind = Literal["narrative", "checkpoint", "consequence", "ending"]
AttemptStatus = Literal["in_progress", "completed", "submitted"]
OpenStatus = Literal["in_progress", "completed"]
MayaDecision = Literal["quiet", "hint", "rescue"]
MayaMood = Literal["curious", "encouraging", "worried", "proud"]
CardState = Literal[
    "available", "in_progress", "waiting_to_submit", "completed", "locked", "in_preparation"
]


class RequestModel(BaseModel):
    """Base for every request body: unknown fields are a 422 (never trust the client)."""

    model_config = ConfigDict(extra="forbid")


class UserView(BaseModel):
    id: str
    email: str
    display_name: str
    role: Role


class Clock(BaseModel):
    time: str
    minutes_left: int
    train_departed: bool
    label: str


class EndingRef(BaseModel):
    key: str
    title: str


class SkillScore(BaseModel):
    skill: Skill
    correct: int
    total: int
    pct: int


class SkillPct(BaseModel):
    skill: Skill
    pct: int


class Profile(BaseModel):
    based_on_attempts: int
    skills: list[SkillPct]
