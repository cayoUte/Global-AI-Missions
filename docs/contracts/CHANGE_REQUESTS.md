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
- Requested by: story-graph-engineer · Date: 2026-09-24 · Status: open
- File(s): `backend/app/engine/maya.py` (`decide`); SHARED_CONTEXT §5 wording.
- Change: read literally, §5 makes Maya rescue at the last moment even when the train is already lost, wasting her single rescue. Proposed rule: RESCUE only if the normal detour would lose the train even with every remaining answer correct (using the same heuristic `h` as the hint rule) **and** the rescue edge keeps the train catchable.
- Why: a rescue that cannot save the train is narratively empty and spends the one rescue.
- Impact: engine only (already implemented; a one-line revert in `decide` if rejected). The narrative-designer noted the related case of a rescue at 0 minutes left.
- Decision (tech-lead): pending
- Note: re-logged by the orchestrator from the story-graph-engineer's report; the original entry was lost to a concurrent write.

### CR-003 — Single fill-blank normalization function
- Requested by: story-graph-engineer · Date: 2026-09-24 · Status: open
- File(s): `backend/app/engine` (`normalize_answer`), backend grading, seed.
- Change: `app.engine.normalize_answer` (lowercase, trim, collapse spaces, strip final punctuation, straighten curly apostrophes) is the only fill-blank normalization; the backend and the seed import it instead of writing their own. ASSESSMENT_SPEC must confirm the same rule.
- Why: one source of truth for grading and for storing accepted answers.
- Impact: backend-api-engineer, data-engineer, assessment-designer.
- Decision (tech-lead): pending
- Note: re-logged by the orchestrator from the story-graph-engineer's report; the original entry was lost to a concurrent write.
