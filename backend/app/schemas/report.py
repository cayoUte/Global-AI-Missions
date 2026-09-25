"""Mission Report DTOs (api-contract §7). Only ever built for a SUBMITTED attempt."""

from typing import Literal

from pydantic import BaseModel

from app.schemas.common import CardState, Cefr, EndingRef, ItemType, MayaDecision, Skill, SkillScore
from app.schemas.state import Stimulus


class LevelEvidence(BaseModel):
    cefr: Cefr
    correct: int
    total: int
    required: int
    met: bool


class SuggestedLevel(BaseModel):
    cefr: Cefr
    base_cefr: Cefr
    reason: str
    evidence: list[LevelEvidence]


class ResultBlock(BaseModel):
    score_pct: int
    correct: int
    incorrect: int
    total: int
    skills: list[SkillScore]
    unmeasured_skills: list[Skill]
    suggested_level: SuggestedLevel


class AttemptRecord(BaseModel):
    attempt_number: int
    started_at: str
    submitted_at: str
    ending: EndingRef
    story_minutes_used: int
    rescue_used: bool
    hints_received: int


class Interpretation(BaseModel):
    summary: str
    strength: Skill
    challenge: Skill
    recommendation: str


class FeedbackSource(BaseModel):
    status: Literal["ready", "fallback"]
    provider_label: str


class NextMission(BaseModel):
    mission_id: str
    title: str
    skill_focus: list[Skill]
    reason: str
    state: CardState
    unlock_hint: str


class DiaryCheckpoint(BaseModel):
    item_id: str
    type: ItemType
    skill: Skill
    cefr: Cefr
    outcome: Literal["understood", "missed"]


class DiaryEntryView(BaseModel):
    seq: int
    clock: str
    node_id: str
    kind: str
    location: str
    text: str
    checkpoint: DiaryCheckpoint | None
    maya_decision: MayaDecision


class MissedCheckpoint(BaseModel):
    item_id: str
    type: ItemType
    skill: Skill
    cefr: Cefr
    prompt: str
    stimulus: Stimulus | None
    your_answer: str
    correct_answer: str
    explanation: str
    maya_tip: str


class Report(BaseModel):
    attempt_id: str
    mission_id: str
    mission_title: str
    label: str
    result: ResultBlock
    attempt_record: AttemptRecord
    interpretation: Interpretation
    feedback_source: FeedbackSource
    next_mission: NextMission | None
    diary: list[DiaryEntryView]
    missed: list[MissedCheckpoint]
