# TEST PLAN — Global AI Missions

> Owner: `qa-engineer`. Internal working note (English). Sources: `docs/agents/SHARED_CONTEXT.md` §1, §4, §5, §9 · `docs/product/PRODUCT.md` §5, §12 · `docs/product/REQUIREMENTS_MAP.md` · `docs/contracts/api-contract.md`.
> Manual checks, bugs and the delivery checklist live in [`CHECKLIST.md`](CHECKLIST.md); the evaluator walkthrough in [`DEMO_SCRIPT.md`](DEMO_SCRIPT.md).
> State on 2026-09-25 (after the stretch items): backend **322 passed** (≈30 s), frontend Vitest **45 passed**, Playwright **10 passed**, 1 skipped (a mobile-only test in the desktop project). BUG-001 is fixed, so its width check is a normal test.

## 1. How to run everything

| Command | What | Needs |
|---|---|---|
| `make test` | pytest (backend, all layers) + Vitest (frontend) | `make up` (PostgreSQL on 127.0.0.1:5433). Without it the PostgreSQL tests skip with the reason printed |
| `make test E2E=1` | the above, then the Playwright E2E | also a Chromium for Playwright (`cd frontend && npx playwright install chromium` on a fresh machine) |
| `make e2e` | only the E2E: builds the SPA, recreates, migrates and seeds a throwaway database `gam_e2e`, serves the SPA from FastAPI on `127.0.0.1:8765`, runs `frontend/e2e/*.spec.ts` | same |
| `make lint` | ruff + ESLint + tsc + Prettier (covers `frontend/e2e` too) | — |

The E2E never touches the demo database `gam` (Ana stays fresh for the demo). Never run two pytest processes at once: the data tests drop and recreate `gam_test`.

## 2. Risk-based strategy — which tests first, and why (interview question 9)

We test first what would make the product **untrustworthy as an assessment**, then what would make the **demo fail**, then everything else. Order and reasons:

| # | Risk | Why it comes first | Tests (layer) |
|---|---|---|---|
| 1 | **Score integrity**: a wrong grade, per-skill %, count or level | It is the product's output; every other feature is decoration if the number is wrong. Pure functions → cheap, exhaustive, deterministic | `services/test_grading_leveling.py` (all 9 worked examples of ASSESSMENT_SPEC, rounding, cap step-down, label format) (unit) |
| 2 | **Answer-key leakage**: keys, explanations, edges or future nodes reaching the browser while an attempt is open | One leak and the assessment is worthless (interview Q2); it is invisible in the UI, so only a machine scan catches it | recursive forbidden-field scan over every response of full runs, including every 409 body, on fakes and on PostgreSQL; StateView whitelist; SPA source and bundle scan (API + contract) |
| 3 | **Client tampering**: a browser that sends a score, correctness, extra fields, a second answer, a future node | Interview Q8; the server must be the only authority | `extra="forbid"` → 422, answer twice → 409, wrong node → 409, submit before the ending → 409 (API) |
| 4 | **Ownership and roles**: another student's attempt, a student on teacher endpoints, a teacher on another class | Privacy and RBAC (interview Q6); 404 instead of 403 prevents enumeration | 404 everywhere for foreign/malformed ids, 401/403 per role, admin fixture (API) |
| 5 | **Engine invariants**: every one of the 1,024 paths keeps 10 checkpoints and the 4/2/2/2 blueprint; the heuristic is exact; one rescue at most | A content or graph change could silently give some students 9 items or a different blueprint | validator on fixture and real content, broken-content fixtures, independent enumeration of the real mission (unit) |
| 6 | **Concurrency and idempotency**: double Confirm, two tabs, retried or concurrent submit | Real networks retry; a race must never double-grade, double-answer or 5xx | concurrent answers and submits on real PostgreSQL (row locks, unique index, `ON CONFLICT`); submit idempotency; two-tab E2E (integration) |
| 7 | **Resume**: lost connection, reload, new device | Interview Q7; the student must never lose a run | same-cookie and fresh-login resume (API), reload in E2E |
| 8 | **AI fallback**: timeout, invalid key, malformed JSON, unknown mission | The report must always render and the LLM must never touch score or level (§9.6) | provider failures at unit level (`tests/ai`) and through `submit` over HTTP (API) |
| 9 | **The evaluator's path**: login → dashboard → 10 items → submit → report → progress, keyboard-only and at 360 px | What the evaluators click in the first minute; also covers the glue no unit test sees | 2 Playwright specs (E2E) |

Deliberately **not** automated: visual polish, speech on real voices, screen readers (manual, `CHECKLIST.md`). Calibration of the simulator is informational (SHARED_CONTEXT §5), not a gate. `/simulate` and the replay are stretch and **out of scope** for this build (not a gap).

Determinism rules: the mock coach everywhere (`COACH_PROVIDER=mock`; provider failures are injected with fake SDK clients, never a real key or a real Anthropic call), seeded simulator (`run(..., seed)`), a frozen clock in the fake store, fixed answer sequences in the E2E, one E2E worker over a freshly seeded database.

## 3. Test pyramid

```
                 ▲  E2E (Playwright, real stack, 7 tests in 2 specs)          ~30 s
                ▲▲▲  API over the real app (FastAPI TestClient)
               ▲▲▲▲▲   - on the in-memory FakeStore (fast, every rule)
              ▲▲▲▲▲▲▲  - on PostgreSQL gam_test (locks, races, seed: 4 API + 18 data)
            ▲▲▲▲▲▲▲▲▲▲▲ Unit: engine, grading/leveling, state view, coach, content schemas
```

| Layer | Where | Count | Speed |
|---|---|---|---|
| Unit — engine (graph, RESULT, h, Maya, simulator, diary, validator) | `backend/tests/engine/` | 75 | < 3 s |
| Unit — services (grading, leveling, state view, coach, rate limiter) | `backend/tests/services/` | 32 | < 1 s |
| Unit — AI adapters, validation, memory | `backend/tests/ai/` | 45 | < 2 s |
| Contracts — JSON Schemas, content, SPA answer scan | `backend/tests/contracts/` | 32 | < 1 s |
| Data — migration, constraints, seed, repositories (PostgreSQL) | `backend/tests/data/` | 18 | ~8 s |
| API — HTTP flow, security, auth (fakes) + PostgreSQL flow and races | `backend/tests/api/` + `test_health.py` | 49 + 2 | ~10 s |
| Frontend unit — reducer, check-in, fill-blank, listening fallback, session | `frontend/src/**/*.test.ts(x)` | 26 | ~5 s |
| E2E — journeys | `frontend/e2e/` | 7 | ~30 s |

The backend suite runs in ≈25 s (budget: 60 s).

## 4. What QA added (2026-09-25)

| File | Tests | Closes |
|---|---|---|
| `backend/tests/api/test_qa_gaps.py` | `test_every_protected_endpoint_is_401_unauthenticated_without_a_cookie`, `test_conflict_bodies_of_an_open_attempt_leak_nothing`, `test_a_new_client_session_resumes_the_same_node_and_state`, `test_a_broken_ai_provider_never_breaks_submit_or_changes_the_grade[timeout, invalid_key, malformed_json, unknown_mission]`, `test_a_valid_ai_provider_is_ready_and_still_cannot_change_the_grade` | 401 code on every endpoint; leaks in 409 bodies; resilience; AI fallback through submit (R-32, R-34) |
| `backend/tests/api/test_postgres_concurrency.py` | `test_two_concurrent_answers_lock_the_checkpoint_once`, `test_two_concurrent_submits_make_one_report_and_one_memory_update`, `test_the_seeded_veteran_progress_over_http` | concurrent submits (one report, `sessions_count` +1, no 5xx); veteran progress over HTTP (R-09) |
| `backend/tests/engine/test_real_mission_invariants.py` | `test_all_1024_paths_visit_the_same_10_checkpoints_with_the_4_2_2_2_blueprint`, `test_every_path_ends_in_one_of_three_endings_with_at_most_one_rescue`, `test_the_heuristic_is_exact_admissible_and_consistent_on_the_real_graph`, `test_the_simulator_is_deterministic_on_the_real_mission` | invariants on the **real** content, independent of the validator |
| `backend/tests/contracts/test_spa_has_no_answers.py` | `test_the_spa_source_has_no_item_content_or_answer_keys`, `test_the_production_bundle_has_no_item_content_or_answer_keys` (skips when `frontend/dist` is not built) | R-22 "build scan" |
| `frontend/e2e/mission.spec.ts` | `new student: check-in → full mission by keyboard → report → progress` (desktop 1280×800 and mobile 360×740), `Progress has no horizontal page scroll at 360 and 768 px` (expected failure, BUG-001) | R-01…R-09, R-15…R-20, R-28 |
| `frontend/e2e/resilience.spec.ts` | `Maya's rescue: a shortcut, the ending Made It Together, and the report records it`, `two tabs, a reload and no speech: the server state wins, nothing breaks`, `reduced motion › the motion tokens drop to the reduced values and the run still works` | rescue UI, 409 resync, resume, PD-014, reduced motion |

## 5. Traceability matrix

Test ids: `backend/tests/<path>::<test>` (pytest) · `vitest <file> › <it>` · `e2e <spec> › <title>` · `M-xx` = manual check in `CHECKLIST.md` · `DOC` = document review at G4 (delivery checklist). Paths below are relative to `backend/tests/` unless they start with `frontend/`.

### 5.1 Flow

| ID | Requirement | Automated | Manual |
|---|---|---|---|
| R-01 | Student login | `api/test_auth.py::test_login_sets_an_httponly_lax_cookie_and_returns_the_user`, `::test_unknown_email_and_wrong_password_get_the_same_response`, `::test_logout_is_204_and_clears_the_cookie`, `::test_me_without_a_cookie_is_200_null`; `vitest CheckInPage.test.tsx › routes a student to the English World after check-in`; `e2e mission.spec.ts › new student…` (keyboard check-in) | demo 0:00 |
| R-02 | Student dashboard | `api/test_mission_flow.py::test_full_run_leaks_nothing_and_the_report_has_the_numbers` (card states, greeting, snapshot, Maya's pick), `::test_an_open_run_shows_in_progress_on_the_world_and_progress`; `e2e mission.spec.ts › new student…` | demo 0:30 |
| R-03 | Access an assessment | `api/test_mission_flow.py::test_an_open_run_shows_in_progress_on_the_world_and_progress` (201 then 200 same run), `::test_play_again_creates_a_new_numbered_attempt`; `api/test_attempt_security.py::test_locked_non_playable_and_unknown_missions_cannot_be_started`; `data/test_schema.py::test_one_open_attempt_per_student_and_mission` | demo 0:45 |
| R-04 | Answer 10 questions | `engine/test_validator.py::test_real_mission_is_valid`, `engine/test_real_mission_invariants.py::test_all_1024_paths_visit_the_same_10_checkpoints_with_the_4_2_2_2_blueprint`; `e2e mission.spec.ts › new student…` (asserts 10 checkpoints) | demo |
| R-05 | Submit the answers | `api/test_mission_flow.py::test_full_run_leaks_nothing_and_the_report_has_the_numbers` (start returns the finished run, submit idempotent), `api/test_postgres_concurrency.py::test_two_concurrent_submits_make_one_report_and_one_memory_update`, `api/test_attempt_security.py::test_submit_before_the_ending_is_409_mission_not_finished`, `::test_a_second_answer_is_409_checkpoint_locked_with_the_current_state` | demo 5:30 |
| R-06 | Score calculation | `services/test_grading_leveling.py::test_worked_examples[example1..9]`, `::test_percent_rounds_half_up_with_integers`, `::test_hints_never_change_the_score`; `api/test_attempt_security.py::test_the_client_can_never_send_a_score` | — |
| R-07 | Result per skill | `services/test_grading_leveling.py::test_worked_examples` (4/2/2/2 denominators); `api/test_mission_flow.py::test_full_run_leaks_nothing_and_the_report_has_the_numbers`; `e2e mission.spec.ts › new student…` ("Result per skill" heading) | demo |
| R-08 | Attempt record | `engine/test_simulator_and_diary.py::test_diary_rebuilds_the_path_from_parent_pointers`; `data/test_repositories.py::test_ownership_and_steps`; `data/test_seed.py::test_each_seeded_attempt_produces_a_report`; `api/test_mission_flow.py::test_full_run_leaks_nothing_and_the_report_has_the_numbers` (attempt_record); `e2e mission.spec.ts › new student…` ("Attempt record" heading) | demo 7:00 |
| R-09 | Progress view | `api/test_postgres_concurrency.py::test_the_seeded_veteran_progress_over_http` (4 rows, profile of 3, ≤ 5 notes newest first); `data/test_repositories.py::test_progress_of_the_veteran`; `api/test_mission_flow.py::test_play_again_creates_a_new_numbered_attempt`; `e2e mission.spec.ts › new student…` (profile + newest row) | M-01 (Progress width, BUG-001); demo with `veteran@` |

### 5.2 Items

| ID | Requirement | Automated | Manual |
|---|---|---|---|
| R-10 | 10 items, 4 MC / 2 fill / 2 comprehension / 2 vocabulary | `engine/test_real_mission_invariants.py::test_all_1024_paths_visit_the_same_10_checkpoints_with_the_4_2_2_2_blueprint`; `engine/test_validator.py::test_validator_rejects_broken_content` (blueprint case); `contracts/test_content_contracts.py::test_repository_content_is_valid` | — |
| R-11 | Each item stores level, skill, prompt, options, correct answer | `contracts/test_content_contracts.py::test_invalid_items_are_rejected`; `engine/test_validator.py::test_validator_rejects_broken_content`, `::test_cli_validate_fails_on_a_broken_answer_key`; `data/test_repositories.py::test_answer_key_path` | — |
| R-12 | Suggested skills incl. Speaking | `api/test_mission_flow.py::test_full_run_leaks_nothing_and_the_report_has_the_numbers` (`unmeasured_skills == ["speaking"]`); `e2e mission.spec.ts › new student…` (speaking note visible) | DOC (DECISIONS roadmap) |
| R-13 | Items leveled (CEFR) | `engine/test_real_mission_invariants.py::test_all_1024_paths_visit_the_same_10_checkpoints_with_the_4_2_2_2_blueprint` (A1×2 → A2×3 → B1×3 → B2×2); `engine/test_validator.py::test_validator_rejects_broken_content` (CEFR order case) | — |
| R-14 | AI English Coach | `engine/test_heuristic_and_maya.py::test_hint_threshold_is_slack_below_3`, `::test_rescue_policy`, `::test_rescue_transition_and_single_rescue`, `::test_mood_machine`; `ai/test_mock_and_ports.py::test_returning_student_gets_one_concrete_memory`; `e2e resilience.spec.ts › Maya's rescue…` | M-11; demo |

### 5.3 Result screen

| ID | Requirement | Automated | Manual |
|---|---|---|---|
| R-15 | Global score in % | `api/test_mission_flow.py::test_full_run_leaks_nothing_and_the_report_has_the_numbers`; `e2e mission.spec.ts › new student…` (heading `B1 · The Last Train — 80%`, tile 80%) | demo |
| R-16 | Result per skill | as R-07 | demo |
| R-17 | Correct / incorrect counts | `services/test_grading_leveling.py::test_worked_examples` (sum 10); `e2e mission.spec.ts › new student…` (8 / 2) | demo |
| R-18 | Suggested level or interpretation | `services/test_grading_leveling.py::test_worked_examples`, `::test_example_3_evidence_matches_the_contract`, `::test_a_level_with_no_items_is_never_met`; `ai/test_service_and_fallback.py::test_mock_is_reported_as_fallback`; `e2e mission.spec.ts › new student…` ("80% points to B1.") | demo |
| R-19 | Attempt record on the result screen | as R-08; `e2e resilience.spec.ts › Maya's rescue…` ("Maya's shortcut: Used") | demo |
| R-20 | Example label format | `services/test_grading_leveling.py::test_report_label_format` | — |

### 5.4 Technical

| ID | Requirement | Automated | Manual |
|---|---|---|---|
| R-21 | Separation FE / BE / persistence | `ai/test_factory_and_seam.py::test_no_provider_sdk_is_imported_outside_app_ai` (layering of the AI seam) | DOC (G0 structure, DECISIONS) |
| R-22 | Questions and answers not hardcoded in the frontend | `api/test_mission_flow.py::test_full_run_leaks_nothing_and_the_report_has_the_numbers`, `::test_the_real_mission_runs_end_to_end_without_leaks`, `api/test_postgres_flow.py::test_walking_skeleton_on_postgres`, `api/test_qa_gaps.py::test_conflict_bodies_of_an_open_attempt_leak_nothing`, `services/test_state_view.py::test_no_forbidden_key_on_any_node`, `::test_checkpoint_view_is_a_whitelist`, `contracts/test_spa_has_no_answers.py::test_the_spa_source_has_no_item_content_or_answer_keys`, `::test_the_production_bundle_has_no_item_content_or_answer_keys` | M-14; demo 8:30 (DevTools) |
| R-23 | A database | `data/test_schema.py::test_migration_matches_models`; `data/test_seed.py::test_seed_is_idempotent` | — |
| R-24 | API to fetch and submit | `api/test_mission_flow.py` (whole file), `api/test_postgres_flow.py::test_walking_skeleton_on_postgres` | — |
| R-25 | Basic authentication | `api/test_qa_gaps.py::test_every_protected_endpoint_is_401_unauthenticated_without_a_cookie`; `api/test_auth.py::test_login_rate_limit_is_5_per_minute_per_ip_and_email`, `::test_tampered_forged_or_expired_cookie_is_401`, `::test_the_role_comes_from_the_database_not_the_token`; `api/test_attempt_security.py::test_student_endpoints_need_a_session_and_the_student_role`, `::test_another_students_attempt_is_404_everywhere` | demo 9:30 |
| R-26 | Error handling and validation | `api/test_attempt_security.py::test_answer_shape_errors_are_422_and_do_not_lock` (both / neither / extra / shape), `::test_item_rules_are_422_and_the_checkpoint_stays_answerable` (text on a choice item), `::test_fill_blank_needs_1_to_80_characters_after_normalization` (whitespace-only), `::test_answer_on_a_non_checkpoint_or_a_future_checkpoint_is_409`, `::test_malformed_and_unknown_ids_are_404_not_422`; `vitest playerReducer.test.ts › renders the server's truth on a 409 resync, silently`, `› unlocks the checkpoint on a 422…`; `e2e resilience.spec.ts › two tabs…` | — |
| R-27 | Organized, readable code | CI lint: `make lint` (ruff, ESLint, tsc, Prettier) | DOC (G4) |
| R-28 | Responsive design | `e2e mission.spec.ts › new student…` [mobile-360] (no horizontal scroll on World, Player, Report); `e2e mission.spec.ts › Progress has no horizontal page scroll at 360 and 768 px` (**expected failure: BUG-001**) | M-01, M-02, M-03 |
| R-29 | Git | — | DOC (git log at G4) |
| R-30 | README with run instructions | — | M-08 (fresh clone) |
| R-31 | Justified stack | — | DOC |

### 5.5 AI

| ID | Requirement | Automated | Manual |
|---|---|---|---|
| R-32 | Brief educational feedback | `api/test_qa_gaps.py::test_a_broken_ai_provider_never_breaks_submit_or_changes_the_grade[…]`, `::test_a_valid_ai_provider_is_ready_and_still_cannot_change_the_grade`; `ai/test_service_and_fallback.py::test_malformed_json_falls_back`, `::test_api_errors_fall_back`, `::test_timeout_falls_back_within_the_budget`, `::test_invalid_skill_or_unknown_mission_falls_back`; `services/test_coach_and_limits.py::test_errors_and_timeouts_fall_back_within_the_budget`; `api/test_mission_flow.py::test_a_coach_failure_after_grading_still_returns_the_report` | M-12 (report footer per provider) |
| R-33 | Explanation of how an LLM powers feedback, accompaniment, reminders, assistance | `ai/test_service_and_fallback.py::test_memory_round_trip_personalizes_the_next_report` (evidence of memory) | DOC (`docs/ai/AI_ARCHITECTURE.md`); demo 7:00 |
| R-34 | AI never influences score, level or unlocks | `api/test_qa_gaps.py::test_a_broken_ai_provider_never_breaks_submit_or_changes_the_grade[…]` (identical `result`), `::test_a_valid_ai_provider_is_ready_and_still_cannot_change_the_grade` | — |

### 5.6 Decisions document (R-35 … R-43)

All **DOC**, checked at G4 (delivery checklist in `CHECKLIST.md` §4). Automated evidence for R-38 is R-22; for R-40 it is R-25 plus `api/test_attempt_security.py::test_teacher_rbac` (teacher of another class → 404, admin fixture → 200); for R-41 `ai/test_factory_and_seam.py::test_factory_selects_by_coach_provider` and `::test_real_settings_accept_any_provider_name_and_boot_with_the_mock`.

### 5.7 Deliverables and conditions

| ID | Requirement | Automated | Manual |
|---|---|---|---|
| R-44 | Git repository | — | DOC |
| R-45 | Runs locally | `make e2e` boots the real stack from scratch (migrate + seed + serve) | M-08 |
| R-46 | README | — | M-08 |
| R-47 | Decisions document | — | DOC |
| R-48 | Test credentials | `api/test_auth.py::test_config_lists_demo_accounts_only_in_demo_mode`, `::test_config_hides_demo_accounts_when_demo_mode_is_off`; `data/test_seed.py::test_seed_is_idempotent`; `vitest CheckInPage.test.tsx › hides the demo panel unless the server says demo mode is on` | demo 0:00 |
| R-49 | Docker | — | M-08 |
| R-50 | Automated tests | this plan; `make test E2E=1` | — |
| R-51 | Deploy (optional) | — | delivery decision |
| R-52 | Real AI integration | `ai/test_service_and_fallback.py::test_valid_claude_output_is_ready_with_label_and_usage` (fake SDK client) | M-12 (local fake Messages API, no real key) |
| R-53 | AI tools declared | — | DOC (`AI_USAGE.md`) |
| R-64 | Time budget | — | DOC |

### 5.8 Interview answers with test evidence

| ID | Question | Evidence |
|---|---|---|
| R-55 | Stop a student seeing correct answers | R-22 tests |
| R-59 | Separate roles | `api/test_attempt_security.py::test_teacher_rbac`, `::test_student_endpoints_need_a_session_and_the_student_role` |
| R-60 | Lost connection mid-assessment | `api/test_qa_gaps.py::test_a_new_client_session_resumes_the_same_node_and_state`; `api/helpers.py` `play()` re-reads `GET /attempts/{id}` after every step and asserts the same state; `e2e resilience.spec.ts › two tabs…` (reload) |
| R-61 | Student cannot modify the score | R-06, R-26 tests; `api/test_postgres_concurrency.py::test_two_concurrent_answers_lock_the_checkpoint_once` |
| R-62 | Which automated tests first | §2 of this document |
| R-54, R-56, R-57, R-58, R-63 | Architecture answers | DOC (`INTERVIEW.md`) |

### 5.9 Security invariants (SHARED_CONTEXT §9) — each has a test

| # | Invariant | Test |
|---|---|---|
| 1 | No keys, explanations, edges, future nodes while open | R-22 row |
| 2 | Client never sends scores; `extra="forbid"` | `api/test_attempt_security.py::test_answer_shape_errors_are_422_and_do_not_lock` (extra `is_correct`), `::test_advance_is_optimistic_and_only_for_continue_nodes` (extra `minutes`), `api/test_auth.py::test_login_rejects_extra_fields_and_bad_shapes`, `api/test_attempt_security.py::test_the_client_can_never_send_a_score` (see BUG-005) |
| 3 | Answer locked on first submission | `api/test_attempt_security.py::test_a_second_answer_is_409_checkpoint_locked_with_the_current_state`, `api/test_postgres_concurrency.py::test_two_concurrent_answers_lock_the_checkpoint_once`, `data/test_schema.py::test_one_answer_per_question_and_exactly_one_answer_field` |
| 4 | Owned attempts → 404, UUID ids | `api/test_attempt_security.py::test_another_students_attempt_is_404_everywhere`, `::test_malformed_and_unknown_ids_are_404_not_422`, `data/test_schema.py::test_attempt_ids_are_uuids` |
| 5 | One open attempt per (student, mission) | `data/test_schema.py::test_one_open_attempt_per_student_and_mission`, `api/test_mission_flow.py::test_full_run_leaks_nothing_and_the_report_has_the_numbers` (PD-028) |
| 6 | LLM only after grading, never affects score/level/unlocks | R-34 row |
| 7 | `/simulate` never exposes answers | `api/test_simulate.py` (access rules, determinism, recursive leak scan) + `engine/test_simulator_and_diary.py::test_trace_shape_and_no_answer_content` |
| 8 | Secrets in env; JWT in httpOnly cookie | `api/test_auth.py::test_login_sets_an_httponly_lax_cookie_and_returns_the_user`; ESLint `no-restricted-globals` (localStorage/sessionStorage) in `make lint` |
