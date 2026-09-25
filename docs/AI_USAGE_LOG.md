# AI usage log — Global AI Missions

> Owner: `tech-lead`. Running log, newest at the bottom. Every agent appends an entry when it delivers; **the human fills in or corrects the "Human review" line** — an agent never claims a review that did not happen.
> Source for `docs/AI_USAGE.md` (Spanish, delivery-engineer), which must be truthful (brief §10: declare the AI tools used and what the candidate did personally).
> Tooling for every entry unless stated otherwise: Claude Code with the subagents defined in `.claude/agents/`, orchestrated by the human.

Entry template:

```md
### <n>. <YYYY-MM-DD> · <agent> — <task>
- Files: <created / changed>
- What the agent did: <1–3 lines>
- Verification: <commands run and results, or "not run" and why>
- Human review: <what the human read, decided, rewrote — or "pending">
```

---

### 1. 2026-09-24 · `product-architect` — product spec and catalog

- Files: `docs/product/PRODUCT.md`, `docs/product/REQUIREMENTS_MAP.md`, `docs/product/MAYA.md`, `docs/product/DECISIONS_LOG.md` (PD-001 … PD-030), `content/catalog.json`.
- What the agent did: turned the fixed concept into journeys, the core loop per screen, screen acceptance criteria with all states (§5), MVP scope and out-of-scope list, microcopy, Maya's character bible, the requirements map against the brief and the five-mission catalog with deterministic unlock rules.
- Verification: `content/catalog.json` validates against `docs/contracts/catalog.schema.json` (checked by the tech-lead at G0, see entry 3).
- Human review: decisions marked "Decided (human, 2026-09-24)" in DECISIONS_LOG were taken by the human (PD-008, PD-009, PD-011, PD-014, PD-018, PD-023, PD-025, PD-027; PD-001 delegated). _Human: add what you read and anything you rewrote._

### 2. 2026-09-24 · human-directed audit and spec revision

- Files: `docs/agents/SHARED_CONTEXT.md`, `docs/agents/README.md`, all twelve briefs in `.claude/agents/`, and the matching entries in `docs/product/` (DECISIONS_LOG, PRODUCT).
- What changed (directed by the human, edits made with an AI assistant — _human: confirm the tool and who wrote what_):
  - Mission Report order: **numbers first** (label `A2 · The Last Train — 70%`, global %, per skill, correct/incorrect, level with reason, attempt record), then Maya's interpretation, next mission, Diary, missed checkpoints (PD-001).
  - **No skip button**: every checkpoint needs a decision, so correct + incorrect always equals 10 and "unanswered = incorrect" disappeared (PD-011).
  - **8-hour budget** instead of 10 (brief §10): shorter timeboxes, a walking-skeleton gate G1 at 2:30 on a fixture mission, polish and `/simulate` moved to stretch, calibration as one informational run (PD-027).
  - Contract changes in SHARED_CONTEXT §6–§12: `GET /api/config` and the demo accounts panel; the open attempt includes a finished but unsubmitted run (PD-028); AnswerRequest validation before any lock; `feedback_source` on the Report; six World card states plus `is_maya_pick`; Progress fields; the coach runs after the grading commit (two-phase submit); `stimulus.rate`; content-integrity rules; the catalog format; demo first names; `docs/ai/AI_ARCHITECTURE.md` added to the ai-coach-engineer's outputs.
- Verification: document review only (no code existed yet).
- Human review: the human decided every change listed above. _Human: add anything else you changed by hand._

### 3. 2026-09-24 · `tech-lead` — G0: application skeleton and frozen contracts

- Files:
  - Backend: `backend/pyproject.toml`, `backend/uv.lock`, `backend/app/main.py`, `backend/app/core/{config,errors}.py`, `backend/app/api/error_handlers.py`, `backend/app/api/routers/health.py`, empty packages for `engine, models, repositories, services, ai, schemas, api/routers`, `backend/scripts/validate_content.py`, `backend/tests/{conftest.py,test_health.py,contracts/test_content_contracts.py}`, placeholder folders (`alembic/`, `seed/`, `tests/{engine,api,services,ai}/`).
  - Frontend: Vite + React 19 + TypeScript 5.9 + Tailwind v4 app in `frontend/` (ESLint + Prettier configs, Vitest setup, feature folders, `src/styles/tokens.css` placeholder, one smoke test).
  - Contracts: `docs/contracts/{items,mission,catalog}.schema.json`, `api-contract.md`, `conventions.md`, `CHANGE_REQUESTS.md` (G0 freeze notes F-01…F-14 and conflicts C-01…C-07); this log.
- What the agent did: scaffolded both apps as in SHARED_CONTEXT §11, froze the three content schemas and the API contract (every §8 endpoint, StateView, Report, World card, Progress, error model, idempotency, forbidden fields), and wrote the conventions.
- Verification (run by the agent): backend `uv sync`, `uv run ruff check .` and `ruff format --check .` clean, `uv run pytest` 32 passed (health, error envelope, schema positive/negative cases, catalog valid); `uvicorn app.main:app` booted and `GET /api/health` returned `{"status":"ok"}`, an unknown route returned the 404 envelope, and a 5-character `JWT_SECRET` was refused at boot; `scripts/validate_content.py` passed on `content/`. Frontend `npm run lint`, `typecheck`, `test` (1 passed), `build` and `format:check` all clean. Not verified: anything needing PostgreSQL (docker-compose belongs to the delivery-engineer), Python 3.12 specifically (the machine has 3.13).
- Human review: pending (G0).

### 4. 2026-09-24 · `narrative-designer` — The Last Train, Step A (item-independent story)

- Files: `content/missions/the-last-train/SCRIPT.md` (Step A draft), `docs/design/BACKDROPS.md` (created). `mission.json` **not** written: `items.json` did not exist yet when Step A finished, so Step B (checkpoints, consequences, per-checkpoint Maya lines, variants, rescue edges) is pending.
- What the agent did: wrote the premise (intro node, under 80 words), the location/backdrop sequence of the night, three flags (`wrong_ticket`, `wrong_platform`, `befriended_guard`) and what they change, the minutes model (correct 1 / incorrect 3 / rescue 1 on checkpoints 8–10; all-correct = 10 story-minutes; `train_departed` first reachable after checkpoint 7), the night-bus Plan B, the three endings with titles and closing lines, and Maya's generic mood lines (3 per mood). Proposed 11 backdrop keys; `docs/design/UI_SPEC.md` did not exist, so the keys must be reconciled with the ux-ui-designer.
- Verification: not run (no `mission.json` yet; the engine validator CLI does not exist yet). Minutes arithmetic checked by hand in SCRIPT.md §4.
- Human review: pending.

### 4. 2026-09-24 · `delivery-engineer` — phase 0: local infrastructure

- Files: created `.gitignore`, `docker-compose.yml`, `docker/db-init/01-create-test-db.sql`, `.env.example`, `Makefile`; appended CR-001 to `docs/contracts/CHANGE_REQUESTS.md`; created a local, git-ignored `.env` from `.env.example`.
- What the agent did: PostgreSQL 16 compose service with a `pg_isready` healthcheck, published on host port **5433** (the dev machine already runs a native PostgreSQL on 5432) and a one-time init script that creates `gam_test` for pytest; `.env.example` with every §10 + F-07 variable and working local defaults (psycopg 3 URL, 55-char dev-only `JWT_SECRET`, `COOKIE_SECURE=false`, `COACH_PROVIDER=mock`, `DEMO_MODE=true`, Anthropic vars commented out because an empty value is not "unset" for pydantic-settings); a POSIX-sh Makefile (`help env install up down reset migrate seed test lint gen-api validate-content`, with `migrate`/`seed` printing "not implemented yet" until `backend/alembic.ini` / `backend/seed/__main__.py` exist). Hosting chosen for the post-G2 deploy: **Render** — one Docker web service built from the repo's Dockerfile plus Render managed PostgreSQL 16 (same image as local, HTTPS out of the box, no infra code; caveats: free web instances sleep, the free database expires, Render's `postgresql://` URL must be rewritten to `postgresql+psycopg://`, and `COOKIE_SECURE=true` there).
- Verification: `docker compose config` valid (db on 5433, healthcheck, init mount). Recipes run by hand because GNU make is not installed on the machine: backend `uv run pytest` 32 passed, `ruff check` and `ruff format --check` clean, `scripts/validate_content.py` "content is valid"; OpenAPI export one-liner produced a valid 3.1 document (written to a scratch path, not to `docs/contracts/`) and `openapi-typescript` generated types from it; frontend `npm test` 1 passed, `lint`, `typecheck`, `format:check` clean. `git status --short --ignored` shows `.env`, `backend/.venv/`, `frontend/node_modules/` and caches ignored, `.env.example` tracked. **Not verified:** the container itself — Docker Desktop 4.45.0 crashed on start (`initializing Inference manager … remove …\AppData\Local\Docker\run\dockerInference: The file cannot be accessed by the system`), so `docker compose up -d --wait db` was never run.
- Human review: pending.

### 6. 2026-09-24 · `story-graph-engineer` — fixture mission and story graph engine

- Files: `content/missions/_fixture/{items,mission}.json` (replaces `.gitkeep`); `backend/app/engine/{__init__,graph,state,transition,heuristic,maya,validator,simulator,diary,cli}.py`, `backend/app/engine/README.md`; `backend/tests/engine/{conftest,helpers,test_transition,test_heuristic_and_maya,test_validator,test_simulator_and_diary}.py` (replaces `.gitkeep`); `docs/contracts/CHANGE_REQUESTS.md` (CR-001, CR-002).
- What the agent did: wrote the fixture (10 checkpoints in the §4 order and distribution, braided ok/fail consequences, rescue edges from checkpoint 7, flags `lost_ticket` and `wrong_platform`, Plan-B variants, three endings; 38 nodes, 55 edges, generated once by a throwaway script that is not committed) and the pure-Python engine: MissionGraph, State, ACTIONS/RESULT/goal test with grading and normalization, h by Dijkstra on the reversed graph, Maya's policy (hint at slack < 3, rescue with a one-step lookahead, see CR-001), mood FSM and line selection, the BFS/Kahn/DFS validator with content integrity, the seeded simulated student and calibration, the Diary from parent pointers, the clock label, a CLI and 70 engine tests.
- Verification (run by the agent, in `backend/`): `uv run python scripts/validate_content.py` → content is valid (fixture included; the script already covered every mission folder, so it was not changed); `uv run python -m app.engine.cli validate` → `_fixture: ok`, 1,024 paths, 10–30 story-minutes, endings by path made_it 386 / made_it_with_maya 246 / night_bus 392; `uv run pytest` → 102 passed, 1 skipped (the real-mission validator test, skipped until `the-last-train/mission.json` exists); `uv run ruff check .` and `ruff format --check .` clean. Calibration over 1,000 runs per profile is in the engine README. Not verified: the real mission (not written yet).
- Human review: pending. Known deviation: the engine is about 850 physical lines after `ruff format`, above the brief's "aim for under 400"; the validator (content integrity plus the path DFS) accounts for about 200 of them.

### 7. 2026-09-24 · `assessment-designer` — The Last Train items and assessment spec

- Files: created `content/missions/the-last-train/items.json` and `docs/assessment/ASSESSMENT_SPEC.md`.
- What the agent did: wrote the 10 original items in the §4 blueprint. The levels are A1 q01–q02, A2 q03–q05, B1 q06–q08 and B2 q09–q10. There are 4 multiple choice (grammar q01 and q09, listening q02 and q07), 2 fill_blank (grammar q05 and q06), 2 comprehension (reading q03 and q10) and 2 vocabulary (q04 and q08). Each item has a stimulus, diagnostic distractors, an explanation and a strategy hint. The spec contains: the blueprint with language points; the grading and integer round-half-up scoring; the level rule, with the evidence cap and the exact level-reason sentence template; 9 worked examples, including an A1 slip and a lucky B2 guess; the fill-blank normalization, written to match the engine's existing `normalize_answer`; the deterministic strength/challenge tie-break rule; the interpretation templates (can-do statement per level, strong/developing/focus lines per skill, and a recommendation per challenge skill); the item-review checklist (10/10 pass); and the story facts the items fix, for the narrative-designer.
- Verification: `cd backend && uv run python scripts/validate_content.py` gave "content is valid" (the-last-train `items.json` ok; `mission.json` skipped, not written yet). `uv run python -m app.engine.cli validate --mission the-last-train` stopped with `FileNotFoundError` for `mission.json`, because the engine validator needs the mission graph. A scratch self-check script confirmed: the blueprint counts and CEFR order; unique option ids and texts; every key among its options; each fill_blank prompt with exactly one `___`; the accepted answers already normalized (`normalize_answer(a) == a`) and de-duplicated; the audio word counts (24 and 34) and rates; the reading word counts (45 and 82); and all 9 worked examples, including their reason sentences and strength/challenge values.
- Human review: pending.

### 4. 2026-09-24 · `ux-ui-designer` — visual language, tokens, Maya avatar, screen specs

- Files: created `docs/design/UI_SPEC.md`, `frontend/src/styles/backdrops.css`, `frontend/src/assets/maya/{curious,encouraging,worried,proud}.svg`, `frontend/src/assets/backdrops/{arches,platform,skyline,bus,carriage}.svg`; replaced the placeholder `frontend/src/styles/tokens.css` (Tailwind v4 `@theme static`, default palette reset so no green/red utilities exist).
- What the agent did: defined "London after dark" (ink/navy, sodium-amber departure board, Maya's warm light; Atkinson Hyperlegible, Fraunces, Share Tech Mono), tokens with numerically checked WCAG contrast (lowest text pair fog-400/ink-700 6.22:1), component inventory, mobile-first specs with all states for every PRODUCT §5 screen, one renderer per item type and stimulus kind (incl. PD-013/PD-014 listening), motion (Must/Should) and keyboard/ARIA rules, microcopy, a proposed backdrop-key list for the narrative-designer, and an original four-mood SVG avatar for Maya. SVGs generated by small Node scripts and checked visually with headless Chrome.
- Verification: in `frontend/`: `npm run build` OK (CSS 26.6 kB, 6.2 kB gzip), `npm run lint` clean, `npm run format:check` clean, `npm test` 1 passed. Contrast computed with the WCAG relative-luminance formula (table in UI_SPEC §3.2). No React components written.
- Human review: pending.
