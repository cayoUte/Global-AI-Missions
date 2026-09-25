# Change requests — Global AI Missions

> Owner: `tech-lead` (triage). Anyone may append a request. Contracts froze at **G0 (2026-09-24)**.
> Frozen: `docs/contracts/{items,mission,catalog}.schema.json`, `api-contract.md`, `conventions.md`, and folder ownership in `docs/agents/SHARED_CONTEXT.md` §11.

## How to request a change

1. Append an entry to **Log** using the template (next free id). Do not edit the frozen file yourself.
2. Tell the human. The tech-lead triages at the next gate (or immediately if it blocks someone).
3. The decision, its impact and the owners who must act are recorded in the entry. Only then does the owner of the file change it.

Status: `open` · `accepted` · `rejected` · `done` (implemented everywhere it impacts).

```md
### CR-0XX — <short title>
- Requested by: <agent> · Date: <YYYY-MM-DD> · Status: open
- File(s): <frozen file(s) and section>
- Change: <exactly what should change>
- Why: <the problem it solves>
- Impact: <agents / files / tests affected; data migration? contract version?>
- Decision (tech-lead): <accepted / rejected + reason> · Owners to act: <…>
```

---

## G0 freeze notes (read these before building)

Decisions taken while freezing that go **beyond or refine** SHARED_CONTEXT. F-01 and the `Departing now` label in F-06 were accepted by the human on 2026-09-24 and applied to SHARED_CONTEXT §8, the backend brief and PRODUCT §5.3. They are part of the frozen contract; each lists who is affected.

| # | Decision | Where | Affects |
|---|---|---|---|
| F-01 | The answer response is `{ maya_line, state }`: the draft's `outcome` field is **dropped**. It is `is_correct` under another name, and no screen needs it (Maya's reaction and the consequence scene carry the story). `outcome` (`understood`/`missed`) appears only in the Report's Diary and `/simulate`. | api-contract §5.10, §9 | backend-api, frontend, qa |
| F-02 | Error precedence on `answer`: 422 shape → 404 → 409 `CHECKPOINT_LOCKED` → 409 `ATTEMPT_NOT_IN_PROGRESS` → 409 `NODE_OUT_OF_SEQUENCE` → 422 item rules → row lock and re-check. Every 409 on an attempt endpoint carries `details.state` (a StateView), so the client resyncs without an extra GET. | api-contract §2, §5.10 | backend-api, frontend, qa |
| F-03 | Malformed UUIDs in paths → 404 (not 422). `GET /report` before submission → 409 `MISSION_NOT_FINISHED` with `details.state`. Start on a non-playable, locked or unknown mission → 404. 405 keeps its status with code `NOT_FOUND`. | api-contract §1, §2, §5 | backend-api, qa |
| F-04 | World card state precedence: an open attempt wins over "completed"; `latest_result` is still filled. `is_maya_pick` comes from the most recent submitted attempt's feedback (deterministic fallback value if no row). | api-contract §5.6 | backend-api, frontend |
| F-05 | Profile (PD-009) is **pooled**: per skill, Σcorrect / Σtotal over the last 3 submitted attempts. All percentages are integers, rounded half up. | api-contract §4 | backend-api, data, qa |
| F-06 | The server builds every display string that depends on rules: the clock `label` (including a new `Departing now` at 0 minutes), the report `label`, the level `reason`. The client renders them verbatim. | api-contract §4, §7 | backend-api, frontend, product (copy "Departing now") |
| F-07 | Session cookie name `gam_session`; new optional env var **`COOKIE_SECURE`** (default `false`, set `true` on any https deploy). **`JWT_SECRET` must be ≥ 32 characters** (the app refuses to boot otherwise). **`DATABASE_URL` uses the psycopg 3 driver**: `postgresql+psycopg://user:password@host:5432/db`. | api-contract §3, `backend/app/core/config.py` | **delivery-engineer** (`.env.example`, compose, deploy), backend-api |
| F-08 | OpenAPI and Swagger live under `/api`: `/api/openapi.json`, `/api/docs` (so the SPA can own every other path). | `backend/app/main.py` | backend-api, frontend (`gen:api`), delivery |
| F-09 | `items.json`: `stimulus` is `null` or `{kind: audio, speaker, audio_script, rate, text: null}` or `{kind: dialogue\|sign\|message\|notice\|timetable, speaker, text}`. A `fill_blank` prompt contains exactly one `___` gap. Plain text only (`\n` for line breaks). Option ids match `^[a-z0-9]{1,8}$`. | items.schema.json | assessment-designer, story-graph (fixture), frontend, ux-ui |
| F-10 | `mission.json` additions to the §12 draft: checkpoint `maya = {intro, reaction_ok, reaction_fail, reaction_rescue?}` (Maya's checkpoint line goes in `maya.intro`, not in `scene.lines`); other nodes may have `maya = {line}` and endings **must** (closing line); endings carry `ending = {key, title, priority, condition}`; optional node `diary` line (past tense, for the Diary); scene `variants` are checked in order, **the first matching flag replaces the lines** and may override `location`, `backdrop`, `maya_line`, `diary` (put `train_departed` first); `train_departed` is reserved and not declared in `flags`; `rescue: true` only on `incorrect` edges. | mission.schema.json | narrative-designer, story-graph (fixture, engine), data |
| F-11 | StateView never contains `skill`, `cefr`, `hint` or `explanation`; the listening `rate` replaces any need for CEFR on the client. Type · skill · CEFR tags appear only in the Report (PD-029). | api-contract §6, §9 | backend-api, frontend, qa |
| F-12 | Frontend tooling: Tailwind CSS **v4** (tokens and theme in `src/styles/tokens.css` as CSS variables plus an `@theme` block — there is no `tailwind.config.js`/`theme.extend`); **TypeScript pinned to 5.9** (openapi-typescript 7 does not support TS 6); **ESLint + Prettier** replace the oxlint that the current Vite template ships. | frontend/ | ux-ui-designer, frontend |
| F-13 | Backend tooling: **uv** (`backend/pyproject.toml`, `uv.lock`); `requires-python >= 3.12` (the Docker image should use 3.12; the skeleton was verified locally on 3.13). `jsonschema` is a runtime dependency so the seed can validate content too. | backend/ | delivery-engineer (Dockerfile, CI, Makefile), data |
| F-14 | Content validation command: `cd backend && uv run python scripts/validate_content.py` (schema + cheap cross-references; the graph and integrity checks stay in the engine validator). Also run by `pytest` (`tests/contracts`). | backend/scripts | delivery-engineer (add a `make validate-content` target), all content owners |

## Conflicts found at G0 (and how they were resolved)

| # | Conflict | Resolution |
|---|---|---|
| C-01 | SHARED_CONTEXT §8 draft answer response includes `outcome`, while §9 forbids `is_correct` and PRODUCT §5.3 never reveals correctness. | F-01: `outcome` dropped from the answer response. |
| C-02 | ux-ui-designer brief asks for a "Tailwind theme extension (theme.extend) snippet"; the skeleton uses Tailwind v4. | F-12: the same tokens go in an `@theme` block in `tokens.css`. |
| C-03 | SHARED_CONTEXT §12 example puts Maya's checkpoint line inside `scene.lines`; the narrative brief requires an intro line per checkpoint and the StateView needs one Maya line. | F-10: `maya.intro` (required). Maya may still speak in `scene.lines` as part of the scene. |
| C-04 | SHARED_CONTEXT §10 lists the environment variables without the DB driver, cookie security or secret length. | F-07. |
| C-05 | tech-lead brief says "the first commit"; the human instructed agents not to commit at G0. | The human's instruction wins: all changes are left in the working tree. |
| C-06 | PRODUCT §5.2 does not say which state wins when a mission has both a submitted attempt and an open one. | F-04: the open attempt wins. |
| C-07 | Stack says Python 3.12; the development machine has 3.13. | F-13: `>= 3.12`, Docker pins 3.12, ruff targets py312. |

---

## Log

### CR-001 — Test database URL default must match the compose port (5433)
- Requested by: delivery-engineer · Date: 2026-09-24 · Status: done
- File(s): `backend/tests/conftest.py` (default `DATABASE_URL`)
- Change: default to `postgresql+psycopg://gam:gam@localhost:5433/gam_test` (today `...@localhost:5432/gam_test`).
- Why: `docker-compose.yml` publishes PostgreSQL on host port **5433** so it never collides with a PostgreSQL installed on the machine (the dev machine already runs one on 5432). The compose init script creates the `gam_test` database, so DB-backed tests work against compose with no extra setup. Env vars set in the shell still override the default (CI sets its own).
- Impact: one line in conftest; data-engineer and backend-api tests that need the DB; no contract change. Nothing breaks today (no test touches the DB yet).
- Decision: accepted by the human on 2026-09-24; conftest default changed to port 5433.

### CR-002 — Maya rescues only when the rescue can still save the train
- Requested by: story-graph-engineer · Date: 2026-09-24 · Status: done
- File(s): `backend/app/engine/maya.py` (`decide`); SHARED_CONTEXT §5 wording.
- Change: read literally, §5 makes Maya rescue at the last moment even when the train is already lost, wasting her single rescue. Proposed rule: RESCUE only if the normal detour would lose the train even with every remaining answer correct (using the same heuristic `h` as the hint rule) **and** the rescue edge keeps the train catchable.
- Why: a rescue that cannot save the train is narratively empty and spends the one rescue.
- Impact: engine only (already implemented; a one-line revert in `decide` if rejected). The narrative-designer noted the related case of a rescue at 0 minutes left.
- Decision: accepted by the human on 2026-09-25. Already implemented in the engine; SHARED_CONTEXT §5 updated.
- Note: re-logged by the orchestrator from the story-graph-engineer's report; the original entry was lost to a concurrent write.

### CR-003 — Single fill-blank normalization function
- Requested by: story-graph-engineer · Date: 2026-09-24 · Status: accepted
- File(s): `backend/app/engine` (`normalize_answer`), backend grading, seed.
- Change: `app.engine.normalize_answer` (lowercase, trim, collapse spaces, strip final punctuation, straighten curly apostrophes) is the only fill-blank normalization; the backend and the seed import it instead of writing their own. ASSESSMENT_SPEC must confirm the same rule.
- Why: one source of truth for grading and for storing accepted answers.
- Impact: backend-api-engineer, data-engineer, assessment-designer.
- Decision: accepted by the human on 2026-09-25. ASSESSMENT_SPEC already mirrors app.engine.normalize_answer; backend grading and the seed must import it (status becomes done once both do).
- Note: re-logged by the orchestrator from the story-graph-engineer's report; the original entry was lost to a concurrent write.

### CR-004 — Coach provider seam used by submit phase 2 (interface note, no contract change)
- Requested by: backend-api-engineer · Date: 2026-09-25 · Status: open
- File(s): none frozen. Code: `backend/app/services/coach.py` (backend-api) ↔ `backend/app/ai/` (ai-coach-engineer).
- Change: `services/coach.run_coach()` looks up `app.ai.get_coach_provider()`; if it is missing or returns `None` / a provider named `mock`, the deterministic feedback is used (status `fallback`). A provider is any object with `provider`, `model`, `prompt_version`, `label` attributes and `generate(request: CoachRequest) -> dict` returning the SHARED_CONTEXT §6 JSON. The service runs it in a worker thread with the 8-second budget, validates it (strength/challenge must equal the deterministic values, `next_mission_id` must be a candidate, texts non-empty ≤ 800 chars) and falls back on any error. It stores `provider_label` inside `coach_feedback.content` so the report can show it without a column.
- Why: the report must always render and the LLM must never touch score, level or unlocks; the ai-coach-engineer can plug in without editing services.
- Impact: ai-coach-engineer (implement `get_coach_provider` and the adapters; may move the deterministic text into `app/ai/mock_provider.py` and have `services/coach.deterministic_feedback` delegate to it). CR-003 is done on the backend side: services import `app.engine.normalize_answer`.
- Decision (tech-lead): pending · Owners to act: ai-coach-engineer

### CR-005 — Use 127.0.0.1 instead of localhost in DATABASE_URL (local runs hang on Windows)
- Requested by: data-engineer · Date: 2026-09-25 · Status: done
- File(s): `.env.example` (and each developer's `.env`), `backend/tests/conftest.py` default `DATABASE_URL`.
- Change: `DATABASE_URL=postgresql+psycopg://gam:gam@127.0.0.1:5433/gam` (and `...@127.0.0.1:5433/gam_test` in the test default).
- Why: on this machine (Windows + Docker Desktop) `localhost` resolves to IPv6 `::1` first and the connection to the published port stalls **forever** when no `connect_timeout` is set; `127.0.0.1` connects instantly. This hung `alembic`, `python -m seed` and `pytest` (including another agent's run). Mitigated on the data side already: `app/repositories/db.get_engine()` and `alembic/env.py` pass `connect_timeout=5`, so `localhost` now fails over to IPv4 after ~5 s instead of hanging, and the DB tests rewrite `@localhost:` to `@127.0.0.1:`. The fix above removes the 5 s delay per new connection.
- Impact: delivery-engineer (`.env.example`, README), tech-lead (conftest default). No contract change.
- Decision: accepted by the human on 2026-09-25. DATABASE_URL uses 127.0.0.1 in .env.example, the local .env and the tests default.

### CR-006 — Data model notes beyond the brief's column list (informational, no new table)
- Requested by: data-engineer · Date: 2026-09-25 · Status: open
- File(s): none frozen. `backend/app/models/`, `backend/alembic/versions/0001_initial.py`, `docs/data/DATA_MODEL.md`.
- Change: (1) `attempt_steps.state_after JSONB` = the engine state on arrival (`{minutes_left, flags, rescued, maya_mood}`), needed so the Diary resolves scene variants per step (`engine.StepRecord.flags`); (2) every attempt has a root step (seq 1, `on_event='start'`, no parent, no from_node) inserted by `create_attempt`, enforced by a CHECK; (3) `UNIQUE(mission_id, content_hash)` on `mission_versions`, and the active version = the most recently `published_at` (re-seeding an older hash republishes it); (4) extra CHECKs on `attempts` (a submitted row must carry its totals and level; a finished row its ending), `users.email = lower(email)` and a partial unique "one primary accepted answer per question".
- Why: completes the persisted search Node (state, parent, action, path cost) and makes versioning and the invariants enforceable in the database.
- Impact: backend-api (already codes against it). No API contract change.
- Decision (tech-lead): pending · Owners to act: none (informational)

### CR-007 — Coach seam follow-ups (CR-004 implemented on the app.ai side)
- Requested by: ai-coach-engineer · Date: 2026-09-25 · Status: done
- File(s): none frozen. `backend/app/core/config.py` (`coach_provider`), `backend/app/services/coach.py`, `backend/app/services/feedback.py`, `backend/app/models/coach.py` (backend-api / data-engineer).
- Done under CR-004 (for the record): `app.ai.get_coach_provider()` exists and returns an adapter with `provider`/`model`/`prompt_version`/`label` and `generate(CoachRequest) -> dict`. `services/coach.py` was edited only inside the seam: the §7 template dicts are now re-exported from `app/ai/templates.py`, `FALLBACK_PROMPT_VERSION` is the mock's (`deterministic-v2`), and `deterministic_feedback()` delegates to the AI mock (templates + coach memory: "Nice to meet you, Ana." / "You usually do well with vocabulary. You still hesitate when someone speaks quickly."), keeping the old assembly as a safety net if the mock ever raises. Memory notes keep the old prefix "Strong in X; Y needs practice", so the veteran's seeded notes are read back without re-seeding.
- Change requested: (1) widen `Settings.coach_provider` from `Literal["mock", "anthropic"]` to `str` (app.ai.factory already maps unknown values to the mock with a warning), so a new adapter needs only a file in `app/ai` plus `COACH_PROVIDER=<name>`; (2) optional: let `run_coach` keep the adapter's token usage (`input_tokens`, `output_tokens`) in `CoachResult.extra` and store it (a JSONB `usage` column or inside `content`); today usage is only logged by `app.ai` (`coach.usage …`); (3) optional: add the student's own text for missed fill-blank items to `CoachRequest.missed` as `student_answer` (≤ 80 chars): the port already accepts it and the prompt delimits it as data.
- Why: (1) "switching providers needs no change outside backend/app/ai" (ai brief DoD); (2) cost per feedback measured per row instead of from logs; (3) richer feedback without new privacy exposure.
- Impact: backend-api (config, coach.py, feedback.py), data-engineer only for (2) (migration). No API contract change. Tests: none break; `tests/ai` already cover the adapter side.
- Decision: (1) accepted by the human on 2026-09-25 and done: `Settings.coach_provider` is now `str` with default `"mock"`; test `test_real_settings_accept_any_provider_name_and_boot_with_the_mock` covers an unknown name booting with the mock. (2) and (3) are optional and not scheduled for the MVP (roadmap).

### CR-008 — Anonymous `GET /api/auth/me` 401 shows as a browser console error (informational)
- Requested by: frontend-engineer · Date: 2026-09-25 · Status: done
- File(s): `docs/contracts/api-contract.md` §5.5 (no change proposed unless the tech-lead wants a clean console).
- Change: none required. Option if a completely clean DevTools console matters for the demo: `GET /api/auth/me` returns `200 null` (or `204`) for an anonymous visitor instead of `401 UNAUTHENTICATED`; the frontend already treats both as "not checked in".
- Why: the route guard and the Check-in redirect ("already authenticated → home") must probe the httpOnly session, which the client cannot read. Chrome logs every 4xx fetch as "Failed to load resource … 401" even though no JavaScript error occurs. This is the only console error seen in the full browser run (both demo students).
- Impact: backend-api (one endpoint) + one test; frontend needs no change either way (`features/auth/session.ts` maps 401 → null).
- Decision: accepted by the human on 2026-09-25 and done. `GET /api/auth/me` without a cookie → `200 null` (`app.api.deps.optional_user`); a present but bad, tampered, forged, expired or orphaned cookie is still `401 UNAUTHENTICATED` (`tests/api/test_auth.py::test_tampered_forged_or_expired_cookie_is_401`, `test_a_deleted_user_session_is_401`). api-contract §3 and §5.5 updated, openapi.json and `frontend/src/api/schema.d.ts` regenerated; `useMe` treats `null` and 401 as "no session" (`features/auth/session.test.tsx`). Every other endpoint keeps 401 for anonymous calls.

### CR-009 — Settings and .env.example for the OpenAI-compatible coach adapter (Groq, xAI)
- Requested by: ai-coach-engineer · Date: 2026-09-25 · Status: done
- File(s): `backend/app/core/config.py` (the only env reader), `.env.example`. New files inside `app/ai` need no CR: `backend/app/ai/openai_compatible_provider.py`, `backend/scripts/coach_smoke.py`, `backend/tests/ai/test_openai_compatible.py`.
- Change: four optional settings, `openai_compat_base_url: str | None`, `openai_compat_api_key: SecretStr | None`, `openai_compat_model: str | None`, `openai_compat_label: str | None` (env `OPENAI_COMPAT_*`); `.env.example` gets a commented block with Groq and xAI examples, `COACH_PROVIDER=mock` stays the default. `app.ai.factory.PROVIDERS` gains `openai_compatible`; a missing base URL, key or model, or a plain-http remote URL → the mock (logged).
- Why: PD-033, the live proof that a new provider is one file in `app/ai` plus env vars (CR-007 made `COACH_PROVIDER` a free string).
- Impact: delivery-engineer (`.env.example` block, README may point to it); no API contract change, no migration, no frontend change (the report already shows `feedback_source.provider_label` from the server). Stored feedback rows carry `provider=openai_compatible`, the model and `prompt_version=maya_feedback_v1`.
- Decision: accepted by the human on 2026-09-25 and done.
