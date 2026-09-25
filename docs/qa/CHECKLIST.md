# QA CHECKLIST — Global AI Missions

> Owner: `qa-engineer` (sections 1–3); the `delivery-engineer` completes section 4. Internal working note (English).
> Environment of every result below, unless stated: Linux container, headless Chromium 141 (Playwright 1.56.1, build 1194), PostgreSQL 16 on 127.0.0.1:5433, the SPA built and served by FastAPI (single origin), throwaway `*_e2e` databases freshly migrated and seeded. The demo database `gam` was never written. Date: 2026-09-25.
> Result legend: **PASS** · **FAIL** (bug id) · **PARTIAL** (what ran, what did not) · **NOT RUN** (why it cannot be verified here — a human must do it).

## 1. Live checks (run for real in headless Chromium)

| # | Check | How it was run | Result |
|---|---|---|---|
| L-1 | **Maya's rescue** shows in the UI and ends in `made_it_with_maya` | Answer sequence found with the engine (all 1,024 paths enumerated): miss q01–q04, then miss q07 (a cheapest path that triggers RESCUE at c07). Automated in `e2e resilience.spec.ts › Maya's rescue…`, played with the keyboard as `veteran@` | **PASS** — the scene "Maya's shortcut" and Maya's bubble tagged "Maya's shortcut" appear after the q07 miss; the Ending heading is **Made It Together** (`made_it_with_maya`); the report reads `Pre-A1 · The Last Train — 50%` and Attempt record "Maya's shortcut: Used". Engine note: a rescue does not guarantee this ending — later misses can still end on the night bus (by design, CR-002). |
| L-2 | **No English voice** on the device: the listening checkpoint stays usable | (a) Headless Chromium as it is: `speechSynthesis` exists but `getVoices()` returns 0 voices (measured). (b) `speechSynthesis` deleted with an init script (`e2e resilience.spec.ts › two tabs, a reload and no speech…`) | **PASS** both — after ~1.5 s the Listen button is replaced by "Audio isn't available on this device" and the announcement as text; choices stay enabled; the answer is sent with the keyboard and the story continues. (Documented trade-off PD-014: in this fallback the transcript is visible before answering.) |
| L-3 | **Same mission in two tabs** | Same cookie, tab A and tab B on the same run (`e2e resilience.spec.ts › two tabs…`) | **PASS** — B's stale Continue → `409 NODE_OUT_OF_SEQUENCE` → B silently shows A's checkpoint; A answers, then B answers the same checkpoint → `409 CHECKPOINT_LOCKED` → B silently shows A's consequence scene (same location as the server state); no error text, no crash, one answer stored. API race version on PostgreSQL: `test_two_concurrent_answers_lock_the_checkpoint_once` — one 200, one 409, one row (see BUG-002 for a rare stale `details.state`). |
| L-4 | **Keyboard-only play** | `e2e mission.spec.ts › new student…` uses only Tab, typing, digits 1–4, Enter and L (no mouse clicks) — check-in, Start mission, 10 checkpoints, Submit mission, See your progress — at 1280×800 and 360×740 | **PASS** — every control was reachable with Tab; Continue and the choice group receive focus on each new node; Enter confirms. |
| L-5 | **Reduced motion** | `reducedMotion: 'reduce'` context: `e2e resilience.spec.ts › reduced motion…` + a frame-by-frame sample of the scene column across a Continue (both preferences) | **PASS with a note (BUG-003, S3)** — tokens drop to quick 0 ms / scene 120 ms / consequence 120 ms; CSS animations are stopped (0.01 ms); the y-slide is gone (0 moving frames vs 17 without the preference); the flow works. The content fade still lasts ~250 ms instead of the UI_SPEC's 120 ms (PRODUCT §5.3 "fade only" is met). |
| L-6 | **Report footer with `COACH_PROVIDER=anthropic`** and no key / an invalid key | Three API servers, each over its own fresh database. No real Anthropic call and no real key: the invalid-key and valid cases point the official SDK at a **local fake Messages API** (`ANTHROPIC_BASE_URL=http://127.0.0.1:880x`) that logged every request | **PASS** — (a) no key: submit `200` in ~0.1 s, `feedback_source = {fallback, "Maya's notebook"}`, footer "About this feedback: Written by Maya from her notebook (offline feedback)." (b) invalid key (fake server answers `401 authentication_error`; it logged one request with the fake key): submit `200` in ~1 s, same fallback and footer. (c) control, fake server returns a valid structured reply: `{ready, "Claude"}`, footer "Written by Maya using Claude." — the UI reads the label from the server. Grades identical in all three. Also automated through submit with a fake SDK client: `test_a_broken_ai_provider_never_breaks_submit_or_changes_the_grade[invalid_key, timeout, malformed_json, unknown_mission]`. |

## 2. Manual checks

| # | Check | Status | Notes |
|---|---|---|---|
| M-01 | 360 px: every screen, no horizontal scroll | **PASS after the BUG-001 fix** (was FAIL) | Measured (`scrollWidth − clientWidth`): Check-in 0, English World 0, Mission Player 0, Mission Report 0, **Progress +25 px** (the Attempt history table). Automated: `e2e mission.spec.ts` [mobile-360]. |
| M-02 | 768 px | **PASS after the BUG-001 fix** (was FAIL) | Check-in 0, World 0, Player 0, Report 0, **Progress +217 px**: at `md` all 11 history columns appear and the table spills out of its card. |
| M-03 | 1440 px (and 1024, 1280) | **PASS** | All screens 0 px overflow; screenshots reviewed. |
| M-04 | Reduced motion | **PASS (note BUG-003)** | See L-5. Should also be eyeballed once on a real OS setting (macOS "Reduce motion"). |
| M-05 | Keyboard-only run | **PASS** | See L-4. Visible focus ring: check by eye at G3. |
| M-06 | Screen-reader spot check | **PARTIAL** | ARIA tree reviewed with Playwright's aria snapshot: the player has an `h1` "The Last Train — {location}", a polite `log` region that announces location, clock, scene and Maya's line, a `radiogroup` named by the prompt with `radio` options, a disabled Confirm until a choice; Progress has a captioned table. Finding: the Listen button's accessible name is "Listen L" on desktop (BUG-004). A real screen reader (VoiceOver / NVDA) **cannot be run here** — do one pass at G3. |
| M-07 | Speech on Chrome, Safari, Firefox | **NOT RUN** | This container has no speech voices (0 voices in Chromium) and no Safari/Firefox. The fallback path is verified (L-2). A human must press **Listen** on Chrome (desktop), Safari (macOS/iOS) and Firefox before the demo and note which voice speaks. |
| M-08 | Fresh clone following the README (< 5 min) | **NOT RUN** | No `README.md` exists yet (delivery phase). What is proven: `make e2e` builds the SPA, migrates and seeds an empty database and serves the app from scratch. Delivery must run the clean-clone check (§4). |
| M-09 | Two tabs | **PASS** | See L-3. |
| M-10 | No English voice | **PASS** | See L-2. |
| M-11 | Maya's rescue | **PASS** | See L-1. |
| M-12 | Report footer per provider | **PASS** | See L-6. |
| M-13 | 10-minute demo rehearsal (G3) | **PENDING (human)** | Follow `DEMO_SCRIPT.md` with a stopwatch on `make reset` data; the scripted answer sequence was dry-run through the API on a fresh seed (90%, B2, Made It, Night Radio as Maya's pick). |
| M-14 | DevTools: no answer keys in Network during a run | **PASS (automated)** | Recursive scans in `test_full_run_leaks_nothing_and_the_report_has_the_numbers`, `test_the_real_mission_runs_end_to_end_without_leaks`, `test_walking_skeleton_on_postgres`, `test_conflict_bodies_of_an_open_attempt_leak_nothing`; SPA bundle scan. Show it live in the demo (8:30). |

## 3. Bugs

Severity: **S1** blocker (data/security/integrity or the demo cannot run) · **S2** a Must requirement fails, no reasonable workaround for the user · **S3** minor, cosmetic or a rare race with self-recovery.

| ID | Sev | Summary | Owner | Status |
|---|---|---|---|---|
| BUG-001 | **S2** | Progress: the Attempt history table overflows the page at 360 px (+25 px) and 768 px (+217 px) — horizontal page scroll, the last columns are cut off; violates PRODUCT §5 ("usable at 360 px without horizontal scroll") and R-28 | frontend-engineer | **Fixed** (orchestrator, 2026-09-25: `overflow-x-auto` on the HistoryTable card; `test.fail` removed and the E2E passes at 360 and 768 px). Original note: fix proposed below, verified by injecting the same CSS: overflow 0 px at 360, 414, 768, 1024, 1280. E2E `Progress has no horizontal page scroll at 360 and 768 px` is marked `test.fail` and will flag the fix (remove the mark then). |
| BUG-002 | S3 | Concurrent Confirm race: the losing request's `409 CHECKPOINT_LOCKED` may carry a **stale** `details.state` (the checkpoint again, built from the attempt read before the winner committed). Integrity is intact (one answer, one 409); the client resyncs to the checkpoint and self-heals on its next action. Seen twice in 31 races on PostgreSQL (once on the first run of the new test, once in a 30-race loop) | backend-api-engineer | **Fixed** (orchestrator, 2026-09-25: `conflict()` refreshes the attempt; `FakeSession.refresh` no-op; the race test now requires `details.state == winner state`). Original note: fix proposed below; with it, 0 stale in 30 races. `test_two_concurrent_answers_lock_the_checkpoint_once` accepts either state until then (comment in the test says how to tighten it). |
| BUG-003 | S3 | Reduced motion: the scene content fade keeps its 250 ms duration (UI_SPEC §3.5/§7: 120 ms, opacity only); the slide is correctly removed | frontend-engineer | **Fixed** (orchestrator, 2026-09-25: `SceneScreen` uses `useReducedMotion()` → `MOTION.reduced` = 120 ms). Re-measure by eye at G3. |
| BUG-004 | S3 | Listen button accessible name is "Listen L" on desktop (the `<kbd>L</kbd>` inside the button is not `aria-hidden`, unlike the Enter hint in `ActionBar`) | frontend-engineer | **Fixed** (orchestrator, 2026-09-25: `aria-hidden="true"` on the `kbd`). Original note: add `aria-hidden="true"` to that `kbd` in `Announcement.tsx`; `aria-keyshortcuts="L"` already announces the shortcut. |
| BUG-005 | S3 | Contract wording: api-contract §9.C says a client-sent score → 422, but `submit` has no body and **ignores** one (`200`, server grade; `test_the_client_can_never_send_a_score` pins this). The invariant "the client never sends scores" holds either way | tech-lead | **Fixed (doc)** — CR-010, commit `ccd978a`: api-contract §5.11 and §9.C now say submit takes no body and ignores one. Original note: recommend adding "submit takes no body; any body is ignored" to §5.11 instead of changing code. |

### Proposed fix — BUG-001 (`frontend/src/features/progress/ProgressPage.tsx`, `HistoryTable`)

```diff
-    <div className="rounded-card bg-ink-800">
+    <div className="overflow-x-auto rounded-card bg-ink-800">
       <table className="w-full border-collapse">
```

(Optional follow-up for a nicer tablet layout: show Date/Mission/Ending/Correct/Incorrect from `lg:` instead of `md:`.)

### Proposed fix — BUG-002 (`backend/app/services/attempts.py`, `conflict`)

```diff
 def conflict(session: Session, code: ErrorCode, message: str, attempt: Any) -> DomainError:
     """Every 409 on an attempt endpoint carries the server's truth in details.state (F-02)."""
+    session.refresh(attempt)  # a concurrent request may have just committed a move
     view = build_state_view(session, attempt)
```

plus `def refresh(self, obj) -> None: pass` on `FakeSession` in `backend/tests/fakes.py` (the fake store is always current).

## 4. Delivery checklist (delivery-engineer, 2026-09-25)

Status legend: **DONE** (verified here, how is stated) · **PENDING (human)** (cannot be done or verified from this container) · **NOT DONE**. Environment: the Linux build container, Docker 29.3 / Compose v5.1, PostgreSQL 16 on 127.0.0.1:5433.

### 4.1 Brief deliverables

| Deliverable (brief) | Status | Evidence |
|---|---|---|
| Git repository, small conventional commits | **DONE** | Branch `claude/peaceful-archimedes-uijpxu`; `git ls-files` has no `.env`, `node_modules/`, `dist/`, `.venv/`, `test-results/`, `playwright-report/`; a regex scan of tracked files for Anthropic/Groq/xAI key patterns found nothing. Tag `v1.0.0`: **PENDING (human)**, after the final review. |
| Runs locally | **DONE** | Fresh `git clone` of the branch → `cp .env.example .env` → `docker compose up -d --build` (only a separate project name and DB host port, so the demo database was not touched; plus this container's proxy CA as a build secret) → `/api/health` ok, SPA 200, `new@` login 200 after 29 s with warm base images and build cache. A cold machine also pulls the Node and Python base images and downloads the npm/PyPI packages: not timed here. Non-Docker path: `make dev-backend` and `make dev-frontend` start and answer `/api/health` (working tree, existing database). |
| Demo URL | **PENDING (human)** | `render.yaml` Blueprint (free web service + free PostgreSQL 16) is ready; no Render account here. The README has the placeholder `[URL de Render — pendiente]` and the step-by-step deploy. |
| README with install and run instructions | **DONE** | `README.md` (Spanish): evaluator section, credentials, 3-command Docker quick start, local development, tests, AI configuration, stack with reasons, architecture, Render deploy, env vars, structure, known limitations. Every Docker command was run as written; the Render steps were not (no account). |
| Technical decisions document | **DONE** (tech-lead) | `docs/DECISIONS.md`, linked from the README's evaluator section. |
| Test credentials | **DONE** | README table + the Check-in "Demo accounts" panel (`DEMO_MODE=true`); `new@`, `veteran@`, `teacher@` logins returned 200 against the container. |
| Optional: Docker | **DONE** | Multi-stage `Dockerfile` (Node 22 → uv/Python 3.12 slim, non-root uid 10001, 348 MB image), `docker/entrypoint.sh` (URL scheme rewrite, `alembic upgrade head`, idempotent seed, uvicorn on `$PORT`), compose `api` service with a healthcheck. Verified: `postgresql://` and `postgres://` URLs are rewritten; a missing `DATABASE_URL` stops with a clear message; empty database → migrated, seeded (3 users, Leo's 4 attempts) and healthy. |
| Optional: automated tests | **DONE** | `uv run pytest` → 322 passed, 0 skipped (PostgreSQL tests ran); `npm test` → 45 passed; `make e2e` → 10 passed, 1 skipped (mobile-only test in the desktop project); `make lint` pieces all clean (ruff check/format, ESLint, tsc, Prettier). |
| Optional: CI | **DONE, not run** | `.github/workflows/ci.yml`: backend (ruff + pytest on a postgres:16 service; fails if the DB tests skip), frontend (lint, typecheck, format, Vitest, build), E2E (Playwright + the built-SPA answer scan), Docker (build + boot with a `postgresql://` URL + login). YAML parsed and `actionlint` clean; GitHub Actions itself cannot run here — check the first run on GitHub. The Docker job's smoke test was reproduced locally against a throwaway database. |
| Optional: deploy | **PENDING (human)** | See "Demo URL". |
| Optional: real AI integration | **PARTIAL** | Anthropic and OpenAI-compatible (Groq, xAI) adapters with fake-client tests; the mock is the default and the fallback. No live LLM call was possible here (network policy): run `cd backend && uv run python scripts/coach_smoke.py` with a real key. |
| AI usage declaration (brief §10) | **DRAFT, PENDING (human)** | `docs/AI_USAGE.md` built from `AI_USAGE_LOG.md`, the git log, DECISIONS_LOG and CHANGE_REQUESTS; section 3 is marked `[CONFIRMA O AJUSTA]` for the candidate. |

### 4.2 Before handing in

- [x] Fresh clone following the README (Docker path) — M-08. 2026-09-25 · delivery-engineer. See 4.1 "Runs locally" for the deviations (project name, DB port, proxy CA).
- [x] `make lint` green (ruff, ESLint, tsc, Prettier). 2026-09-25 · delivery-engineer.
- [x] Tests green: backend 322 passed (PostgreSQL tests not skipped), Vitest 45 passed. 2026-09-25 · orchestrator, after the stretch items.
- [x] `make e2e` green: 10 passed, 1 skipped. 2026-09-25 · orchestrator, after the stretch items.
- [x] README (Spanish) states the run commands, demo credentials, env vars, how to run the tests, the 10-item blueprint and the known limitations (speech, retake, per-process rate limit, teacher view read-only, `/simulate` demo-only). 2026-09-25 · delivery-engineer.
- [x] `.env` not committed; `.env.example` has working local defaults; no build or test outputs in git. 2026-09-25 · delivery-engineer.
- [x] Docker: `docker compose up -d --build` works (see 4.1). 2026-09-25 · delivery-engineer.
- [ ] Deploy on Render from `render.yaml` and put the URL in the README — **human**.
- [ ] Live LLM check with `coach_smoke.py` (and, if used, the provider's env vars on Render) — **human**.
- [ ] CI green on GitHub after the push — **human**.
- [ ] Demo data fresh right before the demo: `make reset` (or `docker compose down -v && docker compose up -d --build`); on Render, the reset steps in the README — **human / orchestrator**.
- [ ] Speech checked on the demo browser (M-07); the text fallback is plan B — **human**.
- [x] No open S1/S2 bugs in §3 (BUG-001 fixed; BUG-005 resolved in the contract by CR-010).
- [ ] `docs/AI_USAGE.md` reviewed and approved by the candidate (section 3, hours) — **human**.
- [ ] Demo rehearsal with a stopwatch (M-13), ≤ 10 min — **human**.
- [ ] Tag `v1.0.0` after the final review — **human**.
