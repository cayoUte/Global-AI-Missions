# PRODUCT — Global AI Missions

> Owner: `product-architect`. Source of truth above this file: `docs/agents/SHARED_CONTEXT.md`.
> Every product decision taken here is also recorded in `docs/product/DECISIONS_LOG.md` (ids `PD-xxx`).
> This file defines **what** the product does and how we know it works. **How** it is built belongs to the Tech Lead (`docs/contracts/`).

---

## 1. Pitch and concept

**Pitch (one sentence):** Global AI Missions is a story you play in English: tonight you have 18 minutes to catch the last train out of London with Maya, and without noticing you have just taken a leveled, 10-item English assessment.

**Concept.** We do not build an assessment system with game elements; we build a narrative experience that, internally, is an assessment. The student never sees "Question 3/10 · Listening". They see a station at night, hear an announcement, read a sign, talk to a guard, and decide what to do. Every decision is a leveled (A1–B2), skill-tagged item graded on the server. The story always continues, right or wrong: mistakes become detours and repairs, never red crosses. When the story ends, the student submits the mission and receives a **Mission Report**: first the plain result the evaluators expect (`A2 · The Last Train — 70%`, per-skill %, correct/incorrect, suggested level and why), then Maya's human reading of what that means and what to train next, then the **Diary** of the night they just lived. Maya remembers them. The next time they check in, she greets them with what she learned last time and has already prepared their next mission.

---

## 2. The core loop and where it lives on screen

`EXPERIENCE → DECISIONS → ASSESSMENT → PROFILE → AI FEEDBACK → NEXT MISSION → EXPERIENCE`

| Step | What it means | Where the student sees it | Where it lives in the system (for orientation only) |
|---|---|---|---|
| **Experience** | A scene: place, story clock, characters, Maya | **Mission Player**: backdrop, scene lines, story clock, Maya panel | Narrative nodes and variants (`mission.json`) |
| **Decisions** | The student acts inside the scene | **Mission Player** checkpoint: options, text field, "Listen" button, **Confirm** | Checkpoint node → one item (`items.json`) |
| **Assessment** | Silent, server-side grading; the story reacts | **Mission Player**: Maya's reaction and the consequence scene (never "correct/incorrect"). **Ending** → **Submit mission** | Transition model on the server; grading and leveling at submit |
| **Profile** | Rolling per-skill picture of the student | **Mission Report** block 1 (the result); **English World** progress snapshot; **Progress** | Submitted attempts → profile |
| **AI Feedback** | Maya interprets the result | **Mission Report** block 2 (interpretation) | Coach (LLM or mock) runs once inside submit |
| **Next Mission** | Maya recommends what to train next | **Mission Report** block 3 ("Maya has prepared your next mission"); **English World** card marked "Maya's pick"; Maya's greeting at the next check-in | `next_mission_id`, `next_greeting` in coach memory |
| back to **Experience** | The student returns to the world | **English World** → mission card → **Mission Player** | New attempt |

The loop must be visible end to end in the demo: new student plays → report → back to the World where the recommended mission is highlighted → veteran shows what the loop looks like after several turns (memory greeting, trend).

---

## 3. Student journeys

### 3.1 Journey A — first-time student (`new@globalai.test`, first meeting with Maya)

| # | Screen | What the student sees and does | What happens underneath |
|---|---|---|---|
| A1 | Check-in | Night-time London title card. Email + password. In demo mode, a "Demo accounts" panel lists the three seeded users. Presses **Check in**. | Auth; session cookie. Role `student` → English World. |
| A2 | English World | Maya's first-meeting greeting (see MAYA.md §6.1). Missions board: *The Last Train* available; four missions locked, each with its unlock hint. Progress snapshot empty state: "Your story starts tonight." | World endpoint returns catalog + per-student state + greeting (no memory yet → canonical first-meeting line). |
| A3 | English World | Taps **Start mission** on *The Last Train*. | Attempt created (or resumed if one exists). |
| A4 | Mission Player — intro | "LONDON — 21:47. You have 18 minutes before the last train leaves." Story clock visible. Maya introduces herself inside the scene in one or two lines. **Continue**. | Narrative node; clock 18 min left. |
| A5 | Mission Player — checkpoints 1–10 | Scenes at the station: announcements to listen to, a ticket machine, a sign to read, a guard to answer. Each checkpoint is one decision. After **Confirm**, Maya reacts in one line and the consequence scene plays; the clock moves by the story-minutes of that path. If time runs short, Maya offers a strategy hint before a decision. At most once, after a mistake that would cost the train, Maya rescues the situation. | Each answer locked on first submit; step persisted; planner decides quiet / hint / rescue; flags change later scenes; `train_departed` switches remaining scenes to Plan B (night bus). |
| A6 | Ending | One of three endings (`made_it`, `made_it_with_maya`, `night_bus`), all warm. Maya's closing line. No score on this screen. **Submit mission**. | Attempt status `completed`. |
| A7 | Mission Report | "Maya is reading your Diary…" (≤ ~10 s). Then: (1) the result: `A2 · The Last Train — 70%`, per-skill %, correct/incorrect, suggested level with its one-line reason, attempt record, (2) Maya's interpretation with can-do statements, (3) "Maya has prepared your next mission" card, (4) the Diary, (5) missed checkpoints with the correct answer and explanation. | Submit: grade → level → coach (8 s budget, fallback) → memory updated → status `submitted`. Idempotent. |
| A8 | English World | **Back to the English World.** The Last Train now shows the latest result label and **Play again**; the recommended mission carries the "Maya's pick" marker; missions whose rule is now met change from locked to "Maya is preparing this mission". Progress snapshot shows the first profile. | World recomputed from submitted attempts. |
| A9 | Progress | One attempt row, first per-skill profile, "Maya's notes" with one note. | Progress endpoint. |

### 3.2 Journey B — returning student (`veteran@globalai.test`, fifth session)

Seed: 4 submitted attempts generated by the simulator with profile `A2_weak_listening`, coach memory with notes and a stored `next_greeting`.

| # | Screen | What the student sees and does | What happens underneath |
|---|---|---|---|
| B1 | Check-in | Checks in. | Same as A1. |
| B2 | English World | Maya greets them by first name with the stored `next_greeting` that references a concrete observation (e.g. fast speech and numbers). Progress snapshot: latest level label, four skill bars, "4 missions played". *Night Radio* carries "Maya's pick" (listening is the challenge). *The Last Train* shows the last result and **Play again**. | `coach_memory.next_greeting`; profile from the last 3 submitted attempts. |
| B3 | Progress | Attempt history (4 rows, each opens its Mission Report), per-skill trend across attempts with listening visibly lagging, suggested-level history, Maya's notes (last 5). | Demonstrates "attempt record" and "progress view". |
| B4 | Mission Player | **Play again** starts a fresh attempt (session 5). Scenes and Maya's in-mission lines are the same content for everyone (PD-021); her greeting and report voice use the familiar stage. | New attempt; one open attempt per (student, mission). |
| B5 | Resume (demo of resilience) | Reload the browser mid-mission, or close the tab and check in again: the student lands exactly on the same scene with the same clock; the English World card says **Continue your mission** with the current clock time. | Attempt state reloaded from the server; answered checkpoints stay locked. |
| B6 | Ending → Report → World | Same as A6–A8. Maya's interpretation mentions change against memory when sessions ≥ 2 ("Listening is getting easier: you caught the platform number tonight."). | Coach prompt receives memory. |

---

## 4. How assessment, narrative, progression and coaching connect per screen

| Screen | Narrative | Assessment | Progression | AI coaching (Maya) |
|---|---|---|---|---|
| Check-in | London-at-night title card | — | — | — |
| English World | Missions as places in one world | — | Progress snapshot; card states; unlock hints | Greeting from memory; "Maya's pick" |
| Mission Player | Scenes, flags, variants, clock, Plan B | Checkpoints = items; answers locked on first submit; no correctness shown | Clock is the only progress indicator | Planner: quiet / hint / rescue; mood; reaction lines (deterministic, authored) |
| Ending | One of three endings | Attempt `completed`; no score here | — | Closing line (authored) |
| Mission Report | Diary retells the night | Numbers, level with reason, missed items with answers | Attempt record; profile updated | Interpretation, strength/challenge, recommendation, next mission (LLM or fallback) |
| Progress | — | History of results | Trend, level history | Maya's notes (memory) |

---

## 5. Screen acceptance criteria

Conventions: **Must** criteria are MVP. Every screen is usable at 360 px width without horizontal scroll, and on desktop at 1280 px. Every interactive element is reachable and operable by keyboard with a visible focus state. All text is English. No emojis, no XP/points/badges/streak vocabulary anywhere.

### 5.1 Check-in

- **Must** show product name, a one-line invitation ("Tonight, your English gets you home."), email and password fields and a **Check in** button.
- **Must** submit with Enter; the button is disabled and shows "Checking in…" while the request is in flight (loading).
- **Must**, on wrong credentials, show one generic message: "That email and password don't match." It never reveals whether the email exists (error).
- **Must**, on network/server failure, show "We couldn't reach Global AI. Check your connection and try again." and keep the typed email (error).
- **Must**, after too many tries (rate limit), show "Too many tries. Wait a minute and check in again." and keep the typed email (error).
- **Must** validate on the client only for presence and email shape; the server is the authority.
- **Must** route by role after success: student → English World; teacher/admin → Teacher view (stretch) or, if the stretch is not built, a plain read-only page stating that the teacher view is not part of this build.
- **Must**, when a session expires mid-use, bring the user here with "Your session ended. Check in again — your mission is saved." and, after check-in, take them to the English World, where **Continue your mission** resumes the run.
- **Must**, in demo mode only, show a "Demo accounts" panel listing the three demo emails, their role/purpose and the shared demo password; hidden when demo mode is off. The panel reads everything from the server (`GET /api/config`); no credentials live in the frontend bundle.
- An already-authenticated user who opens Check-in is sent to their home screen.
- There is no sign-up, password reset or social login (out of scope); no link pretends otherwise.
- Check-out (logout) is available from English World and Progress; it clears the session and returns here.

### 5.2 English World (dashboard)

- **Must** show Maya's greeting card at the top: avatar, first name of the student, and either the canonical first-meeting line (no memory) or the stored `next_greeting` (memory exists).
- **Must** show the missions board with all five catalog missions in `sort_order`, each with title, zone, skill focus, CEFR range and teaser.
- **Must** show each card in exactly one state, with these labels:

  | State | When | Card shows | Primary action |
  |---|---|---|---|
  | Available | playable, never started | teaser | **Start mission** |
  | In progress | an `in_progress` attempt exists | current story clock and location ("21:55 · Platform 4") | **Continue your mission** |
  | Waiting to submit | an attempt reached an ending but was not submitted | ending title | **Submit mission** (opens Ending) |
  | Completed | ≥1 submitted attempt | latest label `A2 · The Last Train — 70%` | **Play again**, secondary **View Mission Report** |
  | Locked | not playable, unlock rule not met | the rule's human-readable hint ("Opens after your first Mission Report on The Last Train.") | none |
  | In preparation | not playable, unlock rule met | "Maya is preparing this mission." | none |

- **Must** mark the mission equal to the student's latest `next_mission_id` with a "Maya's pick" marker (at most one card).
- **Must** show a progress snapshot: latest level label, the four scored skills as simple bars with %, missions played count, and a link **See your progress**.
- **Empty state (Must):** no submitted attempts → snapshot reads "Your story starts tonight. Your progress will appear here after your first mission."; no "Maya's pick" marker. The **See your progress** link stays visible.
- **Loading (Must):** skeleton cards and a greeting placeholder; no layout jump when data arrives.
- **Error (Must):** "The lights went out for a moment. Try again." with **Try again**; nothing half-rendered.
- Locked and in-preparation cards are not clickable as missions; they may expand their hint.
- No XP, coins, streak counters, leaderboards or badges.

### 5.3 Mission Player

General
- **Must** render only what the server sends for the current node; the client never computes correctness, the next node or the clock.
- **Must** show the story clock at all times as clock time plus minutes to departure ("21:53 · 12 min to departure"). It never shows "Question N of 10" or a percentage. At 0 minutes it reads "22:05 · Departing now". When the train has departed it reads "22:07 · Train departed — Plan B".
- **Must** show the scene: location name, backdrop, and scene lines with speaker (narrator, Maya, other characters). Lines appear one block at a time; **Continue** advances narrative and consequence nodes.
- **Must** show Maya's panel with her current mood expression and her current line (if any).
- **Must** offer **Pause** (back to the English World); the attempt is saved on the server and resumes at the same node.
- **Must** resume exactly on reload, on a new tab, or after check-in on another device: same node, same clock, same flags, answered checkpoints locked.

Checkpoints (one per item; exactly 10 on every path)
- **Must** present exactly one decision per screen.
- **Must** render by item type:
  - `multiple_choice` / `vocabulary`: the options as large tappable choices (whole row is the target).
  - `comprehension`: the reading stimulus (sign, message, notice, timetable) styled as an in-world object, then the options.
  - `fill_blank`: the sentence with the gap and a single text input in the gap; submits trimmed text.
  - Listening stimuli: a **Listen** button that plays the audio script via speech synthesis; **Listen again** replays it without limit. The transcript is not shown before answering.
- **Must** use a two-step decision: select, then **Confirm**. Nothing is sent before Confirm; Confirm is disabled until an option is selected or the trimmed text is not empty.
- There is no skip action (PD-011): every checkpoint needs a decision to continue, so every item is answered and "not answered" never exists in the product.
- **Must** lock the answer on the first Confirm: options are disabled, and the UI never offers to change it.
- **Must**, when Maya's decision is **hint**, show her strategy line before the student decides, visually as Maya speaking (not as a system tooltip). The hint never contains or eliminates an option.
- **Must**, after Confirm, show Maya's reaction line and then the consequence scene. The UI **never** shows the words correct/incorrect/wrong/right, never colors options red/green, never plays success/failure sounds and never reveals the correct answer during the mission.
- **Must**, when Maya's decision is **rescue**, play the rescue scene framed as teamwork ("Stay close — I know a shortcut."), never as a failure.
- **Must** apply a scene crossfade under 600 ms and respect `prefers-reduced-motion` (fade only or none).
- **Should** (only after G2 is green): typewriter text (skippable), clock flip on each minute, a subtle idle for Maya, a listening waveform.

States
- **Loading (Must):** between nodes, the current scene stays visible with a subtle transition; if a response takes longer than 1 s, show Maya's idle line "One moment…". No blocking spinner without text.
- **Error (Must):** if a request fails, show "The signal dropped. Your place in the story is saved." with **Try again**. A retried Confirm that the server reports as already answered (lock) must silently fetch the current state and continue — the student never sees a conflict error.
- **Error (Must):** if the attempt no longer exists or is not theirs → "We couldn't find this mission run." with **Back to the English World**.
- **Error (Must):** if speech synthesis is unavailable, the Listen button explains "Audio isn't available on this device" and shows the announcement as a written transcript so the story can continue (documented limitation; see PD-014).
- **Empty:** not applicable (a mission always has a current node); if the mission cannot be loaded at all, show the error state above.

Pace
- **Must** be completable by a practised presenter in ≤ 5 minutes (drives the 10-minute demo): narrative nodes ≤ 3 short lines, no forced waits, no auto-advancing timers.

### 5.4 Ending

- **Must** show the ending title and closing scene for the ending reached: *made_it*, *made_it_with_maya*, *night_bus*. All three are warm and dignified; none suggests failure.
- **Must** show the final story clock and Maya's closing line with her mood expression.
- **Must not** show any score, level or count.
- **Must** show a primary **Submit mission** button with the helper line "Maya will read your Diary and prepare your Mission Report."
- **Loading (Must):** after Submit, "Maya is reading your Diary…" with her curious expression; the button is disabled; the wait can last up to ~10 s and never shows a raw spinner alone.
- **Error (Must):** "Your Diary is safe, but we couldn't finish the report. Try again." with **Try again**. Repeating submit is safe (idempotent) and leads to the same report.
- **Must** be reachable again from the English World ("Waiting to submit") if the student leaves before submitting. Reloading on the Ending, or checking in again, shows the same Ending with **Submit mission** (the finished run is always the student's open attempt until it is submitted).
- AI failure is not an error for this screen: the report always renders (fallback feedback).

### 5.5 Mission Report + Diary

Order is fixed (SHARED_CONTEXT §7, PD-001). The result comes first, exactly where an evaluator looks for it; Maya then explains it. No tabs, accordions or "show details" clicks before the end of block 2.

1. **The result (Must), plain and unambiguous, no diegetic renaming, first thing on screen:**
   - Kicker "English Assessment · Mission Report", then the report label as the page heading, in the brief's format: `A2 · The Last Train — 70%`.
   - **Global score** in %.
   - **Result per skill** (this heading, plain): Grammar, Listening, Reading, Vocabulary, each with % and "x of n". A muted note: "Speaking isn't measured in this mission yet."
   - **Correct** and **Incorrect** counts (they always add up to 10).
   - **Suggested level** with a one-line explanation of the rule applied, e.g. "70% points to B1. B1 needs 2 of 3 B1 checkpoints — you had 1 — so your suggested level is A2."
   - **Attempt record** (this heading, plain): attempt number for this mission, submitted date and time, ending reached, story-minutes used, whether Maya's rescue was used, number of hints received.
2. **Maya's interpretation (Must):** Maya's avatar and 2–4 short sentences that read the numbers above in human terms: `summary` phrased as can-do statements ("You can…"), the strength and the challenge in plain words, and one concrete `recommendation`. English adapted to the student's level. She never contradicts block 1.
3. **"Maya has prepared your next mission" (Must):** one compact card: title, skill focus, one line of why, and its state (Locked with hint / Maya is preparing this mission).
4. **The Diary (Must):** the path of the night in order: clock time, location, one line of what happened; checkpoints marked with a neutral tag of type, skill and level ("Multiple choice · Grammar · A2") and a neutral outcome marker ("Understood" / "Missed"), and Maya's hint/rescue moments. Reads like a travel journal, not a log.
5. **Missed checkpoints (Must):** for each missed item: its type · skill · level tag, the prompt, the student's answer, the correct answer, the explanation and Maya's strategy for next time. Listening items show their transcript here. Shown only for submitted attempts.

Also
- **Must** show actions **Back to the English World** and **See your progress**.
- **Must** show a small footnote "About this feedback": "Written by Maya using {provider_label}" (e.g. Claude) when the feedback status is ready, or "Written by Maya from her notebook (offline feedback)" when the mock or the fallback was used. The label comes from the server; the UI never hard-codes a provider. Never an error.
- **Loading (Must):** skeleton blocks in the same order; if arriving from Submit, the Ending loading state covers it.
- **Error (Must):** fetch failure → "We couldn't open this Mission Report. Try again." with retry. An attempt that is not the student's, or does not exist → "We couldn't find this Mission Report." (same message for both). An attempt not yet submitted → redirect to the Mission Player or Ending.
- **Empty:** not applicable (a report exists only for a submitted attempt).
- Past reports are reachable read-only from Progress and from the Completed card.

### 5.6 Progress

- **Must** show the current profile: the four scored skills with the rolling % (see PD-009) and how many missions it is based on.
- **Must** show the **Attempt history** (plain heading): one row per submitted attempt with attempt number, date, mission, ending, report label, correct/incorrect and the four per-skill % columns; each row opens that Mission Report.
- **Must** show the per-skill trend and the suggested-level history through that table: the per-skill % columns and the level label, row by row (readable at 360 px; no chart library). A chart is a Should after G3.
- **Must** show "Maya's notes": the last (up to 5) memory notes in her voice, newest first.
- **Must** show the open attempt, if any, as "In progress — Continue" or, when it reached an ending, "Waiting to submit — Submit mission".
- **Empty state (Must):** "Your story starts tonight. Play The Last Train and your progress will appear here." with **Go to the English World**.
- **Loading (Must):** skeleton rows and chart placeholder.
- **Error (Must):** "We couldn't load your progress. Try again." with retry.
- No comparisons with other students, no rankings.

### 5.7 Stretch — Teacher view (only when every gate is green)

- Read-only. Teacher sees their classes; per class, each student with first name, missions played, latest report label, per-skill profile and last activity date. No drill-in to individual reports in this build.
- A teacher cannot see classes or students that aren't theirs (the server returns not-found); an admin can see every class. A student navigating to the teacher view is sent back to their English World with "That page is for teachers."
- Loading, error ("We couldn't load your class.") and empty ("No students in this class yet.") states.
- No editing, assigning, messaging or exporting.

### 5.8 Stretch — Simulated replay (demo mode only)

- Reachable from a discreet "Watch a simulated run" link on the English World, visible only in demo mode.
- The presenter picks a profile (`A1`, `A2`, `B1`, `B2`, `A2_weak_listening`) and watches a run play: sequence of nodes, the story clock, Understood/Missed per checkpoint, Maya's quiet/hint/rescue decisions, mood, and the ending reached. Optionally a calibration summary (ending distribution over many runs).
- **Never** shows the options chosen or any answer content.
- Loading, error ("The simulation couldn't run.") states; hidden entirely when demo mode is off.

---

## 6. MVP scope

In the MVP (all Must):

1. Check-in with the three seeded demo users; check-out; role-based landing.
2. English World: greeting from memory, five-mission board (one playable), card states, Maya's pick, progress snapshot.
3. Mission Player for *The Last Train*: 10 checkpoints (4 multiple choice, 2 fill-in-the-blank, 2 comprehension, 2 vocabulary), story clock, flags and variants, Maya's planner (quiet/hint/rescue) and mood, Plan B after departure, resume.
4. Ending with three endings and **Submit mission**.
5. Mission Report with the fixed 5-block order: the result first (numbers, level, attempt record), then Maya's feedback, next mission, Diary and missed checkpoints.
6. AI feedback once per submission (Claude adapter or mock), always with fallback; coach memory feeding the next greeting.
7. Progress page with history, trend, level history and Maya's notes.
8. Responsive (360 px → desktop) and keyboard accessible.
9. One simulated "next mission": recommended and displayed, not playable.

## 7. Stretch goals (only if every gate G0–G3 is green)

In priority order: (1) Teacher view (read-only); (2) Simulated replay (demo mode). A second AI provider adapter is a Tech Lead / AI Coach decision, not a product feature. Anything else goes through the out-of-scope test in §8.

## 8. Out of scope (and why)

Test for any new idea: *Does it serve the core loop or a line of the evaluators' checklist, and can it be demonstrated in 10 minutes?* If not, it goes here.

| Feature | Why it is out |
|---|---|
| XP, points, coins, hearts, lives, streaks, badges, trophies, confetti, leaderboards | Contradicts the concept: they turn a story into a scoreboard and reintroduce fear of failure. The only numbers live on the Mission Report. |
| Real-time countdown timer | The story clock is diegetic and moves only with the path taken; real time pressure would measure speed and anxiety, not English. |
| Open world / free map navigation / walking around the station | Huge content and UI cost for no assessment value; the braided graph already gives meaningful consequences. |
| Speech recognition, pronunciation scoring, scored Speaking | Unreliable in browsers, privacy-sensitive, cannot be graded deterministically in a one-day build. `speaking` stays in the data model as roadmap. |
| Free chat with Maya (during or after the mission) | Could leak answers, is unbounded in cost and safety, and breaks the rule that the LLM never controls the flow. Maya speaks through authored lines and one structured feedback. |
| LLM-generated scenes, items or hints at runtime | Items must be fixed, leveled and validated; the planner decides Maya's actions deterministically. |
| Adaptive item selection during the mission (CAT) | Would break the invariant that every path visits the same 10 checkpoints; roadmap with an item bank. |
| More playable missions | One extraordinary mission beats five thin ones; the four others are catalog entries only. |
| Multiplayer, friends, sharing, social feeds | No assessment value; adds privacy and moderation scope. |
| Content CMS / mission editor / admin UI | Content is versioned JSON validated by the engine; an editor is a product of its own. The `admin` role exists in the data model only. |
| Native mobile apps / offline mode / PWA install | The web app is responsive; native packaging adds no evaluator value. |
| Sign-up, password reset, email verification, social/SSO login | Demo users are seeded; the brief asks for basic authentication. |
| Reminders by email/push, notifications | Documented as the future of AI accompaniment in `docs/ai/AI_ARCHITECTURE.md` (Spanish), not built. |
| Teacher actions (assign missions, edit, message, export) | Teacher view, if built, is read-only for the RBAC demo. |
| Payments, subscriptions, certificates | Not part of an assessment prototype. |
| Avatar customization, character creation | Cosmetic; no educational value. |
| UI localization (Spanish UI, translations of prompts) | In-app content is English by decision (§13); translations would weaken the assessment. |
| Secure re-assessment on retake | Known trade-off: replaying the same mission after reading its report is practice, not a new assessment (production: item bank with variants). |
| Analytics dashboards beyond the Progress page | No brief requirement. |

## 9. UX principles

1. **Story first, numbers after.** During the mission the student only sees the world. Numbers appear once, on the Mission Report, in plain words.
2. **Nothing punishes.** Mistakes become detours and repairs. No red, no buzzers, no "wrong". Every ending is dignified.
3. **One decision per screen.** One checkpoint, one clear action, large targets.
4. **Diegetic labels, unless they hide a required function.** We rename screens and progress (Check-in, English World, story clock, Mission Report, Diary), but actions the evaluators look for keep their plain verbs: **Submit mission**, **Progress**, and the report's labels (Global score, Result per skill, Correct, Incorrect, Suggested level, Attempt record), plus **Attempt history** on Progress.
5. **Honest numbers.** The level comes with its reason. Hints never change the score. Numbers are hidden during the story and shown first, in full, on the report.
6. **Maya is brief.** In the mission, one or two short sentences per bubble. She never lectures.
7. **Always recoverable.** Every request can fail and be retried; the story resumes where it was.
8. **Calm motion.** Short fades and slides that support the scene; reduced motion respected.
9. **Mobile first, keyboard complete, readable.** 360 px, visible focus, sufficient contrast on night backdrops, no information by color alone.
10. **Level-appropriate English.** UI copy and Maya's lines stay at A2-readable English; the challenge lives in the items, not in the buttons.

## 10. Microcopy

| Generic label | Global AI Missions label |
|---|---|
| Login / Sign in | **Check in** |
| Logout | **Check out** |
| Dashboard / Home | **English World** |
| Start assessment / Start test | **Start mission** |
| Resume | **Continue your mission** |
| Question 3/10 / progress bar | Story clock: **21:53 · 12 min to departure** |
| Next | **Continue** |
| Submit answer | **Confirm** |
| Skip | (none: every checkpoint needs a decision) |
| Hint | Maya speaking (no label) |
| Correct! / Wrong! | No label; Maya's reaction + consequence scene |
| Finish / Submit test | **Submit mission** |
| Results / Score page | **Mission Report** |
| Answer review | **Diary** (+ "Checkpoints to revisit" for missed items) |
| Attempt record / attempt history | **Attempt record** / **Attempt history** (plain, kept) |
| Recommended next | **Maya has prepared your next mission** |
| Locked | **Opens after …** (the rule's hint) |
| Coming soon | **Maya is preparing this mission.** |
| Recommended badge | **Maya's pick** |
| History / Statistics | **Progress** (required word, kept) |
| Loading | Maya-voiced lines: "One moment…", "Maya is reading your Diary…" |
| Network error | "The signal dropped. Your place in the story is saved." |

Banned in UI and in Maya's lines: XP, points, level up, streak, combo, reward, unlock achievement, "Great job!!!", "Oops!", "Wrong", "Fail", "Game over", emojis, exclamation chains.

## 11. Terminology (aligned with SHARED_CONTEXT §14)

| Term | Meaning | Shown to the student as |
|---|---|---|
| Mission | A playable story that is, internally, one assessment | "mission" |
| Scene | What is on screen at a node | (the scene itself) |
| Checkpoint | A node that holds exactly one item | never named; it is a decision |
| Item | A leveled, skill-tagged assessment question | never named during the mission; "checkpoint" in the Diary |
| Consequence | The narrative node after a checkpoint outcome | (the scene itself) |
| Ending | A goal node | ending title (e.g. "Night Bus") |
| Story clock / story-minutes | Diegetic time; the path cost | "21:53 · 12 min to departure" |
| Flag | Story memory set by a branch | never named |
| Rescue | Maya's one-time cheaper edge | "Maya's shortcut" in the Diary |
| Mission Report | The result screen | "Mission Report" |
| Diary | The reconstructed path of an attempt | "Diary" |
| English World | The dashboard map of missions | "English World" |
| Profile | Rolling per-skill performance | "Your English today" (Progress / snapshot) |
| Coach memory | What Maya remembers between sessions | "Maya's notes" |
| Attempt / Step | One run of a mission / one persisted transition | "attempt" on the report and Progress ("Attempt 3 · submitted 24 Sep 21:58"); "mission run" only in Maya's voice / Diary entry |
| Maya's pick | The mission Maya recommends next (`next_mission_id`) | "Maya's pick" |
| Unlock rule | Deterministic condition that opens a catalog mission | "Opens after …" |

## 12. Demonstrability — the 10-minute shape

(QA owns the final script; this is the product intent it must preserve.)

| Minute | Beat | Proves |
|---|---|---|
| 0:00–0:45 | Check-in as `new@`; English World with first-meeting greeting and locked missions | login, dashboard, catalog |
| 0:45–5:30 | Play *The Last Train* end to end (one deliberate mistake, see Maya react; one listening checkpoint) | access assessment, 10 items, immersion, no answers shown |
| 5:30–7:00 | Ending → Submit mission → Mission Report: numbers, Maya, next mission, Diary, missed checkpoint | submit, score, per-skill, counts, level, AI feedback, attempt record |
| 7:00–8:30 | Check out; check in as `veteran@`: memory greeting, Maya's pick, Progress trend and notes | progress view, profile, coach memory, next mission |
| 8:30–9:30 | DevTools: network responses carry no answer keys; reload mid-mission resumes | security, resilience |
| 9:30–10:00 | `teacher@` (stretch) or API 403/404 demonstration | roles |
