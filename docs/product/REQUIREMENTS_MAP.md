# REQUIREMENTS MAP — Global AI Missions

> Owner: `product-architect`. Maps every requirement in `docs/agents/SHARED_CONTEXT.md` §1 to where it is satisfied, who owns it and how it is verified.
> QA builds its traceability matrix from this table (`docs/qa/`). Screen names refer to `docs/product/PRODUCT.md` §5.
>
> Verification types: **AUTO** automated test (pytest / Vitest / Playwright) · **GATE** human check at a gate (G0–G4) · **DEMO** visible in the 10-minute demo · **DOC** checked in a document review.

## 1. Flow

| ID | Requirement (§1) | Satisfied by (screen / feature) | Owner(s) | Verification |
|---|---|---|---|---|
| R-01 | Student login | **Check-in**: email + password, JWT in httpOnly cookie, role-based landing | backend-api-engineer (auth), frontend-engineer (screen) | AUTO: API tests login ok/bad credentials/logout/me; E2E logs in as `new@`. DEMO 0:00 |
| R-02 | Student dashboard | **English World**: greeting, missions board, progress snapshot | backend-api-engineer (`/api/world`), frontend-engineer | AUTO: world endpoint test (states per user); E2E sees board. DEMO 0:30 |
| R-03 | Access an assessment | **English World** card → **Start mission / Continue your mission** → **Mission Player** | backend-api-engineer (start/resume), frontend-engineer | AUTO: start creates one attempt, second start resumes it. DEMO 0:45 |
| R-04 | Answer 10 questions | **Mission Player**: exactly 10 checkpoints on every path, one item each | assessment-designer (items), narrative-designer (graph), story-graph-engineer (validator) | AUTO: validator BFS/DFS proves all 1,024 outcome paths visit the same 10 checkpoints in order; E2E answers 10. DEMO |
| R-05 | Submit the answers | **Ending** → **Submit mission** (per-checkpoint answers are locked as they are given; submit grades and closes) | backend-api-engineer, frontend-engineer | AUTO: submit is idempotent; two concurrent submits → one report, no 5xx; submit before an ending is rejected; answer twice → 409; start with a completed, unsubmitted attempt returns it (no new row) and submit then works. DEMO 5:30 |
| R-06 | Score calculation | Server-side deterministic grading at submit (`grading.py`); global % = correct/10, hints do not change score (every checkpoint requires an answer, so nothing is ever unanswered) | backend-api-engineer (grading service), assessment-designer (rules) | AUTO: grading unit tests incl. all-correct, all-wrong, hints used; client cannot send scores (`extra="forbid"`) |
| R-07 | Result per skill | **Mission Report** numbers block: Grammar/Listening/Reading/Vocabulary % and "x of n" | backend-api-engineer, frontend-engineer | AUTO: per-skill % tests (4/2/2/2 denominators); component test renders 4 skills. DEMO |
| R-08 | Attempt record | Attempts + steps persisted; **Mission Report** attempt record line; **Progress** history rows; **Diary** | data-engineer (schema), backend-api-engineer, frontend-engineer | AUTO: steps persisted per transition; report contains attempt metadata; veteran seed has 4 submitted attempts. DEMO 7:00 |
| R-09 | Progress view | **Progress**: profile, Attempt history with per-skill % columns (trend) and level labels, Maya's notes, open attempt; snapshot on English World | backend-api-engineer (`/api/me/progress`), frontend-engineer | AUTO: progress endpoint returns only own attempts; for `veteran@` 4 history rows, a profile based on 3 attempts, ≤ 5 notes newest first; empty state test; E2E sees profile bars and the new label. DEMO with `veteran@` |

## 2. Items

| ID | Requirement (§1) | Satisfied by | Owner(s) | Verification |
|---|---|---|---|---|
| R-10 | Exactly 10 items: 4 multiple choice, 2 fill-in-the-blank, 2 comprehension, 2 vocabulary | `content/missions/the-last-train/items.json` (4 MC = 2 grammar + 2 listening; 2 fill_blank grammar; 2 comprehension reading; 2 vocabulary) | assessment-designer | AUTO: content test counts types and skills; JSON Schema validation. GATE G1. DEMO: type · skill · level tags in the Diary; blueprint table in README |
| R-11 | Each item stores level, skill, prompt, options (when applicable), correct answer | Item fields: id, type, skill, cefr, prompt, stimulus, options, answer_key, explanation, hint | tech-lead (items.schema.json), assessment-designer, data-engineer (persistence) | AUTO: schema test; validator content-integrity check (valid answer key per item) fails on a broken fixture; seed loads items into DB. GATE G0 |
| R-12 | Suggested skills: Grammar, Vocabulary, Reading, Listening, Speaking | Four scored skills; `speaking` in the data model and shown on the report as "not measured in this mission yet" (roadmap) | assessment-designer, data-engineer, frontend-engineer | AUTO: skill enum includes speaking; report shows speaking note. DOC: DECISIONS.md explains roadmap |
| R-13 | Items are leveled (CEFR) | A1×2 → A2×3 → B1×3 → B2×2 rising with the story clock | assessment-designer | AUTO: content test on CEFR spread and order. GATE G1 |
| R-14 | AI English Coach (suggested) | **Maya**: planner during the mission + LLM feedback after it + coach memory | story-graph-engineer (planner), ai-coach-engineer (LLM, memory), narrative-designer (lines) | AUTO: planner tests (hint/rescue thresholds, one rescue max); coach tests (valid output, fallback). DEMO |

## 3. Result screen

| ID | Requirement (§1) | Satisfied by | Owner(s) | Verification |
|---|---|---|---|---|
| R-15 | Global score in % | **Mission Report** block 1: the first thing on screen, as the report heading `A2 · The Last Train — 70%` | backend-api-engineer, frontend-engineer | AUTO: report DTO contains global %; component test; E2E asserts it is visible. DEMO |
| R-16 | Result per skill | Same block (see R-07) | backend-api-engineer, frontend-engineer | AUTO. DEMO |
| R-17 | Number of correct and incorrect answers | Same block: Correct / Incorrect | backend-api-engineer, frontend-engineer | AUTO: counts sum to 10. DEMO |
| R-18 | Suggested level or interpretation | Same block: suggested level + one-line rule explanation; block 2: Maya's interpretation | assessment-designer (rules, templates), backend-api-engineer (leveling), ai-coach-engineer (interpretation) | AUTO: leveling unit tests for every band and the evidence cap step-down; fallback interpretation always present. DEMO |
| R-19 | Attempt record on the result screen | Same block, under the plain heading "Attempt record": attempt number, submitted at, ending, story-minutes, rescue, hints; Diary (block 4) | backend-api-engineer, frontend-engineer | AUTO: report contains attempt record; E2E sees the "Result per skill" and "Attempt record" headings; Diary reconstructs the path by parent pointers. DEMO |
| R-20 | Example format "A2 English Assessment – 82%. Grammar 80%…" | Report label `A2 · The Last Train — 70%` + per-skill line | backend-api-engineer, frontend-engineer | AUTO: label format test. DEMO |

## 4. Technical

| ID | Requirement (§1) | Satisfied by | Owner(s) | Verification |
|---|---|---|---|---|
| R-21 | Separation of frontend, backend and persistence | `frontend/` (React SPA), `backend/` (FastAPI, layered: api → services → engine/repositories), PostgreSQL | tech-lead | GATE G0 (repo structure); DOC DECISIONS.md architecture |
| R-22 | Questions and answers not hardcoded in the frontend | Content lives in `content/` and the DB; the client receives only StateView; answer keys, explanations, edges and future nodes never leave the server while an attempt is open | backend-api-engineer, frontend-engineer, qa-engineer | AUTO: response-scan tests assert no forbidden keys on every open-attempt endpoint; build scan that the SPA bundle contains no item text/keys. DEMO 8:30 (DevTools) |
| R-23 | A database | PostgreSQL 16 via SQLAlchemy + Alembic; idempotent seed | data-engineer | AUTO: migration up on empty DB in CI; seed idempotency test |
| R-24 | API to fetch the assessment and submit results | `/api/world`, `/api/missions/{id}/attempts`, `/api/attempts/{id}` (+ advance, answer, submit, report), `/api/me/progress` | tech-lead (contract), backend-api-engineer | AUTO: API tests per endpoint; OpenAPI exported. GATE G0 |
| R-25 | Basic authentication | JWT HS256, 60 min, httpOnly SameSite=Lax cookie; argon2 password hashes; roles student/teacher/admin | backend-api-engineer | AUTO: unauthenticated → 401 UNAUTHENTICATED; login rate limit → 429; wrong role → 403; foreign attempt → 404 |
| R-26 | Error handling and validation | Pydantic request models with `extra="forbid"`; unified error model; every screen has error states (PRODUCT.md §5); 409 on second answer handled silently by the player | tech-lead (error model), backend-api-engineer, frontend-engineer | AUTO: validation tests (extra fields, bad option id, both/neither of option_id and text, whitespace-only text → 422 and the checkpoint stays answerable, wrong node); frontend error-state tests. GATE G2 |
| R-27 | Organized, readable, maintainable code | Conventions in `docs/contracts/`; ruff; typed TS; ownership by folder | tech-lead, all engineers | GATE G4 (the human can explain every module); CI lint |
| R-28 | Responsive design | Mobile-first specs (360 px → desktop) for every screen and checkpoint type | ux-ui-designer (UI_SPEC), frontend-engineer | GATE G3 responsive pass; E2E at mobile viewport (Playwright) |
| R-29 | Git | Small conventional commits telling the story | the human, all agents | DOC: git log review at G4 |
| R-30 | README with clear run instructions (Spanish) | `README.md`: one command, demo credentials, env vars | delivery-engineer | GATE G4: clean clone run in < 5 min |
| R-31 | Justified stack | DECISIONS.md "stack and reasons" | tech-lead | DOC |

## 5. AI

| ID | Requirement (§1) | Satisfied by | Owner(s) | Verification |
|---|---|---|---|---|
| R-32 | Brief educational feedback after the assessment (simulated or real LLM) | **Mission Report** blocks 2 and 3: Maya's interpretation, strength/challenge, recommendation, next mission; Claude adapter or deterministic mock; fallback within 8 s | ai-coach-engineer | AUTO: mock provider output valid; invalid/timeout → fallback, report still renders; strength/challenge echo deterministic values; `next_mission_id` ∈ candidates. DEMO |
| R-33 | Explanation of how an LLM would power personalized feedback, accompaniment, reminders and learning assistance | `docs/ai/AI_ARCHITECTURE.md` (Spanish, one paragraph per use) + a two-line pointer in the DECISIONS.md AI point; in-product evidence: coach memory → next greeting (accompaniment), Maya's pick (personalization), Maya's notes | ai-coach-engineer (doc and evidence), tech-lead (pointer) | DOC; DEMO 7:00 with `veteran@` |
| R-34 | Project invariant (SHARED_CONTEXT §9.6), supports brief §7/§8: AI never influences score, level or unlocks | Coach runs after the grading commit; unlock rules are deterministic (catalog) | ai-coach-engineer, backend-api-engineer | AUTO: submit with a provider returning garbage yields identical score/level |

## 6. Technical decisions document (max. 2 pages) — DECISIONS.md, Spanish

| ID | Required point | Owner | Verification |
|---|---|---|---|
| R-35 | Stack and reasons | tech-lead | DOC (G4) |
| R-36 | Architecture | tech-lead | DOC |
| R-37 | Data model | tech-lead (with data-engineer input) | DOC |
| R-38 | How correct answers are protected | tech-lead (with backend-api-engineer) | DOC + AUTO evidence (R-22) |
| R-39 | Scaling 100 → 50,000–100,000 students | tech-lead | DOC |
| R-40 | Student / teacher / admin roles | tech-lead | DOC + AUTO evidence (R-25; teacher of another class → 404; admin fixture → 200) |
| R-41 | Integrating AI without coupling to one provider | tech-lead (with ai-coach-engineer) | DOC + code (`CoachProvider` port) |
| R-42 | What changes with three months to productize | tech-lead (product input: PRODUCT.md §8 out-of-scope list is the natural backlog) | DOC |
| R-43 | Max 2 pages | tech-lead | DOC (page count at G4) |

## 7. Deliverables and conditions

| ID | Requirement (§1) | Satisfied by | Owner | Verification |
|---|---|---|---|---|
| R-44 | Git repository | This repo | the human | G4 |
| R-45 | Runs locally (demo URL preferred) | Docker Compose one command; deploy of the same image right after G2 (Should) | delivery-engineer | G4 clean clone; URL smoke test, or README states why there is none |
| R-46 | README | See R-30 | delivery-engineer | G4 |
| R-47 | Decisions document | See R-35–R-43 | tech-lead | G4 |
| R-48 | Test credentials | Seeded demo users (`new@`, `veteran@`, `teacher@`, password `LastTrain2026!`) listed in README and on Check-in in demo mode | data-engineer (seed, `app/core/demo.py`), backend-api-engineer (`GET /api/config`), tech-lead (contract), delivery-engineer (README), frontend-engineer (demo panel) | AUTO: seed test; `/api/config` hides accounts when DEMO_MODE=false. DEMO 0:00 |
| R-49 | Optional: Docker | Dockerfile + docker-compose | delivery-engineer | G4 |
| R-50 | Optional: automated tests | pytest, Vitest, 1–2 Playwright specs, CI | qa-engineer + each owner | CI green |
| R-51 | Optional: deploy | Delivery decision | delivery-engineer | smoke test |
| R-52 | Optional: real AI integration | Anthropic adapter via `COACH_PROVIDER=anthropic` | ai-coach-engineer | manual run with key; provider/model/prompt_version stored |
| R-53 | Declare AI tools used and the candidate's personal work | `docs/AI_USAGE.md` (Spanish), built from `docs/AI_USAGE_LOG.md` | delivery-engineer, the human | G4: truthful review by the human |
| R-64 | Time: at most one day, estimated 6–8 h, no overnight work (brief §10) | 8-hour plan in `docs/agents/README.md` with a walking-skeleton gate at 2:30; AI_USAGE.md states the real hours | the human | DOC: plan review at G0; AI_USAGE.md at G4 |

## 8. Interview questions — where the answer is demonstrable

| ID | Question | Answer lives in | Owner |
|---|---|---|---|
| R-54 | 100 → 100,000 students | DECISIONS.md scaling; stateless API (the login rate limit is per-process in the MVP and moves to a shared store at scale), content cached per version, the coach seam becomes a queue | tech-lead |
| R-55 | Stop a student from seeing correct answers in the browser | StateView + server-only transition model; R-22 tests; DevTools demo | tech-lead, backend-api-engineer |
| R-56 | Where progress lives; how attempts are modeled | attempts + steps (the Diary), profile from submitted attempts; Progress screen | data-engineer, backend-api-engineer |
| R-57 | Adding Pre-A1…C1 without redesign | CEFR reference table, per-item `cefr`, per-mission `cefr_range`; the level bands are per-mission code today (`leveling.py`) and move to mission-version data next; C1 needs another mission | assessment-designer, tech-lead |
| R-58 | Replacing Claude with another model | `CoachProvider` port + adapters; prompts versioned | ai-coach-engineer |
| R-59 | Separating student / teacher / admin | roles + RBAC dependencies; teachers scoped to their classes (404 otherwise), admin bypass; Teacher view (stretch); 404 on foreign attempts | backend-api-engineer |
| R-60 | Connection lost mid-assessment | Server-held attempt state; resume on reload (also on the Ending, before submit); idempotent retries; demo 8:30 | backend-api-engineer, frontend-engineer |
| R-61 | Student cannot modify their score | Server-only grading; `extra="forbid"`; answers locked | backend-api-engineer, qa-engineer |
| R-62 | Which automated tests first | Score integrity, answer-key leakage, ownership, locking, resume, AI fallback, engine invariants | qa-engineer |
| R-63 | Priorities for production in three months | DECISIONS.md; PRODUCT.md §8 as backlog | tech-lead |
| — | All ten written up | `docs/INTERVIEW.md` (Spanish) | tech-lead |

## 9. Selection criteria — where the product shows them

| Criterion | Evidence in the product |
|---|---|
| Engineering judgment | Out-of-scope list (PRODUCT.md §8); explicit trade-offs (SHARED_CONTEXT §9) |
| Ability to build product | Two journeys, core loop visible on screen, acceptance criteria with all states |
| Security | R-22, R-25, R-34, R-38, R-55, R-61 |
| Architectural clarity | R-21, search-problem engine, provider port |
| Maintainability | Content as data, versioned missions, tests |
| Imagination (unique, immersive) | *The Last Train*, story clock, Maya, Diary, three dignified endings |
| Scalability vision | R-39, R-54, catalog and CEFR as data |
