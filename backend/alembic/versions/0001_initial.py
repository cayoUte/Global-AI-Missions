"""Initial schema: reference, identity, content, attempts, results and coach tables.

Written by hand to mirror app/models (same constraint names through the naming convention), so
every constraint can be read and explained here. See docs/data/DATA_MODEL.md.

Revision ID: 0001
Revises:
Create Date: 2026-09-24
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TSTZ = sa.DateTime(timezone=True)
JSONB = postgresql.JSONB()

CEFR_LEVELS = [
    {"code": "PRE_A1", "rank": 0, "label": "Pre-A1"},
    {"code": "A1", "rank": 1, "label": "A1"},
    {"code": "A2", "rank": 2, "label": "A2"},
    {"code": "B1", "rank": 3, "label": "B1"},
    {"code": "B2", "rank": 4, "label": "B2"},
    {"code": "C1", "rank": 5, "label": "C1"},
]
SKILLS = [
    {"code": "grammar", "label": "Grammar"},
    {"code": "vocabulary", "label": "Vocabulary"},
    {"code": "reading", "label": "Reading"},
    {"code": "listening", "label": "Listening"},
    {"code": "speaking", "label": "Speaking"},
]


def upgrade() -> None:
    # --- Reference -----------------------------------------------------------------------
    cefr_levels = op.create_table(
        "cefr_levels",
        sa.Column("code", sa.String(8), nullable=False),
        sa.Column("rank", sa.SmallInteger(), nullable=False),
        sa.Column("label", sa.String(16), nullable=False),
        sa.PrimaryKeyConstraint("code", name="pk_cefr_levels"),
        sa.UniqueConstraint("rank", name="uq_cefr_levels_rank"),
    )
    skills = op.create_table(
        "skills",
        sa.Column("code", sa.String(16), nullable=False),
        sa.Column("label", sa.String(32), nullable=False),
        sa.PrimaryKeyConstraint("code", name="pk_skills"),
    )
    op.bulk_insert(cefr_levels, CEFR_LEVELS)  # the seed upserts the same rows (idempotent)
    op.bulk_insert(skills, SKILLS)

    # --- Identity ------------------------------------------------------------------------
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("email", sa.String(254), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("display_name", sa.String(80), nullable=False),
        sa.Column("role", sa.String(16), nullable=False),
        sa.Column("created_at", TSTZ, server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_users"),
        sa.UniqueConstraint("email", name="uq_users_email"),
        sa.CheckConstraint("email = lower(email)", name="ck_users_email_lowercase"),
        sa.CheckConstraint("role IN ('student', 'teacher', 'admin')", name="ck_users_role"),
    )
    op.create_table(
        "classes",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(80), nullable=False),
        sa.Column("teacher_id", sa.Uuid(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_classes"),
        sa.ForeignKeyConstraint(
            ["teacher_id"], ["users.id"], name="fk_classes_teacher_id_users", ondelete="RESTRICT"
        ),
    )
    op.create_index("ix_classes_teacher_id", "classes", ["teacher_id"])
    op.create_table(
        "class_members",
        sa.Column("class_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.PrimaryKeyConstraint("class_id", "user_id", name="pk_class_members"),
        sa.ForeignKeyConstraint(
            ["class_id"], ["classes.id"], name="fk_class_members_class_id_classes",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name="fk_class_members_user_id_users", ondelete="CASCADE"
        ),
    )

    # --- Content -------------------------------------------------------------------------
    op.create_table(
        "missions",
        sa.Column("id", sa.String(64), nullable=False),
        sa.Column("title", sa.String(80), nullable=False),
        sa.Column("world_zone", sa.String(64), nullable=False),
        sa.Column("skill_focus", postgresql.ARRAY(sa.String(16)), nullable=False),
        sa.Column("cefr_min", sa.String(8), nullable=False),
        sa.Column("cefr_max", sa.String(8), nullable=False),
        sa.Column("playable", sa.Boolean(), nullable=False),
        sa.Column("unlock_rule", JSONB, nullable=False),
        sa.Column("teaser", sa.Text(), nullable=False),
        sa.Column("sort_order", sa.SmallInteger(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_missions"),
        sa.ForeignKeyConstraint(
            ["cefr_min"], ["cefr_levels.code"], name="fk_missions_cefr_min_cefr_levels"
        ),
        sa.ForeignKeyConstraint(
            ["cefr_max"], ["cefr_levels.code"], name="fk_missions_cefr_max_cefr_levels"
        ),
    )
    op.create_table(
        "mission_versions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("mission_id", sa.String(64), nullable=False),
        sa.Column("version", sa.SmallInteger(), nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("content", JSONB, nullable=False),
        sa.Column("published_at", TSTZ, server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_mission_versions"),
        sa.UniqueConstraint("mission_id", "version", name="uq_mission_versions_mission_id_version"),
        sa.UniqueConstraint(
            "mission_id", "content_hash", name="uq_mission_versions_mission_id_content_hash"
        ),
        sa.ForeignKeyConstraint(
            ["mission_id"], ["missions.id"], name="fk_mission_versions_mission_id_missions",
            ondelete="RESTRICT",
        ),
    )
    op.create_table(
        "questions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("mission_version_id", sa.Integer(), nullable=False),
        sa.Column("external_id", sa.String(32), nullable=False),
        sa.Column("type", sa.String(20), nullable=False),
        sa.Column("skill", sa.String(16), nullable=False),
        sa.Column("cefr", sa.String(8), nullable=False),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("stimulus", JSONB, nullable=True),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("hint", sa.Text(), nullable=False),
        sa.Column("position", sa.SmallInteger(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_questions"),
        sa.UniqueConstraint(
            "mission_version_id", "external_id", name="uq_questions_mission_version_id_external_id"
        ),
        # Also the (mission_version_id, position) index for "items of a version in order".
        sa.UniqueConstraint(
            "mission_version_id", "position", name="uq_questions_mission_version_id_position"
        ),
        sa.CheckConstraint(
            "type IN ('multiple_choice', 'fill_blank', 'comprehension', 'vocabulary')",
            name="ck_questions_type",
        ),
        sa.ForeignKeyConstraint(
            ["mission_version_id"], ["mission_versions.id"],
            name="fk_questions_mission_version_id_mission_versions", ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(["skill"], ["skills.code"], name="fk_questions_skill_skills"),
        sa.ForeignKeyConstraint(
            ["cefr"], ["cefr_levels.code"], name="fk_questions_cefr_cefr_levels"
        ),
    )
    op.create_table(
        "question_options",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("question_id", sa.Integer(), nullable=False),
        sa.Column("option_key", sa.String(8), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("position", sa.SmallInteger(), nullable=False),
        sa.Column("is_correct", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_question_options"),
        sa.UniqueConstraint(
            "question_id", "option_key", name="uq_question_options_question_id_option_key"
        ),
        sa.ForeignKeyConstraint(
            ["question_id"], ["questions.id"], name="fk_question_options_question_id_questions",
            ondelete="CASCADE",
        ),
    )
    # At most one correct option per question (exactly one: the engine validator, pre-seed).
    op.create_index(
        "uq_question_options_one_correct", "question_options", ["question_id"],
        unique=True, postgresql_where=sa.text("is_correct"),
    )
    op.create_table(
        "accepted_answers",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("question_id", sa.Integer(), nullable=False),
        sa.Column("answer_normalized", sa.String(80), nullable=False),
        sa.Column("is_primary", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_accepted_answers"),
        sa.UniqueConstraint(
            "question_id", "answer_normalized",
            name="uq_accepted_answers_question_id_answer_normalized",
        ),
        sa.ForeignKeyConstraint(
            ["question_id"], ["questions.id"], name="fk_accepted_answers_question_id_questions",
            ondelete="CASCADE",
        ),
    )
    op.create_index(
        "uq_accepted_answers_one_primary", "accepted_answers", ["question_id"],
        unique=True, postgresql_where=sa.text("is_primary"),
    )

    # --- Attempts ------------------------------------------------------------------------
    op.create_table(
        "attempts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("mission_id", sa.String(64), nullable=False),
        sa.Column("mission_version_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("current_node_id", sa.String(64), nullable=False),
        sa.Column("state", JSONB, nullable=False),
        sa.Column("started_at", TSTZ, server_default=sa.func.now(), nullable=False),
        sa.Column("last_activity_at", TSTZ, server_default=sa.func.now(), nullable=False),
        sa.Column("completed_at", TSTZ, nullable=True),
        sa.Column("submitted_at", TSTZ, nullable=True),
        sa.Column("score_pct", sa.SmallInteger(), nullable=True),
        sa.Column("correct_count", sa.SmallInteger(), nullable=True),
        sa.Column("incorrect_count", sa.SmallInteger(), nullable=True),
        sa.Column("suggested_cefr", sa.String(8), nullable=True),
        sa.Column("ending_node_id", sa.String(64), nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_attempts"),
        sa.CheckConstraint(
            "status IN ('in_progress', 'completed', 'submitted')", name="ck_attempts_status"
        ),
        sa.CheckConstraint(
            "status = 'in_progress' OR (completed_at IS NOT NULL AND ending_node_id IS NOT NULL)",
            name="ck_attempts_finished_has_ending",
        ),
        sa.CheckConstraint(
            "status <> 'submitted' OR (submitted_at IS NOT NULL AND score_pct IS NOT NULL"
            " AND correct_count IS NOT NULL AND incorrect_count IS NOT NULL"
            " AND suggested_cefr IS NOT NULL)",
            name="ck_attempts_submitted_has_result",
        ),
        sa.CheckConstraint("score_pct BETWEEN 0 AND 100", name="ck_attempts_score_pct_range"),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name="fk_attempts_user_id_users", ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["mission_id"], ["missions.id"], name="fk_attempts_mission_id_missions",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["mission_version_id"], ["mission_versions.id"],
            name="fk_attempts_mission_version_id_mission_versions", ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["suggested_cefr"], ["cefr_levels.code"], name="fk_attempts_suggested_cefr_cefr_levels"
        ),
    )
    # One open attempt (in_progress, or completed and not yet submitted) per student and mission.
    op.create_index(
        "uq_attempts_one_open", "attempts", ["user_id", "mission_id"],
        unique=True, postgresql_where=sa.text("status IN ('in_progress', 'completed')"),
    )
    op.create_index(
        "ix_attempts_user_id_submitted_at", "attempts", ["user_id", sa.text("submitted_at DESC")]
    )

    op.create_table(
        "attempt_steps",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("attempt_id", sa.Uuid(), nullable=False),
        sa.Column("seq", sa.SmallInteger(), nullable=False),
        sa.Column("parent_step_id", sa.BigInteger(), nullable=True),
        sa.Column("from_node_id", sa.String(64), nullable=True),
        sa.Column("to_node_id", sa.String(64), nullable=False),
        sa.Column("on_event", sa.String(16), nullable=False),
        sa.Column("action", JSONB, nullable=True),
        sa.Column("minutes_cost", sa.SmallInteger(), nullable=False),
        sa.Column("path_cost", sa.SmallInteger(), nullable=False),
        sa.Column("minutes_left_after", sa.SmallInteger(), nullable=False),
        sa.Column("maya_decision", sa.String(8), nullable=False),
        sa.Column("state_after", JSONB, nullable=False),
        sa.Column("created_at", TSTZ, server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_attempt_steps"),
        # Also the (attempt_id, seq) index used to read an attempt's steps in order.
        sa.UniqueConstraint("attempt_id", "seq", name="uq_attempt_steps_attempt_id_seq"),
        sa.CheckConstraint(
            "on_event IN ('start', 'always', 'correct', 'incorrect', 'ending')",
            name="ck_attempt_steps_on_event",
        ),
        sa.CheckConstraint(
            "maya_decision IN ('quiet', 'hint', 'rescue')", name="ck_attempt_steps_maya_decision"
        ),
        sa.CheckConstraint(
            "(seq = 1 AND on_event = 'start' AND parent_step_id IS NULL AND from_node_id IS NULL)"
            " OR (seq > 1 AND on_event <> 'start' AND parent_step_id IS NOT NULL"
            " AND from_node_id IS NOT NULL)",
            name="ck_attempt_steps_root_or_child",
        ),
        sa.CheckConstraint("minutes_cost >= 0", name="ck_attempt_steps_minutes_cost_positive"),
        sa.ForeignKeyConstraint(
            ["attempt_id"], ["attempts.id"], name="fk_attempt_steps_attempt_id_attempts",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["parent_step_id"], ["attempt_steps.id"],
            name="fk_attempt_steps_parent_step_id_attempt_steps", ondelete="CASCADE",
        ),
    )

    op.create_table(
        "attempt_answers",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("attempt_id", sa.Uuid(), nullable=False),
        sa.Column("question_id", sa.Integer(), nullable=False),
        sa.Column("selected_option_id", sa.Integer(), nullable=True),
        sa.Column("text_answer", sa.String(200), nullable=True),
        sa.Column("is_correct", sa.Boolean(), nullable=False),
        sa.Column("hint_shown", sa.Boolean(), nullable=False),
        sa.Column("answered_at", TSTZ, server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_attempt_answers"),
        # One answer per checkpoint; the leading attempt_id also serves attempt_answers lookups.
        sa.UniqueConstraint(
            "attempt_id", "question_id", name="uq_attempt_answers_attempt_id_question_id"
        ),
        sa.CheckConstraint(
            "num_nonnulls(selected_option_id, text_answer) = 1", name="ck_attempt_answers_one_answer"
        ),
        sa.ForeignKeyConstraint(
            ["attempt_id"], ["attempts.id"], name="fk_attempt_answers_attempt_id_attempts",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["question_id"], ["questions.id"], name="fk_attempt_answers_question_id_questions",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["selected_option_id"], ["question_options.id"],
            name="fk_attempt_answers_selected_option_id_question_options", ondelete="RESTRICT",
        ),
    )

    # --- Results -------------------------------------------------------------------------
    op.create_table(
        "attempt_skill_scores",
        sa.Column("attempt_id", sa.Uuid(), nullable=False),
        sa.Column("skill", sa.String(16), nullable=False),
        sa.Column("correct", sa.SmallInteger(), nullable=False),
        sa.Column("total", sa.SmallInteger(), nullable=False),
        sa.Column("pct", sa.SmallInteger(), nullable=False),
        sa.PrimaryKeyConstraint("attempt_id", "skill", name="pk_attempt_skill_scores"),
        sa.CheckConstraint(
            "total > 0 AND correct BETWEEN 0 AND total", name="ck_attempt_skill_scores_counts"
        ),
        sa.CheckConstraint("pct BETWEEN 0 AND 100", name="ck_attempt_skill_scores_pct_range"),
        sa.ForeignKeyConstraint(
            ["attempt_id"], ["attempts.id"], name="fk_attempt_skill_scores_attempt_id_attempts",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["skill"], ["skills.code"], name="fk_attempt_skill_scores_skill_skills"
        ),
    )

    # --- Coach ---------------------------------------------------------------------------
    op.create_table(
        "coach_feedback",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("attempt_id", sa.Uuid(), nullable=False),
        sa.Column("provider", sa.String(32), nullable=False),
        sa.Column("model", sa.String(64), nullable=True),
        sa.Column("prompt_version", sa.String(32), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("content", JSONB, nullable=False),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("created_at", TSTZ, server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_coach_feedback"),
        sa.UniqueConstraint("attempt_id", name="uq_coach_feedback_attempt_id"),
        sa.CheckConstraint("status IN ('ready', 'fallback')", name="ck_coach_feedback_status"),
        sa.ForeignKeyConstraint(
            ["attempt_id"], ["attempts.id"], name="fk_coach_feedback_attempt_id_attempts",
            ondelete="CASCADE",
        ),
    )
    op.create_table(
        "coach_memory",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("sessions_count", sa.Integer(), nullable=False),
        sa.Column("notes", JSONB, nullable=False),
        sa.Column("next_greeting", sa.Text(), nullable=True),
        sa.Column("updated_at", TSTZ, server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("user_id", name="pk_coach_memory"),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name="fk_coach_memory_user_id_users", ondelete="CASCADE"
        ),
    )


def downgrade() -> None:
    for table in (
        "coach_memory",
        "coach_feedback",
        "attempt_skill_scores",
        "attempt_answers",
        "attempt_steps",
        "attempts",
        "accepted_answers",
        "question_options",
        "questions",
        "mission_versions",
        "missions",
        "class_members",
        "classes",
        "users",
        "skills",
        "cefr_levels",
    ):
        op.drop_table(table)
