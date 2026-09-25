# API contract — Global AI Missions

> Owner: `tech-lead`. **Frozen at G0 (2026-09-24).** Changes only through [`CHANGE_REQUESTS.md`](CHANGE_REQUESTS.md).
> Sources: `docs/agents/SHARED_CONTEXT.md` §4–§9 (wins on conflict), `docs/product/PRODUCT.md` §5, `docs/product/DECISIONS_LOG.md`.
> The backend implements this document exactly; the frontend builds against it (mock adapter first, then the real API). `docs/contracts/openapi.json`, exported from FastAPI by the backend-api-engineer, must match it; this file is the human-readable source of truth.

Contents: 1 Conventions · 2 Error model · 3 Auth and roles · 4 Shared types · 5 Endpoints · 6 StateView · 7 Report · 8 Idempotency and concurrency · 9 Forbidden fields · 10 Out of scope

---

## 1. Conventions

- Base path `/api`. JSON in and out (`Content-Type: application/json`). Keys are `snake_case`.
- Timestamps: ISO 8601 in UTC with `Z` (`"2026-09-24T21:58:03Z"`).
- User-facing ids (users, attempts, classes) are UUID strings. Mission ids are slugs (`the-last-train`); node, item, option and ending ids are the content's external ids.
- A malformed UUID in a path returns **404 `NOT_FOUND`** (same as unknown or not owned), never 422, so ids cannot be probed.
- Percentages are **integers 0–100**, rounded half up from `100 × correct / total`.
- Enums:
  - `cefr`: `PRE_A1 | A1 | A2 | B1 | B2 | C1`. Display label: `PRE_A1` → `Pre-A1`, the rest unchanged.
  - `skill`: `grammar | vocabulary | reading | listening | speaking`. **Scored skills** in fixed display order: `grammar, listening, reading, vocabulary`. `speaking` is never scored in the MVP.
  - `item type`: `multiple_choice | fill_blank | comprehension | vocabulary`. Choice types = every type except `fill_blank`.
  - `node kind`: `narrative | checkpoint | consequence | ending`.
  - `attempt status`: `in_progress | completed | submitted` (completed = an ending was reached; submitted = graded). **Open** = `in_progress` or `completed`.
  - `maya decision`: `quiet | hint | rescue` · `maya mood`: `curious | encouraging | worried | proud`.
  - `world card state`: `available | in_progress | waiting_to_submit | completed | locked | in_preparation`.
- Every response carries `X-Request-ID` (echoed if the client sent one, otherwise generated). Authenticated responses carry `Cache-Control: no-store`.
- Report label format: `{cefr label} · {mission title} — {score_pct}%` → `A2 · The Last Train — 70%` (middle dot U+00B7, em dash U+2014).
- No pagination in the MVP (lists are small); history endpoints are paginated at scale.

---

## 2. Error model

Every non-2xx response has exactly this body:

```json
{ "error": { "code": "NODE_OUT_OF_SEQUENCE", "message": "Developer-facing text.", "details": { } } }
```

- `code` is stable and from the table below. `message` is for developers and logs; **the frontend picks its user copy from `code`** (PRODUCT §5 microcopy), never from `message`.
- `details` is an object or `null`. No stack traces, SQL or internal ids ever appear.
- Implemented by `backend/app/core/errors.py` (pure: `ErrorCode`, `DomainError`) and `backend/app/api/error_handlers.py` (the FastAPI mapping). Services raise `DomainError`; they never build responses.

| Code | HTTP | When | `details` |
|---|---|---|---|
| `INVALID_CREDENTIALS` | 401 | Login with an unknown email or a wrong password (same response for both). | `null` |
| `UNAUTHENTICATED` | 401 | Missing, malformed, tampered or expired session cookie, or its user no longer exists. | `null` |
| `FORBIDDEN_ROLE` | 403 | Authenticated, but the role is not allowed on this endpoint (e.g. a student on `/api/teacher/*`, a teacher on `/api/world`). | `{ "required": ["teacher", "admin"] }` |
| `NOT_FOUND` | 404 | Unknown resource, another user's attempt, a malformed id, a class the teacher does not teach, a non-playable or locked mission on start, `/simulate` with `DEMO_MODE` off, unknown route (405 keeps its status with this code). | `null` |
| `ATTEMPT_NOT_IN_PROGRESS` | 409 | `advance` or `answer` on an attempt that is `completed` or `submitted`. | `{ "state": StateView }` |
| `NODE_OUT_OF_SEQUENCE` | 409 | `node_id` is not the current node, or the current node is the wrong kind for the action (advance on a checkpoint/ending, answer on a non-checkpoint). Also a retried `advance`. | `{ "state": StateView }` |
| `CHECKPOINT_LOCKED` | 409 | `answer` for a checkpoint that already has an answer in this attempt (a retried Confirm). | `{ "state": StateView }` |
| `MISSION_NOT_FINISHED` | 409 | `submit` or `GET report` on an attempt that has not reached an ending (`in_progress`), or `GET report` before submit (`completed`). | `{ "state": StateView }` |
| `VALIDATION_ERROR` | 422 | Body/query shape errors (including extra fields: request models use `extra="forbid"`), and the AnswerRequest rules in §5.10. | `{ "errors": [ { "field": "option_id", "message": "..." } ] }` |
| `RATE_LIMITED` | 429 | Login rate limit exceeded. Header `Retry-After: <seconds>`. | `{ "retry_after_seconds": 42 }` |
| `INTERNAL_ERROR` | 500 | Anything unexpected (logged with the request id). | `null` |

**Client rule for every 409 on an attempt endpoint:** render `details.state` (the server's truth) and continue; never show a conflict error to the student (PRODUCT §5.3).

---

## 3. Auth and roles

- Session: JWT HS256 signed with `JWT_SECRET` (≥ 32 chars; the app refuses to boot otherwise). Claims: `sub` (user UUID), `role`, `iat`, `exp` (60 minutes). No refresh token in the MVP: on expiry the next call returns 401 `UNAUTHENTICATED` and the client shows "Your session ended…" (PRODUCT §5.1); the mission is safe on the server.
- Cookie: name `gam_session`, `HttpOnly`, `SameSite=Lax`, `Path=/`, `Max-Age=3600`, `Secure` when `COOKIE_SECURE=true` (any https deploy). The token is never in a response body, never in `localStorage`.
- `current_user` decodes the cookie and loads the user by `sub` on every request (role changes and deleted users take effect immediately). `require_role(*roles)` wraps it.
- CSRF: `SameSite=Lax` blocks cross-site POSTs with the cookie; all mutating endpoints are `POST` and accept JSON only. Nothing mutates on `GET`.
- CORS: none. Production is single origin (FastAPI serves the SPA); development uses the Vite proxy.

| Endpoint group | Public | student | teacher | admin |
|---|---|---|---|---|
| `GET /api/health`, `GET /api/config`, `POST /api/auth/login`, `POST /api/auth/logout` | yes | yes | yes | yes |
| `GET /api/auth/me` | `200 null` without a cookie; 401 with a bad or expired one (CR-008) | yes | yes | yes |
| `/api/world`, `/api/missions/{id}/attempts`, `/api/attempts/*`, `/api/me/progress` | 401 | own data only | 403 | 403 |
| `/api/teacher/classes`, `/api/teacher/classes/{id}/progress` | 401 | 403 | own classes (other class → 404) | all classes |
| `GET /api/missions/{id}/simulate` (stretch) | 401 | yes | yes | yes — only when `DEMO_MODE=true`, otherwise 404 |

Ownership: an attempt belonging to another user is **404**, not 403 (SHARED_CONTEXT §9.4).

---

## 4. Shared types

```ts
type UserView = { id: string; email: string; display_name: string; role: "student" | "teacher" | "admin" }

type Clock = {
  time: string            // "21:53" = setting.start_clock + (minutes_available - minutes_left)
  minutes_left: number    // integer; negative once the train has departed
  train_departed: boolean // minutes_left < 0 (the engine's automatic flag)
  label: string           // built by the server, rendered verbatim:
                          //   "21:53 · 12 min to departure" | "22:05 · Departing now" (0)
                          //   | "22:07 · Train departed — Plan B"
}

type EndingRef = { key: string; title: string }          // key from mission.json, e.g. "made_it"

type SkillScore = { skill: Skill; correct: number; total: number; pct: number }

type Profile = {                                         // PD-009
  based_on_attempts: number                              // 1..3
  skills: { skill: Skill; pct: number }[]                // the 4 scored skills, fixed order
}
// Profile pct = 100 × Σcorrect / Σtotal over the student's last 3 SUBMITTED attempts
// (all missions, by submitted_at), pooled per skill, computed by query, never stored.
// A skill with Σtotal = 0 is omitted. No submitted attempts → Profile is null.
```

---

## 5. Endpoints

### 5.1 `GET /api/health` — public

`200 { "status": "ok" }`. No database access (liveness only).

### 5.2 `GET /api/config` — public

```json
{
  "demo_mode": true,
  "demo_accounts": [
    { "email": "new@globalai.test", "display_name": "Ana", "role": "student", "purpose": "First meeting with Maya." },
    { "email": "veteran@globalai.test", "display_name": "Leo", "role": "student", "purpose": "Returning student: history, memory and progress trend." },
    { "email": "teacher@globalai.test", "display_name": "Ms. Clarke", "role": "teacher", "purpose": "Teacher of a class with both students (roles demo)." }
  ],
  "demo_password": "LastTrain2026!"
}
```

With `DEMO_MODE=false`: `{ "demo_mode": false, "demo_accounts": null, "demo_password": null }`. Values come from `backend/app/core/demo.py` (shared with the seed). The admin fixture is never listed. No other configuration is exposed.

### 5.3 `POST /api/auth/login` — public

Request (`extra="forbid"`): `{ "email": string (email shape, ≤ 254, trimmed and lowercased by the server), "password": string (1–128) }`

- `200 UserView` and `Set-Cookie: gam_session=…`. Logging in again replaces the cookie.
- `401 INVALID_CREDENTIALS` (unknown email or wrong password; the server still runs an argon2 verify on unknown emails to keep timing similar) · `422 VALIDATION_ERROR` · `429 RATE_LIMITED`.
- Rate limit: at most **5 login requests per minute per (client IP, normalized email)**; the 6th in the window → 429 with `Retry-After`. In-memory, per process: the one piece of per-instance state in the MVP (at scale: a shared store or the API gateway).

### 5.4 `POST /api/auth/logout` — public

No body. Always `204` and clears the cookie (`Max-Age=0`), whether or not a session existed.

### 5.5 `GET /api/auth/me` — any role

`200 UserView` · `200 null` when the request carries no `gam_session` cookie (an anonymous visitor is "not checked in", not an error; CR-008) · `401 UNAUTHENTICATED` when a cookie is present but invalid, tampered, forged, expired or belongs to a deleted user. The frontend's route guard and role-based landing use it and treat both `null` and 401 as "no session".

### 5.6 `GET /api/world` — student

```json
{
  "student": { "display_name": "Leo" },
  "greeting": { "text": "Welcome back, Leo. Last time fast speech was tricky…", "source": "memory", "mood": "encouraging" },
  "cards": [ MissionCard, … ],
  "snapshot": { "missions_played": 4, "latest_label": "A2 · The Last Train — 70%", "profile": Profile | null }
}
```

- `greeting.source`: `first_meeting` (no coach memory → the canonical line of PD-022, mood `curious`) or `memory` (`coach_memory.next_greeting`).
- `snapshot.missions_played` = number of submitted attempts (all missions). Empty state: `0`, `null`, `null`.
- `cards` sorted by catalog `sort_order`, all catalog missions:

```ts
type MissionCard = {
  mission_id: string; title: string; world_zone: string; teaser: string; sort_order: number
  skill_focus: Skill[]; cefr_range: { min: Cefr; max: Cefr }; playable: boolean
  state: "available" | "in_progress" | "waiting_to_submit" | "completed" | "locked" | "in_preparation"
  is_maya_pick: boolean
  unlock_hint: string                      // catalog unlock_rule.hint (the UI shows it on locked cards)
  open_attempt: null | {
    attempt_id: string; status: "in_progress" | "completed"
    clock: Clock; location: string         // "21:55" + "Platform 4" for "Continue your mission"
    ending: EndingRef | null               // set when status = completed ("Waiting to submit")
  }
  latest_result: null | { attempt_id: string; label: string; submitted_at: string }
  attempts_submitted: number
}
```

State rules (exactly one per card, evaluated in this order):

| Mission | Condition | `state` |
|---|---|---|
| playable | open attempt with status `in_progress` | `in_progress` |
| playable | open attempt with status `completed` | `waiting_to_submit` |
| playable | ≥ 1 submitted attempt | `completed` |
| playable | none of the above (and unlock rule met) | `available` |
| playable | unlock rule not met | `locked` |
| not playable | unlock rule met | `in_preparation` |
| not playable | unlock rule not met | `locked` |

- Unlock rules (PD-008): `always` → met · `mission_submitted {mission_id}` → the student has ≥ 1 submitted attempt of that mission · `level_reached {min_level}` → any submitted attempt's `suggested_cefr` has rank ≥ `min_level`. The LLM never influences this.
- `latest_result` is filled whenever a submitted attempt exists, also while another run is open.
- `is_maya_pick`: true only on the card whose `mission_id` equals the `next_mission_id` of the coach feedback of the student's **most recent submitted attempt** (the deterministic fallback value if that attempt has no feedback row). At most one card; none without submitted attempts.

### 5.7 `POST /api/missions/{mission_id}/attempts` — student (start or return the open attempt)

No body.

- If the student has an **open** attempt (`in_progress` or `completed`) for this mission → `200 StateView` of that attempt (nothing is created; a finished but unsubmitted run can always be submitted, PD-028).
- Otherwise creates an attempt on the mission's active version at its `start_node` → `201 StateView`.
- `404 NOT_FOUND`: unknown mission, not playable, no active version, or unlock rule not met.
- Race: two concurrent starts → the partial unique index `(user_id, mission_id) WHERE status IN ('in_progress','completed')` lets one insert win; the loser catches the conflict and returns the winner's attempt with `200`.

### 5.8 `GET /api/attempts/{attempt_id}` — student, owner

`200 StateView` for any status (this is how a student resumes after a reload or a lost connection) · `404 NOT_FOUND`.

### 5.9 `POST /api/attempts/{attempt_id}/advance` — student, owner

Request (`extra="forbid"`): `{ "node_id": string }` — must equal the current node (optimistic concurrency).

- Allowed only when `status = in_progress` and the current node is `narrative` or `consequence` (CONTINUE). The server follows the node's `always` edge, or resolves the `ending` edges by priority and condition.
- Reaching an ending sets `status = completed`, `completed_at`, `ending_node_id`.
- `200 StateView` · `404` · `409 ATTEMPT_NOT_IN_PROGRESS` · `409 NODE_OUT_OF_SEQUENCE` (includes a retried advance) · `422`.

### 5.10 `POST /api/attempts/{attempt_id}/answer` — student, owner

Request (`extra="forbid"`):

```json
{ "node_id": "c02", "option_id": "b" }      // choice types
{ "node_id": "c05", "text": "have" }        // fill_blank
```

Response `200`:

```json
{ "maya_line": "You caught the number. Platform six it is.", "state": StateView }
```

`maya_line` is Maya's reaction (item-specific `reaction_ok` / `reaction_fail` / `reaction_rescue`, chosen by the engine); `state` is the node the story moved to (a consequence, or the rescue scene with `maya.decision = "rescue"`). There is **no `outcome` / `is_correct` field**: the student learns what happened only through the story (see §9).

**Processing order** (so that a rejected request never locks the checkpoint):

1. Body shape (Pydantic): exactly one of `option_id` / `text`; `node_id` string; `option_id` matches `^[a-z0-9]{1,8}$`; raw `text` ≤ 200 chars; no extra fields → else `422`.
2. Load the attempt **without a row lock**; not found / not owned → `404`.
3. The checkpoint `node_id` already has an answer in this attempt → `409 CHECKPOINT_LOCKED`.
4. `status ≠ in_progress` → `409 ATTEMPT_NOT_IN_PROGRESS`.
5. `node_id ≠ current node`, or the current node is not a checkpoint → `409 NODE_OUT_OF_SEQUENCE`.
6. Item rules → else `422 VALIDATION_ERROR`, checkpoint still answerable:
   - choice types: `option_id` required, `text` absent, and `option_id` is one of the **current item's** option ids;
   - `fill_blank`: `text` required, `option_id` absent, and 1–80 characters **after normalization** (lowercase, trim, collapse spaces, strip final punctuation, straighten curly apostrophes — the exact function is specified in `docs/assessment/ASSESSMENT_SPEC.md` and shared by validation and grading).
7. `SELECT … FOR UPDATE` the attempt and re-check 3–5 (a concurrent request may have won).
8. Grade on the server; the planner's decision at this checkpoint (recomputed deterministically, stored as `hint_shown`); apply `RESULT` (edge, minutes, flags, `train_departed`, at most one rescue); insert the answer (raw trimmed text is stored for the report; the normalized form is graded) and the step; commit. **The LLM is never called here.**

### 5.11 `POST /api/attempts/{attempt_id}/submit` — student, owner — two-phase, idempotent

No body.

- `in_progress` → `409 MISSION_NOT_FINISHED` (with `details.state`).
- **Phase 1 (one short transaction):** `SELECT … FOR UPDATE` the attempt. If already `submitted`, skip to phase 2's check. Otherwise grade and level (`services/grading.py`, `services/leveling.py`, exactly as ASSESSMENT_SPEC), save `attempt_skill_scores` and the attempt totals, set `status = submitted`, `submitted_at`; commit.
- **Phase 2 (after the commit, no lock, no transaction held):** if no `coach_feedback` row exists for the attempt, call the coach (8-second total budget; any failure → deterministic fallback), then `INSERT … ON CONFLICT (attempt_id) DO NOTHING`; update `coach_memory` **only if that insert wrote the row** (so `sessions_count` grows exactly once per attempt). If phase 2 fails for any reason, the request still succeeds.
- Response `200 Report` (§7) — the same body as `GET /report`. A retried or concurrent submit returns the same report; score and level are never recomputed after phase 1. Two concurrent first submits may both call the coach; only one row is stored.
- `404` · `409 MISSION_NOT_FINISHED`.

### 5.12 `GET /api/attempts/{attempt_id}/report` — student, owner

`200 Report` when `submitted` · `409 MISSION_NOT_FINISHED` when `in_progress` or `completed` (with `details.state`: the client redirects to the Mission Player or the Ending) · `404`. If no feedback row exists yet, the report renders the deterministic mock (`feedback_source.status = "fallback"`). Past reports are read-only and reachable from Progress.

### 5.13 `GET /api/me/progress` — student

```json
{
  "profile": Profile | null,
  "history": [ HistoryRow, … ],            // submitted attempts, newest first
  "level_history": [ { "attempt_id": "…", "submitted_at": "…", "suggested_cefr": "A2" } ],  // oldest first (chronological, for a trend)
  "notes": [ { "text": "Hesitates when people speak quickly; strong with signs and menus.", "created_at": "…" } ],  // ≤ 5, newest first
  "open_attempt": null | { "attempt_id": "…", "mission_id": "the-last-train", "mission_title": "The Last Train", "status": "in_progress" | "completed", "clock": Clock }
}
```

```ts
type HistoryRow = {
  attempt_id: string; attempt_number: number; mission_id: string; mission_title: string
  submitted_at: string; ending: EndingRef; label: string; suggested_cefr: Cefr
  score_pct: number; correct: number; incorrect: number
  skills: SkillScore[]                     // the 4 scored skills, fixed order
}
```

`attempt_number` = 1-based position of the attempt among the student's attempts **of that mission**, ordered by `started_at` (stable: attempts are never deleted). Empty state: `profile: null, history: [], level_history: [], notes: [], open_attempt: null`. If a student had several open attempts on different missions (impossible in the MVP), the most recently active one is returned.

### 5.14 `GET /api/teacher/classes` — teacher, admin

`200 { "classes": [ { "class_id": "uuid", "name": "Evening B1", "teacher_name": "Ms. Clarke", "student_count": 2 } ] }` — a teacher sees only the classes they teach; an admin sees all. `403` for students.

### 5.15 `GET /api/teacher/classes/{class_id}/progress` — that class's teacher, or admin

```json
{
  "class_id": "uuid", "name": "Evening B1",
  "students": [
    { "display_name": "Leo", "missions_played": 4, "latest_label": "A2 · The Last Train — 70%", "profile": Profile | null, "last_activity_at": "…" | null }
  ]
}
```

Read-only, no user ids, no drill-in to individual reports (PD-030). A teacher asking for a class they do not teach → **404** (not 403). Students → 403.

### 5.16 `GET /api/missions/{mission_id}/simulate?profile=A2&seed=7` — STRETCH, any authenticated role, `DEMO_MODE` only

Built only with the Simulated replay (PRODUCT §5.8). `DEMO_MODE=false` → `404 NOT_FOUND`. `profile` ∈ `A1 | A2 | B1 | B2 | A2_weak_listening` (else 422); `seed` optional integer (default 1).

```json
{
  "mission_id": "the-last-train", "profile": "A2", "seed": 7,
  "steps": [ { "seq": 1, "node_id": "c02", "kind": "checkpoint", "clock": Clock, "outcome": "understood" | "missed" | null, "maya_decision": "hint", "maya_mood": "worried" } ],
  "ending": EndingRef, "story_minutes_used": 14
}
```

Never options, chosen answers, prompts or answer content (SHARED_CONTEXT §9.7).

---

## 6. StateView — the only shape the client sees during a mission

Returned by start, `GET /attempts/{id}`, advance, `answer.state` and every attempt-endpoint 409 (`details.state`). Built by one function, `to_state_view(...)` in `backend/app/services/state_view.py`, which is unit-tested against §9.

```json
{
  "attempt_id": "5b1d…",
  "mission_id": "the-last-train",
  "mission_title": "The Last Train",
  "status": "in_progress",
  "clock": { "time": "21:49", "minutes_left": 16, "train_departed": false, "label": "21:49 · 16 min to departure" },
  "node": {
    "id": "c02",
    "kind": "checkpoint",
    "scene": {
      "location": "Platform 6",
      "backdrop": "platform_6",
      "lines": [ { "speaker": "narrator", "text": "The speakers crackle above the crowd." } ]
    },
    "checkpoint": {
      "item_id": "q02",
      "type": "multiple_choice",
      "prompt": "Which platform does the announcer say?",
      "stimulus": { "kind": "audio", "speaker": "Station announcer", "audio_script": "…", "rate": 0.85, "text": null },
      "options": [ { "id": "a", "text": "Platform two" }, { "id": "b", "text": "Platform six" }, { "id": "c", "text": "Platform sixteen" } ]
    },
    "ending": null
  },
  "maya": { "mood": "curious", "decision": "quiet", "line": "Listen carefully. Something about the platform changed." }
}
```

Field rules:

- `node.scene`: location, backdrop and lines with **variants already resolved** on the server (first matching flag wins; `train_departed` variants give the Plan-B scene). The client never sees `variants` or flags.
- `node.checkpoint`: non-null only on checkpoints. `options` is `null` for `fill_blank`, whose `prompt` contains exactly one `___` gap (the text input goes there; max 80 characters). `stimulus` is `null` or the item's stimulus as in `items.schema.json` (listening: `audio_script` + `rate`, played with `speechSynthesis`, never shown as text except the PD-014 fallback). **No `skill`, `cefr`, `hint`, `explanation` or answer key.**
- `node.ending`: `EndingRef` only on ending nodes, otherwise `null`.
- `maya.line`: checkpoint → the item's `hint` when `decision = "hint"` (slack < 3), otherwise the checkpoint's `maya.intro`; other nodes → the node's `maya.line` (or a variant's `maya_line`), else a mood line chosen by the engine, else `null`.
- `maya.decision`: checkpoint → `quiet | hint`; a node reached through a rescue edge → `rescue`; otherwise `quiet`.
- What the client may do, derived from `status` and `node.kind` (no action list is sent):

| `status` | `node.kind` | Client action |
|---|---|---|
| `in_progress` | `narrative`, `consequence` | **Continue** → `advance { node_id }` |
| `in_progress` | `checkpoint` | select / type, **Confirm** → `answer` |
| `completed` | `ending` | Ending screen, **Submit mission** → `submit` |
| `submitted` | `ending` | open the Mission Report |

---

## 7. Report — the Mission Report (only for submitted attempts)

Returned by `submit` and `GET /report`. Block order on screen is PRODUCT §5.5 / PD-001: result → interpretation → next mission → Diary → missed checkpoints.

```json
{
  "attempt_id": "5b1d…",
  "mission_id": "the-last-train",
  "mission_title": "The Last Train",
  "label": "A2 · The Last Train — 70%",

  "result": {
    "score_pct": 70,
    "correct": 7,
    "incorrect": 3,
    "total": 10,
    "skills": [
      { "skill": "grammar",    "correct": 3, "total": 4, "pct": 75 },
      { "skill": "listening",  "correct": 1, "total": 2, "pct": 50 },
      { "skill": "reading",    "correct": 2, "total": 2, "pct": 100 },
      { "skill": "vocabulary", "correct": 1, "total": 2, "pct": 50 }
    ],
    "unmeasured_skills": ["speaking"],
    "suggested_level": {
      "cefr": "A2",
      "base_cefr": "B1",
      "reason": "70% points to B1. B1 needs 2 of 3 B1 checkpoints — you had 1 — so your suggested level is A2.",
      "evidence": [
        { "cefr": "B1", "correct": 1, "total": 3, "required": 2, "met": false },
        { "cefr": "A2", "correct": 3, "total": 3, "required": 2, "met": true }
      ]
    }
  },

  "attempt_record": {
    "attempt_number": 3,
    "started_at": "2026-09-24T21:41:10Z",
    "submitted_at": "2026-09-24T21:58:03Z",
    "ending": { "key": "made_it_with_maya", "title": "Made It, With Maya" },
    "story_minutes_used": 16,
    "rescue_used": true,
    "hints_received": 2
  },

  "interpretation": {
    "summary": "You can follow signs and short messages without help. …",
    "strength": "reading",
    "challenge": "listening",
    "recommendation": "Tonight, listen for numbers first, then names."
  },
  "feedback_source": { "status": "ready", "provider_label": "Claude" },

  "next_mission": {
    "mission_id": "night-radio",
    "title": "Night Radio",
    "skill_focus": ["listening"],
    "reason": "It trains listening, the skill that was hardest tonight.",
    "state": "in_preparation",
    "unlock_hint": "Opens after your first Mission Report on The Last Train."
  },

  "diary": [
    {
      "seq": 1, "clock": "21:47", "node_id": "intro", "kind": "narrative", "location": "Station concourse",
      "text": "We reached the concourse with eighteen minutes to spare.",
      "checkpoint": null, "maya_decision": "quiet"
    },
    {
      "seq": 2, "clock": "21:47", "node_id": "c02", "kind": "checkpoint", "location": "Platform 6",
      "text": "An announcement echoed across the platform.",
      "checkpoint": { "item_id": "q02", "type": "multiple_choice", "skill": "listening", "cefr": "A1", "outcome": "missed" },
      "maya_decision": "hint"
    }
  ],

  "missed": [
    {
      "item_id": "q02", "type": "multiple_choice", "skill": "listening", "cefr": "A1",
      "prompt": "Which platform does the announcer say?",
      "stimulus": { "kind": "audio", "speaker": "Station announcer", "audio_script": "…", "rate": 0.85, "text": null },
      "your_answer": "Platform two",
      "correct_answer": "Platform six",
      "explanation": "The announcer says 'six'; 'two' was the old platform.",
      "maya_tip": "Listen for the number, not the name."
    }
  ]
}
```

Field rules:

- `result`: server-computed at submit (phase 1) and read back from the stored scores; `correct + incorrect = total = 10`. `skills` lists the four scored skills in fixed order; `unmeasured_skills` drives "Speaking isn't measured in this mission yet." (PD-017).
- `suggested_level`: the §4 rule (base band from the global %, then the evidence cap stepping down). `evidence` lists every level checked, top-down; `reason` is one sentence from ASSESSMENT_SPEC's templates (PD-015). `base_cefr` = the band before the cap.
- `attempt_record.story_minutes_used` = `minutes_available − minutes_left` at the ending (path cost). `hints_received` = checkpoints where the planner decided `hint`.
- `interpretation` is the coach's (or fallback's) validated output. `strength` and `challenge` always equal the deterministic values; `memory_note` and `next_greeting` are stored in coach memory and are not part of the report.
- `feedback_source`: `status = "ready"` when a real LLM produced valid output; `"fallback"` for the mock provider, a timeout, an invalid output or a missing feedback row. `provider_label` is supplied by the adapter that produced the text (e.g. `"Claude"`; the mock's own label otherwise). The UI chooses its footnote by `status` and never hard-codes a provider (PD-016).
- `next_mission`: the catalog mission named by `next_mission_id` (validated against the candidates: the non-playable catalog missions, PD-010), with its current card state for this student (`locked` or `in_preparation`) and one deterministic sentence of why.
- `diary`: every persisted step in order, rebuilt from the parent pointers; `text` is the node's `diary` line (variant-resolved) or its first scene line. Checkpoint entries carry type · skill · CEFR and a neutral `outcome` (`understood | missed`) — allowed here because the attempt is closed (PD-029). `maya_decision` marks hint and rescue moments ("Maya's shortcut").
- `missed`: every incorrect checkpoint in mission order; `your_answer` is the chosen option's text or the typed text; `correct_answer` is the correct option's text or the **first** accepted answer; listening items include the transcript through `stimulus.audio_script`.

---

## 8. Idempotency, concurrency and the open-attempt rule

| Operation | Retry / race behaviour |
|---|---|
| Start | Returns the open attempt if one exists (200); a race on creation resolves through the partial unique index (loser returns the winner, 200). One open attempt per (student, mission). |
| Advance | Optimistic: `node_id` must be current. A retry after success gets `409 NODE_OUT_OF_SEQUENCE` with the current `state` — the client renders it. |
| Answer | Locked on first write (`UNIQUE(attempt_id, question_id)` + row lock). A retried Confirm gets `409 CHECKPOINT_LOCKED` with the current `state`; the client continues silently. Validation failures (422) never lock. |
| Submit | Two-phase (§5.11). Repeats return the same report; grading happens exactly once; coach memory is updated exactly once. |
| Report / world / progress / state | Pure reads. |
| Login | Not idempotent by design (rate limited). Logout is idempotent. |

The server is authoritative for everything: node, clock, flags, correctness, score and level. The client never sends scores, minutes, correctness or a next node.

---

## 9. Forbidden fields

**A. While an attempt is open** — in every StateView-bearing response (start, `GET /attempts/{id}`, advance, answer, and `details.state` of every 409), no key anywhere in the JSON may be one of:

`is_correct`, `correct`, `incorrect`, `outcome`, `correct_option_id`, `answer_key`, `accepted`, `accepted_answers`, `correct_answer`, `explanation`, `hint`, `skill`, `cefr`, `score_pct`, `edges`, `edge`, `nodes`, `next_node_id`, `variants`, `when_flag`, `flags`

(the hint's *text* appears only as `maya.line` when the planner decided `hint`; `audio_script` is allowed — documented trade-off, SHARED_CONTEXT §9). QA's recursive scanner asserts this over a full in-progress run.

**B. Everywhere except the Report of a submitted attempt**: no `is_correct`, `correct_option_id`, `answer_key`, `accepted`, `accepted_answers`, `correct_answer` or `explanation`. `/api/world`, `/api/me/progress` and the teacher endpoints contain aggregates only (labels, percentages, counts), never item content.

**C. Requests**: every request model uses `extra="forbid"`; a client-sent `score`, `is_correct`, `minutes` or any unknown field → 422.

---

## 10. Out of scope for this contract

Sign-up, password reset, refresh tokens, pagination, teacher actions (assign, edit, export), content editing, WebSockets, free chat with Maya. Any addition goes through `CHANGE_REQUESTS.md`.
