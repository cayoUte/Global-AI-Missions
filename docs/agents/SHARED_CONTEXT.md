# SHARED CONTEXT — Global AI Missions

> Every agent reads this file completely before starting. It is the single source of truth for the project.
> If your brief and this file disagree, this file wins: log the conflict in `docs/contracts/CHANGE_REQUESTS.md` instead of improvising.

---

## 1. The assignment

Technical assessment for a Full Stack Developer role at **Global AI**, an EdTech platform for learning English from Pre-A1 (Pre-Beginner) to C1 (CEFR). The official brief asks for a "Mini Global AI Assessment": a working prototype of an English assessment module that could later become part of a scalable product.

**Budget: 8 hours in total** (brief §10: at most one day, an estimated 6–8 hours, no overnight work, not a full platform), one human orchestrating several AI agents. When time runs short, cut scope, never the §1 flow. The human must be able to explain and modify every line in the technical interview. Readable, explainable code beats clever code.

### What the evaluators require (nothing in this list is optional)

- **Flow:** student login · student dashboard · access an assessment · answer 10 questions · submit the answers · score calculation · result per skill · attempt record · progress view.
- **Items:** exactly 10 — 4 multiple choice, 2 fill-in-the-blank, 2 comprehension, 2 vocabulary. Each item stores at least level, skill, prompt, options (when applicable) and correct answer. Suggested skills: Grammar, Vocabulary, Reading, Listening, Speaking. An AI English Coach is suggested.
- **Result screen:** global score in %, result per skill, number of correct and incorrect answers, suggested level or interpretation, attempt record. Their example: "A2 English Assessment – 82%. Grammar 80%, Vocabulary 100%, Reading 75%, Listening 70%."
- **Technical:** reasonable separation of frontend, backend and persistence; questions and answers not hardcoded in the frontend; a database; an API to fetch the assessment and submit results; basic authentication; error handling and validation; organized, readable, maintainable code; responsive design; Git; a README with clear run instructions; a justified stack.
- **AI:** brief educational feedback after the assessment (simulated or real LLM), plus an explanation of how Claude or another LLM would later power personalized feedback, student accompaniment, reminders and learning assistance.
- **Technical decisions document (max. 2 pages):** stack and reasons · architecture · data model · how correct answers are protected · scaling from 100 to 50,000–100,000 students · student/teacher/admin roles · integrating AI without coupling the platform to a single provider · what would change with three months to turn the prototype into a product.
- **Deliverables:** Git repository · runs locally (a demo URL is preferred) · README · decisions document · test credentials · optional: Docker, automated tests, deploy, real AI integration.
- **Conditions:** at most one day, an estimated 6–8 hours; they judge quality of reasoning, architecture, execution and imagination, not completeness. Declare which AI tools were used and which parts the candidate did personally.
- **Interview questions to be ready for:** (1) 100 → 100,000 students: what changes and why; (2) how to stop a student from seeing correct answers in the browser; (3) where progress lives and how attempts are modeled; (4) adding Pre-A1, A1, A2, B1, B2 and C1 without redesigning; (5) what code changes if Claude is replaced by another model; (6) separating student, teacher and admin permissions; (7) what happens if the student loses connection mid-assessment; (8) how to guarantee a student cannot modify their score from the browser; (9) which automated tests first and why; (10) what to prioritize for production in three months.
- **Selection criteria:** engineering judgment, ability to build product, security, architectural clarity, maintainability, imagination (a unique, immersive experience) and scalability vision. They are *not* looking for the fanciest stack or the flashiest UI.

---

## 2. The concept (fixed)

**Global AI Missions** — *"Don't build an assessment system with game elements. Build a narrative experience that, internally, is an assessment."*

- The student never sees "Question 3/10 · Listening · Choose the correct answer". They see a situation and make a decision inside it. Underneath, every decision is a leveled, skill-tagged assessment item.
- The story always continues, right or wrong. Performance is recorded silently. Fear of failure is designed out.
- Consequences are narrative and linguistic ("you misunderstood the guard" → the next scene lets you notice or repair it). No XP, coins, hearts, streaks, confetti or disappointed mascots.
- **Maya**, the AI companion, is the heart of the product. She knows the student through their history and evolves with them.

Core loop: `EXPERIENCE → DECISIONS → ASSESSMENT → PROFILE → AI FEEDBACK → NEXT MISSION → EXPERIENCE`

---

## 3. The MVP mission: THE LAST TRAIN

- *LONDON — 21:47. You have 18 minutes before the last train leaves.* The student and Maya must reach the platform by 22:05.
- Exactly 10 checkpoints, each one an assessment item embedded in a scene.
- The **story clock** replaces "question N of 10". It is not a real-time timer: it only advances by the story-minutes of the path taken.
- Three endings, all warm and dignified: `made_it`, `made_it_with_maya` (Maya's rescue was needed) and `night_bus` (the train is gone; Plan B together). The ending never changes the score.
- MVP = one mission, one setting, one AI companion, 10 items, one report, one profile, one simulated next mission, polished scene transitions. That single mission must feel extraordinary.

---

## 4. Assessment invariants (must hold on every possible path)

| `type` | Count | Skills |
|---|---|---|
| `multiple_choice` | 4 | 2 `grammar` + 2 `listening` |
| `fill_blank` | 2 | `grammar` |
| `comprehension` | 2 | `reading` |
| `vocabulary` | 2 | `vocabulary` |

- Scored skills: grammar (4 items), listening (2), reading (2), vocabulary (2). `speaking` exists in the data model but is not scored in the MVP (roadmap).
- CEFR spread, rising with the story clock: A1 ×2 → A2 ×3 → B1 ×3 → B2 ×2.
- Every item stores: id, type, skill, cefr, prompt, stimulus, options (choice types), answer key, explanation and a strategic hint.
- **Scoring** (deterministic, server-side only): global % = correct / 10 · per-skill % = correct / items of that skill · correct and incorrect counts (they always add up to 10: every checkpoint needs an answer to continue and there is no skip) · hints never change the score (they are recorded).
- **Suggested level** (deterministic and explainable):
  1. Base level from the global %: 0–29 Pre-A1 · 30–49 A1 · 50–69 A2 · 70–84 B1 · 85–100 B2.
  2. Evidence cap: level L ∈ {A1, A2, B1, B2} requires at least ⌈n_L / 2⌉ correct answers among the n_L items tagged L; otherwise step down one level and check again. Pre-A1 needs no evidence.
  3. This mission can suggest at most B2; C1 needs another mission.
- Report label format: `A2 · The Last Train — 70%`.

---

## 5. The mission as a search problem (story graph)

| Search concept | In The Last Train |
|---|---|
| Agent (human) | Perceives the scene (text, audio, Maya) and acts by choosing |
| Agent (Maya) | Perceives the student's state and acts: quiet, hint or rescue |
| State `s` | `(node_id, minutes_left, flags, rescued, maya_mood)` |
| `ACTIONS(s)` | The options of the checkpoint at `s` (or CONTINUE on narrative nodes) |
| `RESULT(s, a)` | The transition model: the only function that knows answer keys; it runs only on the server |
| Goal test | `node.kind == "ending"` (several goal states) |
| Path cost | Story-minutes: correct edge ≈ 1, incorrect edge (a detour) ≈ 3 |
| Node (state, parent, action, path_cost) | Each persisted attempt step; following the parent pointers back from the ending **is the Diary** |

**Braided graph (critical invariant):**

```
[C1] ──correct──▶ C1_ok ───┐
  └──incorrect──▶ C1_fail ─┴──▶ [C2] ──▶ … ──▶ [C10] ──▶ ending chosen by state
```

- Every path visits the same 10 checkpoints in the same order. Branches between checkpoints are narrative only and rejoin before the next checkpoint.
- Flags set by branches (2–3 at most, e.g. `lost_ticket`) change later scene text through variants.
- The engine sets the automatic flag `train_departed` when `minutes_left < 0` (with the default costs this can first happen right after checkpoint 7). Every node reachable in that state has a Plan-B variant (the night bus), so the remaining checkpoints stay meaningful.
- 2¹⁰ = 1,024 outcome paths from roughly 30–35 authored nodes. No cycles; every reachable state reaches an ending.

**Maya = planner + narrator:**

- `h(n)` = exact minimum story-minutes from node `n` to an ending using non-rescue edges, precomputed once per mission version with a backward uniform-cost search (Dijkstra on the reversed graph). An exact cost-to-go is admissible and consistent.
- `slack = minutes_left − h(node)`.
- At a checkpoint: `slack < 3` → **HINT** (a strategy, never the answer), otherwise **QUIET**.
- After an incorrect answer: if the train has not departed, the normal detour would lose the train even with every remaining answer correct (`minutes_left − cost − h(detour) < 0`), the rescue edge would still keep it catchable (`minutes_left − cost − h(rescue) ≥ 0`), a rescue edge exists and no rescue was used yet → **RESCUE** (Maya takes the cheaper rescue edge; at most once per mission). A rescue that cannot save the train is never spent (CR-002). Fill-blank normalization lives only in `app.engine.normalize_answer` (CR-003).
- Maya's mood is a small finite-state machine (`curious`, `encouraging`, `worried`, `proud`) driven by outcomes and slack; it selects her expression and her generic mood lines.
- The planner decides WHAT Maya does during the mission. The LLM decides HOW she speaks after the mission. The LLM never controls the flow and never sees answer keys of an open attempt.
- Minimax / alpha-beta are deliberately not used: Maya and the student cooperate; nobody is an adversary.

**Simulated student agent:** a policy `P(correct | skill, cefr)` per profile (`A1`, `A2`, `B1`, `B2`, `A2_weak_listening`). MVP uses: content validation in tests and realistic seed history for the veteran demo user. Calibration (endings over 1,000 runs) is one informational run, not a gate; targets for `made_it` + `made_it_with_maya`: B1 ≥ 85% · A2 50–80% · A1 ≤ 30%. The demo replay is stretch.

---

## 6. AI companion contract (LLM)

- Runs once per attempt, inside `submit` but **after the grading transaction has committed** (never while holding a lock or a transaction). Synchronous with an 8-second budget; any failure falls back to a deterministic mock (status `fallback`). If no feedback row exists yet, the report renders the deterministic mock. The report always renders. At scale this exact seam becomes a queue.
- Input (built by the backend): first name, suggested level, global %, per-skill scores, the deterministic strength and challenge, missed items with explanations (the attempt is already closed), a path summary (ending, rescue, hints), the coach memory (sessions count, last notes) and candidate next missions from the catalog.
- Output: strict JSON validated with Pydantic:

```json
{
  "summary": "You can communicate. You understand written English very well…",
  "strength": "vocabulary",
  "challenge": "listening",
  "recommendation": "…",
  "next_mission_id": "night-radio",
  "memory_note": "Hesitates when people speak quickly; strong with signs and menus.",
  "next_greeting": "Welcome back. Last time fast speech was tricky. Tonight, listen for the numbers."
}
```

- The Report carries `feedback_source: { status: "ready" | "fallback", provider_label }`; the active adapter supplies `provider_label` (e.g. "Claude"), so the UI never hard-codes a provider name.
- `strength` and `challenge` must echo the deterministic values; `next_mission_id` must be one of the candidates. Anything else → fallback values.
- A `CoachProvider` port with the adapters `anthropic` and `mock`, selected by `COACH_PROVIDER`. Prompts are versioned files; provider, model and prompt_version are stored with every feedback.
- English adapted to the learner's level (short sentences for A1–A2). No personal data beyond the first name.

---

## 7. Product surface (MVP)

- Screens: **Check-in** (login) · **English World** (the dashboard: missions board, Maya's greeting from memory, progress snapshot) · **Mission Player** · **Ending** · **Mission Report** (with the Diary) · **Progress**. Stretch goals, only when everything else is green: a read-only **Teacher view** and a **Simulated replay**.
- English World card states (one per card): `available | in_progress | waiting_to_submit | completed | locked | in_preparation`, plus at most one `is_maya_pick` (the latest `next_mission_id`). A non-playable mission whose unlock rule is met is `in_preparation`; only The Last Train is playable in the MVP.
- English World catalog: `the-last-train` (playable) plus four locked missions: `the-interview` (grammar), `dinner-for-two` (vocabulary), `campus-day` (reading), `night-radio` (listening).
- Mission Report order: (1) the result, first and without clicks, in the brief's format: level label `A2 · The Last Train — 70%`, global %, per-skill %, correct/incorrect, suggested level with its reason, attempt record → (2) Maya's interpretation (can-do statements, the brief's "educational feedback") → (3) "Maya has prepared your next mission" → (4) the Diary → (5) missed checkpoints with explanation and correct answer (only after submission). Numbers never appear during the mission; on the report they come first.
- Demo users (demo-only password for all: `LastTrain2026!`):
  - `new@globalai.test` — Ana; first meeting with Maya.
  - `veteran@globalai.test` — Leo; 4 previous submitted attempts generated with the simulator (`A2_weak_listening`), coach memory and a visible progress trend.
  - `teacher@globalai.test` — Ms. Clarke; teacher of a class that contains both students (RBAC demo). An `admin` user exists only as a test fixture.
- Profile = per-skill % over the last 3 submitted attempts (all missions), computed by query (not stored) and shown with the number of attempts it is based on.

---

## 8. API surface (draft — the Tech Lead freezes it in `docs/contracts/api-contract.md`)

```
GET  /api/health
GET  /api/config                 public: {demo_mode, demo_accounts | null, demo_password | null}; lists only when DEMO_MODE=true
POST /api/auth/login            POST /api/auth/logout            GET /api/auth/me
GET  /api/world                                  cards with state, is_maya_pick, open attempt id/clock, latest label; greeting; snapshot
POST /api/missions/{mission_id}/attempts          start, or return the OPEN attempt (in_progress, or completed and not yet submitted)
GET  /api/attempts/{attempt_id}                   current StateView (resume after a lost connection)
POST /api/attempts/{attempt_id}/advance           {node_id}                  → StateView
POST /api/attempts/{attempt_id}/answer            {node_id, option_id|text}  → {maya_line, state}  (no outcome field: it would reveal correctness; validation below)
POST /api/attempts/{attempt_id}/submit            grade + coach → Report (idempotent)
GET  /api/attempts/{attempt_id}/report
GET  /api/me/progress                            profile, attempt history, level history, Maya's notes (≤ 5), open attempt | null
GET  /api/teacher/classes                         teacher/admin only
GET  /api/teacher/classes/{class_id}/progress     that class's teacher or admin; another class → 404
GET  /api/missions/{mission_id}/simulate?profile=A2    STRETCH (only with Simulated replay); DEMO_MODE only; outcomes, never options
```

**StateView** is the only shape the client sees during a mission: attempt id and status, clock label, minutes_left, the current node (kind, scene lines with variants already resolved and, for checkpoints, the item's id, type, prompt, stimulus and options *without* correctness) and Maya (mood, decision, line).

**AnswerRequest validation** runs before any lock or write, so a rejected request never locks the checkpoint: exactly one of `option_id` / `text`; `option_id` is required for choice types and must be one of the current item's option ids; `text` is required for `fill_blank` and must be 1–80 characters after normalization. Anything else → 422 `VALIDATION_ERROR`.

**Forbidden** in every response while an attempt is open: `is_correct`, answer keys, accepted answers, explanations, edges and future nodes.

---

## 9. Security invariants (never weaken these)

1. Answer keys, explanations, edges and future nodes never leave the server while an attempt is open.
2. The client never sends scores or correctness; request models use `extra="forbid"`.
3. A checkpoint answer is locked on first submission; a second answer returns 409.
4. Attempts are owned: another user's attempt returns 404 (not 403) to avoid enumeration. User-facing ids are UUIDs.
5. One open attempt (`in_progress` or `completed`) per (student, mission); starting again returns it, so a finished run can always be submitted.
6. The LLM runs only after grading and never influences score, level or unlocks.
7. When `/simulate` exists (stretch), its output contains outcomes, nodes and Maya's decisions — never chosen options or answer content.
8. Secrets only in environment variables; `.env` is never committed. The JWT lives in an httpOnly cookie, never in localStorage.

**Known, documented trade-offs:** the listening script reaches the browser because the MVP uses `speechSynthesis` (production: pre-generated audio behind signed URLs); retaking the same mission after reading its report is not a secure re-assessment (production: an item bank with variants).

---

## 10. Stack (decided)

- **Frontend:** React + TypeScript + Vite + Tailwind CSS · React Router · TanStack Query · Framer Motion · Web Speech API (`speechSynthesis`) · openapi-typescript · Vitest + Testing Library · Playwright (1–2 E2E specs).
- **Backend:** Python 3.12 · FastAPI · Pydantic v2 + pydantic-settings · SQLAlchemy 2.0 · Alembic · PostgreSQL 16 · PyJWT · argon2-cffi · httpx · anthropic SDK · pytest · ruff.
- **Infra:** Docker Compose · FastAPI serves the built SPA in production mode (single origin, no CORS) · Vite proxies `/api` in development.
- **Auth:** JWT (HS256, 60 minutes) in an httpOnly, SameSite=Lax cookie · roles `student`, `teacher`, `admin`.
- **Environment variables:** `DATABASE_URL`, `JWT_SECRET`, `COACH_PROVIDER` (`mock` | `anthropic`, default `mock`), `ANTHROPIC_API_KEY`, `ANTHROPIC_MODEL`, `DEMO_MODE`. `.env.example` ships working local defaults: `DEMO_MODE=true`, `COACH_PROVIDER=mock`, a non-empty dev-only `JWT_SECRET`.

---

## 11. Repository layout and ownership

```
global-ai-missions/
├── backend/
│   ├── app/core/              config, security, errors            tech-lead (skeleton) → backend-api-engineer
│   ├── app/engine/            pure-Python story graph engine      story-graph-engineer
│   ├── app/models/            SQLAlchemy models                   data-engineer
│   ├── app/repositories/      data access                         data-engineer
│   ├── app/services/          attempts, grading, leveling, state_view, report, world, progress   backend-api-engineer
│   ├── app/ai/                coach port, adapters, prompts       ai-coach-engineer
│   ├── app/api/routers/       HTTP layer                          backend-api-engineer
│   ├── app/schemas/           Pydantic DTOs                       backend-api-engineer
│   ├── app/core/demo.py       demo users constants (seed + /api/config) data-engineer
│   ├── alembic/, seed/                                            data-engineer
│   └── tests/                 each owner writes its own; gaps → qa-engineer
├── content/
│   ├── catalog.json                                               product-architect
│   ├── missions/_fixture/     tiny 10-checkpoint graph for the walking skeleton  story-graph-engineer
│   └── missions/the-last-train/
│       ├── items.json                                             assessment-designer
│       └── mission.json, SCRIPT.md                                narrative-designer
├── frontend/src/                                                  frontend-engineer
│   └── styles/tokens.css                                          ux-ui-designer
├── docs/
│   ├── agents/                this file and the README            the human
│   ├── ai/AI_ARCHITECTURE.md  AI vision, Spanish, evaluator-facing   ai-coach-engineer
│   ├── product/               PRODUCT, REQUIREMENTS_MAP, MAYA     product-architect
│   ├── contracts/             schemas, API contract, conventions  tech-lead
│   ├── assessment/            ASSESSMENT_SPEC                     assessment-designer
│   ├── design/UI_SPEC.md                                          ux-ui-designer
│   ├── design/BACKDROPS.md                                        narrative-designer
│   ├── engine/  data/  qa/                                        their respective owners
│   ├── DECISIONS.md, INTERVIEW.md, AI_USAGE_LOG.md                tech-lead
│   └── AI_USAGE.md                                                delivery-engineer
└── README.md, Dockerfile, docker-compose.yml, .env.example,
    .gitignore, Makefile, .github/                                 delivery-engineer
```

Rule: edit only what you own. If you need a change elsewhere, add an entry to `docs/contracts/CHANGE_REQUESTS.md` (who, what, why, impact) and tell the human.

---

## 12. Content format (draft — the Tech Lead freezes it as JSON Schema)

`content/missions/the-last-train/items.json` (assessment-designer):

```json
{
  "mission_id": "the-last-train",
  "items": [
    {
      "id": "q02", "type": "multiple_choice", "skill": "listening", "cefr": "A1",
      "prompt": "Which platform does the announcer say?",
      "stimulus": { "kind": "audio", "speaker": "Station announcer", "audio_script": "…", "rate": 0.85, "text": null },
      "options": [ { "id": "a", "text": "…" }, { "id": "b", "text": "…" }, { "id": "c", "text": "…" } ],
      "answer_key": { "correct_option_id": "b" },
      "explanation": "…",
      "hint": "Listen for the number, not the name."
    },
    {
      "id": "q05", "type": "fill_blank", "skill": "grammar", "cefr": "A2",
      "prompt": "Could I ___ a single ticket, please?",
      "stimulus": { "kind": "dialogue", "speaker": "You", "text": "…" },
      "options": null,
      "answer_key": { "accepted": ["have", "get", "buy"] },
      "explanation": "…",
      "hint": "…"
    }
  ]
}
```

- `stimulus.rate` (audio only): the `speechSynthesis` rate, 0.8–1.0 (about 0.85 for A1–A2, 1.0 for B1–B2). The client uses it and never needs the item's CEFR.
- Content integrity (checked by the engine validator, and the seed aborts on failure): choice items have 3–4 options with unique ids and `correct_option_id` among them; `fill_blank` has `options: null` and at least one accepted answer, stored normalized and de-duplicated; the first accepted answer is the one the report displays.

`content/catalog.json` (product-architect): `{ "catalog_version", "missions": [ { "id", "title", "world_zone", "skill_focus": [skill], "cefr_range": { "min", "max" }, "playable", "unlock_rule": { "kind": "always" | "mission_submitted" | "level_reached", "mission_id"?, "min_level"?, "hint" }, "teaser", "sort_order" } ] }`.

`content/missions/the-last-train/mission.json` (narrative-designer):

```json
{
  "mission_id": "the-last-train", "version": 1, "title": "The Last Train",
  "setting": { "city": "London", "start_clock": "21:47", "minutes_available": 18 },
  "companion": {
    "id": "maya", "name": "Maya",
    "mood_lines": { "curious": ["…"], "encouraging": ["…"], "worried": ["…"], "proud": ["…"] }
  },
  "flags": [ { "id": "lost_ticket", "description": "…" } ],
  "start_node": "intro",
  "nodes": [
    { "id": "intro", "kind": "narrative",
      "scene": { "location": "Station concourse", "backdrop": "concourse_night",
                 "lines": [ { "speaker": "narrator", "text": "LONDON — 21:47. You have 18 minutes before the last train leaves." } ] } },
    { "id": "c02", "kind": "checkpoint", "item_id": "q02",
      "scene": { "location": "…", "backdrop": "…",
                 "lines": [ { "speaker": "maya", "text": "Listen carefully. There was something unusual about what he said." } ] },
      "maya": { "reaction_ok": "…", "reaction_fail": "You understood the situation, but you missed the reason he gave." } },
    { "id": "c02_fail", "kind": "consequence",
      "scene": { "location": "…", "backdrop": "…",
                 "lines": [ { "speaker": "narrator", "text": "…" } ],
                 "variants": [ { "when_flag": "lost_ticket", "lines": [ { "speaker": "maya", "text": "…" } ] } ] } },
    { "id": "end_made_it", "kind": "ending",
      "ending": { "priority": 1, "condition": { "min_minutes_left": 0, "rescued": false } },
      "scene": { "…": "…" } }
  ],
  "edges": [
    { "from": "c02",    "to": "c02_ok",      "on": "correct",   "minutes": 1 },
    { "from": "c02",    "to": "c02_fail",    "on": "incorrect", "minutes": 3, "effects": { "set_flags": ["wrong_platform"] } },
    { "from": "c07",    "to": "c07_rescue",  "on": "incorrect", "minutes": 1, "rescue": true },
    { "from": "c02_ok", "to": "c03",         "on": "always",    "minutes": 0 },
    { "from": "c10_ok", "to": "end_made_it", "on": "ending",    "minutes": 0 }
  ]
}
```

- `ending` edges: the engine follows the one whose target ending has the best priority (lowest number) among those whose condition matches the state.
- Enums — node `kind`: `narrative | checkpoint | consequence | ending` · edge `on`: `always | correct | incorrect | ending` · item `type`: `multiple_choice | fill_blank | comprehension | vocabulary` · `skill`: `grammar | vocabulary | reading | listening | speaking` · `cefr`: `PRE_A1 | A1 | A2 | B1 | B2 | C1` · Maya decision: `quiet | hint | rescue` · mood: `curious | encouraging | worried | proud` · attempt status: `in_progress | completed | submitted` (completed = an ending was reached; submitted = graded).

---

## 13. Language

Code, comments, commit messages and all in-app content: **English**.
README, DECISIONS, INTERVIEW, AI_USAGE and docs/ai/AI_ARCHITECTURE.md: **Spanish** (the evaluators' language). Everything else in docs/ is an internal working note; the README's "Para evaluadores" section links only the Spanish documents.

---

## 14. Glossary

- **Mission** — a playable story that is, internally, one assessment.
- **Scene** — what is on screen at a node.
- **Checkpoint** — a node that holds exactly one item.
- **Item** — a leveled, skill-tagged assessment question.
- **Consequence** — the narrative node after a checkpoint outcome.
- **Ending** — a goal node.
- **Story clock / story-minutes** — diegetic time; the path cost.
- **Flag** — story memory set by a branch.
- **Rescue** — Maya's one-time cheaper edge.
- **Mission Report** — the result screen.
- **Diary** — the reconstructed path of an attempt.
- **English World** — the dashboard map of missions.
- **Profile** — rolling per-skill performance of a student.
- **Coach memory** — what Maya remembers between sessions.
- **Attempt / Step** — one run of a mission / one persisted transition.

---

## 15. Project definition of done

- The full required flow works locally with one command, with seeded demo users, within the 8-hour budget.
- Every assessment invariant and security invariant is covered by an automated test.
- A stranger can run the project from the README in under 5 minutes.
- DECISIONS.md fits in 2 pages and covers the 8 required points.
- AI_USAGE.md truthfully declares the tools used and the candidate's personal contribution.
- The Git history tells the story in small, conventional commits.
