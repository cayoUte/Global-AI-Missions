"""English World, Progress and Teacher DTOs (api-contract §5.6, §5.13–§5.15).

Aggregates only: labels, percentages and counts, never item content (§9.B).
"""

from typing import Literal

from pydantic import BaseModel

from app.schemas.common import (
    CardState,
    Cefr,
    Clock,
    EndingRef,
    MayaMood,
    OpenStatus,
    Profile,
    Skill,
    SkillScore,
)


class CefrRange(BaseModel):
    min: Cefr
    max: Cefr


class OpenAttemptCard(BaseModel):
    attempt_id: str
    status: OpenStatus
    clock: Clock
    location: str
    ending: EndingRef | None


class LatestResult(BaseModel):
    attempt_id: str
    label: str
    submitted_at: str


class MissionCard(BaseModel):
    mission_id: str
    title: str
    world_zone: str
    teaser: str
    sort_order: int
    skill_focus: list[Skill]
    cefr_range: CefrRange
    playable: bool
    state: CardState
    is_maya_pick: bool
    unlock_hint: str
    open_attempt: OpenAttemptCard | None
    latest_result: LatestResult | None
    attempts_submitted: int


class StudentName(BaseModel):
    display_name: str


class Greeting(BaseModel):
    text: str
    source: Literal["first_meeting", "memory"]
    mood: MayaMood


class Snapshot(BaseModel):
    missions_played: int
    latest_label: str | None
    profile: Profile | None


class WorldResponse(BaseModel):
    student: StudentName
    greeting: Greeting
    cards: list[MissionCard]
    snapshot: Snapshot


class HistoryRow(BaseModel):
    attempt_id: str
    attempt_number: int
    mission_id: str
    mission_title: str
    submitted_at: str
    ending: EndingRef
    label: str
    suggested_cefr: Cefr
    score_pct: int
    correct: int
    incorrect: int
    skills: list[SkillScore]


class LevelPoint(BaseModel):
    attempt_id: str
    submitted_at: str
    suggested_cefr: Cefr


class Note(BaseModel):
    text: str
    created_at: str


class ProgressOpenAttempt(BaseModel):
    attempt_id: str
    mission_id: str
    mission_title: str
    status: OpenStatus
    clock: Clock


class ProgressResponse(BaseModel):
    profile: Profile | None
    history: list[HistoryRow]
    level_history: list[LevelPoint]
    notes: list[Note]
    open_attempt: ProgressOpenAttempt | None


class ClassSummary(BaseModel):
    class_id: str
    name: str
    teacher_name: str
    student_count: int


class ClassesResponse(BaseModel):
    classes: list[ClassSummary]


class ClassStudent(BaseModel):
    display_name: str
    missions_played: int
    latest_label: str | None
    profile: Profile | None
    last_activity_at: str | None


class ClassProgressResponse(BaseModel):
    class_id: str
    name: str
    students: list[ClassStudent]
