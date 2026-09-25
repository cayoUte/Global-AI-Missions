"""Data access: small, explicit query functions over the SQLAlchemy models (data-engineer).

Rules (docs/contracts/conventions.md §1):
- Every function takes the request's `Session` as its first argument. Repositories flush, they
  never commit: the service owns the transaction.
- No business logic here: no scoring, no levels, no Maya decisions, no rounding of percentages.
  Aggregates come back as raw sums (correct, total) and the service computes the %.
- Answer keys travel on one path only: `missions.get_answer_key(...)` (and
  `missions.load_mission_content(...)`, whose output feeds the engine on the server and must
  never be serialized to a client). No other function selects `is_correct` of an option or
  `accepted_answers`.
- User-facing ids (users, attempts, classes) are `uuid.UUID`. Node, item and option ids are the
  content's external ids (text).

Import modules, not names:  `from app.repositories import attempts, missions, users`.

Index (signatures; `s` = `sqlalchemy.orm.Session`):

db
    get_engine() -> Engine                                          # from settings.database_url
    get_sessionmaker() -> sessionmaker[Session]                     # for api/deps.get_session

users
    get_user_by_email(s, email: str) -> User | None                 # trims + lowercases
    get_user_by_id(s, user_id: UUID) -> User | None

missions (catalog, content, answer keys)
    list_missions(s) -> list[Mission]                               # by sort_order
    get_mission(s, mission_id: str) -> Mission | None
    get_cefr_ranks(s) -> dict[str, int]                             # {"PRE_A1": 0, ... "C1": 5}
    get_active_mission_version(s, mission_id: str) -> MissionVersion | None
    get_mission_version(s, version_id: int) -> MissionVersion | None
    load_mission_content(s, version_id: int) -> MissionContent      # (items_doc, mission_doc)
        # SERVER ONLY: the exact dicts engine.build_graph(items_doc, mission_doc) expects,
        # answer keys included. Cache per version_id in the service (content is immutable).
    get_question_id(s, version_id: int, item_id: str) -> int | None
    get_option_id(s, question_id: int, option_key: str) -> int | None
    get_answer_key(s, question_id: int) -> AnswerKey                # the grading/report path

attempts (lifecycle; the attempt row is the head, attempt_steps the search nodes)
    create_attempt(s, *, user_id, mission_id, mission_version_id, start_node_id, state,
                   maya_decision, now=None) -> Attempt | None
        # Inserts the attempt AND its root step (seq 1, on_event "start") in a SAVEPOINT.
        # Returns None when the one-open-attempt index rejects it (lost race): call
        # get_open_attempt(...) and return the winner.
    get_open_attempt(s, user_id, mission_id) -> Attempt | None     # in_progress | completed
    list_open_attempts(s, user_id) -> list[Attempt]                 # most recently active first
    get_owned_attempt(s, attempt_id, user_id) -> Attempt | None     # None if not owned (-> 404)
    lock_attempt_for_update(s, attempt_id, user_id) -> Attempt | None   # SELECT ... FOR UPDATE
    get_last_step(s, attempt_id) -> AttemptStep | None
    list_steps(s, attempt_id) -> list[AttemptStep]                  # by seq (Diary input)
    append_step(s, attempt, *, from_node_id, to_node_id, on_event, action, minutes_cost,
                minutes_left_after, maya_decision, state_after, now=None) -> AttemptStep
        # seq = last.seq + 1, parent_step_id = last.id, path_cost = last.path_cost + minutes_cost.
        # Also moves the attempt head: current_node_id = to_node_id, state = state_after,
        # last_activity_at = now. Call it under lock_attempt_for_update.
    answer_exists(s, attempt_id, question_id) -> bool               # CHECKPOINT_LOCKED check
    save_answer(s, *, attempt_id, question_id, selected_option_id=None, text_answer=None,
                is_correct, hint_shown, now=None) -> AttemptAnswer | None
        # None when UNIQUE(attempt_id, question_id) rejects it (a concurrent Confirm won).
    list_attempt_answers(s, attempt_id) -> list[AnswerRow]         # by item position
        # SERVER ONLY (grading at submit, report of a submitted attempt): carries is_correct.
    mark_attempt_completed(s, attempt, *, ending_node_id, now=None) -> None
    finish_attempt(s, attempt, *, score_pct, correct_count, incorrect_count, suggested_cefr,
                   now=None) -> None                                # status -> submitted
    save_skill_scores(s, attempt_id, scores: Iterable[SkillScoreIn]) -> None
    get_skill_scores(s, attempt_id) -> list[AttemptSkillScore]
    get_attempt_number(s, attempt) -> int                           # 1-based within its mission

progress (read models for /world, /me/progress, /teacher)
    get_profile(s, user_id, last_n=3) -> ProfileSums | None         # PD-009 / F-05, one query
    list_submitted_attempts(s, user_id) -> list[HistoryRow]         # newest first, with skills
    get_progress(s, user_id) -> ProgressData                        # profile, history,
                                                                    # level_history, notes, open
    list_teacher_classes(s, teacher_id: UUID | None) -> list[ClassSummary]   # None = admin
    list_class_progress(s, class_id, teacher_id: UUID | None) -> ClassProgress | None
        # None when the class does not exist or the teacher does not teach it (-> 404).

coach
    get_coach_memory(s, user_id) -> CoachMemory | None
    save_coach_memory(s, user_id, *, sessions_count, notes, next_greeting, now=None) -> CoachMemory
    get_coach_feedback(s, attempt_id) -> CoachFeedback | None
    get_latest_submitted_feedback(s, user_id) -> CoachFeedback | None   # is_maya_pick
    save_coach_feedback(s, *, attempt_id, provider, model, prompt_version, status, content,
                        latency_ms) -> bool
        # INSERT ... ON CONFLICT (attempt_id) DO NOTHING; True only if this call wrote the row
        # (then, and only then, update coach memory).

JSON shapes stored by the services (documented in docs/data/DATA_MODEL.md):
    attempts.state / attempt_steps.state_after = {"minutes_left": int, "flags": [str],
        "rescued": bool, "maya_mood": str}  -> engine State(node_id=<current/to node>, ...)
    attempt_steps.action = null (root) | {"kind": "continue"} | {"kind": "answer", "item_id": "q02"}
"""
