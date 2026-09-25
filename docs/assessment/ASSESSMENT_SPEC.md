# ASSESSMENT SPEC — The Last Train

> Owner: `assessment-designer`. Sources above this file: `docs/agents/SHARED_CONTEXT.md` §4 and §12, `docs/contracts/items.schema.json`, `docs/contracts/api-contract.md` §0 and §7.
> Items: `content/missions/the-last-train/items.json`. After G1 the items, and the rules in this file, change only through `docs/contracts/CHANGE_REQUESTS.md`: the graph, the seed and the tests depend on them.
> The backend implements `services/grading.py` and `services/leveling.py` **exactly** as written in §3–§5. The engine's `normalize_answer` (`backend/app/engine/transition.py`) implements §6.

---

## 1. Blueprint

The items rise in CEFR level with the story clock. Types, skills and levels match SHARED_CONTEXT §4 exactly: 4 multiple choice (2 grammar, 2 listening), 2 fill in the blank (grammar), 2 comprehension (reading), 2 vocabulary. The levels are A1 ×2, A2 ×3, B1 ×3 and B2 ×2.

| id | type | skill | cefr | Language point | Why this level |
|---|---|---|---|---|---|
| q01 | multiple_choice | grammar | A1 | Question with *be*: "**Is** this the way to the platforms?" | Inverting *be* in a yes/no question, with singular *this*, is one of the first structures taught at A1. The distractors test do-support overgeneralization and agreement. |
| q02 | multiple_choice | listening | A1 | Numbers in a slow, repeated announcement (platform 7 versus the time 22:05) | A1 learners can catch numbers and times in slow, clear speech that is repeated (rate 0.85, the key fact said twice). |
| q03 | comprehension | reading | A2 | A short notice with a time and a condition (*after 21:30*, *if the machines are not working*) | A2 learners can find specific, predictable information in simple everyday notices. The 45-word text uses A2 vocabulary. |
| q04 | vocabulary | vocabulary | A2 | Travel tickets: *single* versus *return* | Buying transport tickets is a core A2 topic. The distractor *return* catches the typical "going home = return" error. |
| q05 | fill_blank | grammar | A2 | Past simple negative (*didn't see*) with finished time (*when I came in*) | The past simple and its negative with *did* are core A2 grammar. |
| q06 | fill_blank | grammar | B1 | Present perfect (continuous) with *since* + a past-simple clause | Present perfect versus present or past simple with *since* is a classic B1 contrast and a frequent L1-transfer error (*we look since…*). |
| q07 | multiple_choice | listening | B1 | A natural-speed announcement: a problem, an instruction and a location, with the options in reported speech | B1 learners can follow the main points and detailed instructions of clear public announcements at normal speed (rate 1.0). They must filter out words that appear in the audio but are not the instruction (*lift*, *barriers*). |
| q08 | vocabulary | vocabulary | B1 | Phrasal verb with an idiomatic meaning: *hold on* = *wait* | Common non-literal phrasal verbs are B1 vocabulary. The distractors test literal readings of *hold*. |
| q09 | multiple_choice | grammar | B2 | Third conditional: "If we **had left** earlier, we wouldn't have had to run." | The third conditional (unreal past) is B2 grammar. *would have* after *if* is the most common B2 error. |
| q10 | comprehension | reading | B2 | Inference and implied meaning across sentences in an informal 82-word message (*held up*, *isn't exactly lively*, *head over there*) | B2 readers understand implied meaning and informal idiom. The plan (wait at the café) is never stated in one sentence. |

Per-skill spread: grammar A1 · A2 · B1 · B2 (4 items); listening A1 · B1; reading A2 · B2; vocabulary A2 · B1.
Per-level item counts (`n_L`): A1 = 2, A2 = 3, B1 = 3, B2 = 2.

Content facts (checked by script): each listening `audio_script` has 15–35 words (q02 = 24, q07 = 34), with `rate` 0.85 at A1 and 1.0 at B1. The reading texts have 30–60 words at A2 (q03 = 45) and 60–100 at B2 (q10 = 82). Every choice item has 4 options with unique ids and unique texts, and its key is among them. Each fill_blank prompt has exactly one `___`, and its accepted answers are stored already normalized (§6) and de-duplicated.

---

## 2. Definitions

- **Item outcome**: `correct` or `incorrect`. The outcome is decided once, when the answer is locked, by `grade(item, answer)` (§3). No item is ever unanswered: every checkpoint needs a decision to continue and there is no skip (PD-011). A submitted attempt therefore always has exactly 10 outcomes, one per item id.
- **Scored skills**, in fixed display order: `grammar, listening, reading, vocabulary`. `speaking` is never scored in this mission. It is reported only through `unmeasured_skills: ["speaking"]`.
- **Level order** (rank): `PRE_A1 < A1 < A2 < B1 < B2 < C1`. Display label: `PRE_A1` → `Pre-A1`. Every other code displays unchanged.
- `n_L` = the number of items tagged with level `L` in this mission's `items.json`. `c_L` = how many of them are correct. `n_s` and `c_s` are the same counts for skill `s`. Always count from the item tags; never hard-code the counts.

---

## 3. Grading (`grade`)

| Item type | Correct if and only if |
|---|---|
| `multiple_choice`, `comprehension`, `vocabulary` | the submitted `option_id` equals `answer_key.correct_option_id` (exact string comparison) |
| `fill_blank` | `normalize(text)` (§6) is equal to one of `normalize(a)` for `a` in `answer_key.accepted` |

- Each item is worth 1 point. There is no partial credit and no penalty beyond the lost point.
- **Hints never change the score.** Neither does Maya's rescue, the ending reached, the story-minutes used, `train_departed`, how many times a listening item was replayed, or the time taken. Hints and rescue are only recorded (`attempt_record.hints_received`, `rescue_used`).
- `grade` is pure and deterministic. Re-grading the stored raw answers must give the same outcomes as the stored ones. Submit aggregates the stored outcomes and never changes them.

---

## 4. Scoring

**Percentages.** Every percentage is an integer from 0 to 100, **rounded half up** from `100 × c / t` (api-contract §0). Compute it with integer arithmetic only. Do not use floats or Python's `round()`, which rounds half to even.

```
pct(c, t) = (200 * c + t) // (2 * t)          # t > 0; integer floor division
```

Checks: `pct(1,3) = 33`, `pct(2,3) = 67`, `pct(1,8) = 13` (12.5 rounds up), `pct(7,10) = 70`, `pct(3,4) = 75`.

| Field | Rule |
|---|---|
| `total` | 10 (the number of items) |
| `correct` | the number of items whose outcome is correct |
| `incorrect` | `total − correct`. `correct + incorrect = 10` always. |
| `score_pct` (global %) | `pct(correct, 10)`. With 10 items this is always `10 × correct`. |
| per skill `s` | `{ skill, correct: c_s, total: n_s, pct: pct(c_s, n_s) }`, listed in the fixed order grammar, listening, reading, vocabulary. Here grammar has `n_s = 4` and the other skills have `n_s = 2`. |
| report `label` | `"{display(suggested_cefr)} · The Last Train — {score_pct}%"`, e.g. `A2 · The Last Train — 70%`. The separators are U+00B7 (·) and U+2014 (—), each with one space on both sides. |

Values the per-skill % can take: grammar 0, 25, 50, 75 or 100; listening, reading and vocabulary 0, 50 or 100.

---

## 5. Suggested level (`leveling`)

### 5.1 Rule

1. **Base level** from the integer `score_pct`:

   | score_pct | 0–29 | 30–49 | 50–69 | 70–84 | 85–100 |
   |---|---|---|---|---|---|
   | base | PRE_A1 | A1 | A2 | B1 | B2 |

   With 10 items, the reachable values are 0 to 20 → Pre-A1, 30 to 40 → A1, 50 to 60 → A2, 70 to 80 → B1 and 90 to 100 → B2. (85 cannot be reached.)

2. **Evidence cap.** Start with `L = base`. While `L ≠ PRE_A1`:
   - `required_L = ceil(n_L / 2)`, computed in integers as `(n_L + 1) // 2`. Here A1 needs 1 of 2, A2 needs 2 of 3, B1 needs 2 of 3 and B2 needs 1 of 2.
   - Append `{cefr: L, correct: c_L, total: n_L, required: required_L, met: c_L >= required_L}` to `evidence`.
   - If `met`, stop: the suggested level is `L`. Otherwise set `L` to the next lower level and repeat.
   - A level with `n_L = 0` is never met: append the entry with `total: 0, required: 0, met: false`. (This never happens in this mission. The rule is here for future missions.)
   - `PRE_A1` needs no evidence and is never appended.
3. **Ceiling.** This mission can suggest at most **B2**. C1 needs another mission. The band table already stops at B2.

Output (api-contract §7): `suggested_level = { cefr, base_cefr, reason, evidence }`. `evidence` lists every level checked, top-down. It is empty when the base is Pre-A1. When the final level is Pre-A1 after stepping down, every entry has `met: false`.

**Properties with this blueprint** (useful as test oracles):
- A B2 base (≥ 90%, so at most one item incorrect) always meets B2's 1-of-2 check. The cap never lowers B2.
- A B1 base (70–80%, 2–3 incorrect) can step down at most once, to A2. If B1 fails, at least 2 of the incorrect items are B1 items, so A2 has at least 2 of 3 correct.
- An A2 base (50–60%) can step down to A1 or, with 4 incorrect items spread over both A1 items and two A2 items, all the way to Pre-A1 (example 6).
- An A1 base (30–40%) falls to Pre-A1 when both A1 items are incorrect.

### 5.2 Level-reason sentence (`suggested_level.reason`, PD-015)

`D(x)` is the display label. `word(n)` is `checkpoint` when `n = 1` and `checkpoints` otherwise. The dash is U+2014 with one space on each side. Build exactly one of these three shapes:

| Case | Template |
|---|---|
| Base is Pre-A1 | `"{score_pct}% points to Pre-A1, so your suggested level is Pre-A1."` |
| Base check met (no step down) | `"{score_pct}% points to {D(base)}. {D(L)} needs {required} of {total} {D(L)} {word(total)} — you had {correct} — so your suggested level is {D(L)}."` (L = base) |
| One or more checks failed | `"{score_pct}% points to {D(base)}. " + " and ".join(clause(e) for e in failed) + " so your suggested level is {D(final)}."`, where `clause(e) = "{D(e.cefr)} needs {e.required} of {e.total} {D(e.cefr)} {word(e.total)} — you had {e.correct} —"` and `failed` holds the evidence entries with `met: false`, in the order they were checked. The final met entry, if any, is not narrated. |

The third shape reproduces the contract example exactly: `70% points to B1. B1 needs 2 of 3 B1 checkpoints — you had 1 — so your suggested level is A2.`

### 5.3 Worked examples

Items by level: A1 = q01, q02 · A2 = q03, q04, q05 · B1 = q06, q07, q08 · B2 = q09, q10.
Items by skill: grammar = q01, q05, q06, q09 · listening = q02, q07 · reading = q03, q10 · vocabulary = q04, q08.
Every row below was computed with the formulas in §4 and §5 by a script, and checked by hand. Strength and challenge follow §7.1.

| # | Scenario | Incorrect items | Correct / Incorrect | score_pct | Base | Evidence (checked top-down) | Suggested | Grammar · Listening · Reading · Vocabulary | Strength / Challenge |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Clean run | none | 10 / 0 | 100 | B2 | B2 2/2, needs 1 → met | **B2** | 4/4=100 · 2/2=100 · 2/2=100 · 2/2=100 | grammar / listening |
| 2 | **Slip on an A1 item** by a strong student | q02 | 9 / 1 | 90 | B2 | B2 2/2, needs 1 → met | **B2** | 4/4=100 · 1/2=50 · 2/2=100 · 2/2=100 | grammar / listening |
| 3 | Contract example (api-contract §7) | q07, q08, q09 | 7 / 3 | 70 | B1 | B1 1/3, needs 2 → not met; A2 3/3, needs 2 → met | **A2** | 3/4=75 · 1/2=50 · 2/2=100 · 1/2=50 | reading / listening |
| 4 | **Lucky B2 guess** by an A2 student | q06, q07, q09 | 7 / 3 | 70 | B1 | B1 1/3, needs 2 → not met; A2 3/3, needs 2 → met | **A2** | 2/4=50 · 1/2=50 · 2/2=100 · 2/2=100 | reading / grammar |
| 5 | Solid B1 | q07, q09 | 8 / 2 | 80 | B1 | B1 2/3, needs 2 → met | **B1** | 3/4=75 · 1/2=50 · 2/2=100 · 2/2=100 | reading / listening |
| 6 | Inverted pattern (misses the basics, gets the hard items) | q01, q02, q04, q05 | 6 / 4 | 60 | A2 | A2 1/3, needs 2 → not met; A1 0/2, needs 1 → not met | **Pre-A1** | 2/4=50 · 1/2=50 · 2/2=100 · 1/2=50 | reading / grammar |
| 7 | Beginner with evidence | q01, q05, q07, q08, q09, q10 | 4 / 6 | 40 | A1 | A1 1/2, needs 1 → met | **A1** | 1/4=25 · 1/2=50 · 1/2=50 · 1/2=50 | listening / grammar |
| 8 | Pre-A1 base | q02, q03, q05, q06, q07, q08, q09, q10 | 2 / 8 | 20 | Pre-A1 | (none) | **Pre-A1** | 1/4=25 · 0/2=0 · 0/2=0 · 1/2=50 | vocabulary / listening |
| 9 | **Slips on both A1 items** at the bottom of the A1 band | q01, q02, q05, q07, q08, q09, q10 | 3 / 7 | 30 | A1 | A1 0/2, needs 1 → not met | **Pre-A1** | 1/4=25 · 0/2=0 · 1/2=50 · 1/2=50 | reading / listening |

Reason sentences, exactly as the server must build them:

1. `100% points to B2. B2 needs 1 of 2 B2 checkpoints — you had 2 — so your suggested level is B2.`
2. `90% points to B2. B2 needs 1 of 2 B2 checkpoints — you had 2 — so your suggested level is B2.`
3. `70% points to B1. B1 needs 2 of 3 B1 checkpoints — you had 1 — so your suggested level is A2.`
4. `70% points to B1. B1 needs 2 of 3 B1 checkpoints — you had 1 — so your suggested level is A2.`
5. `80% points to B1. B1 needs 2 of 3 B1 checkpoints — you had 2 — so your suggested level is B1.`
6. `60% points to A2. A2 needs 2 of 3 A2 checkpoints — you had 1 — and A1 needs 1 of 2 A1 checkpoints — you had 0 — so your suggested level is Pre-A1.`
7. `40% points to A1. A1 needs 1 of 2 A1 checkpoints — you had 1 — so your suggested level is A1.`
8. `20% points to Pre-A1, so your suggested level is Pre-A1.`
9. `30% points to A1. A1 needs 1 of 2 A1 checkpoints — you had 0 — so your suggested level is Pre-A1.`

What the examples show:
- **Example 2 (A1 slip):** one slip on an easy item does not lower a strong student. The cap only looks at the items of the level being claimed, so a missed A1 item never caps B2.
- **Example 4 (lucky B2 guess):** a correct guess on q10 lifts an A2 student into the B1 band (70%). The cap then asks for B1 evidence (1 of 3) and steps the level back down to A2. A lucky guess on a harder item cannot buy a level the student has not shown at that level.
- **Example 6:** the cap can step down twice. A 60% result built on missed A1 and A2 items is not trusted as A2 evidence.
- **Examples 3 and 4** reach the same level and sentence from different item patterns. The per-skill results and strength/challenge still differ.

Report labels for the examples: `B2 · The Last Train — 100%`, `B2 · The Last Train — 90%`, `A2 · The Last Train — 70%` (×2), `B1 · The Last Train — 80%`, `Pre-A1 · The Last Train — 60%`, `A1 · The Last Train — 40%`, `Pre-A1 · The Last Train — 20%`, `Pre-A1 · The Last Train — 30%`.

---

## 6. Fill-blank normalization (`normalize`)

One function, `normalize_answer` in `backend/app/engine/transition.py`, is shared by request validation (AnswerRequest `text`: 1–80 characters **after** normalization) and by grading. Accepted answers in `items.json` are already stored in normalized form, and normalizing them again changes nothing. The steps run in this order:

1. **Straighten apostrophes.** Replace U+2018 (‘), U+2019 (’) and U+02BC (ʼ) with U+0027 (').
2. **Lowercase** with Python's `str.lower()`.
3. **Trim and collapse spaces** with `" ".join(text.split())`. Every run of whitespace (spaces, tabs, newlines, other Unicode whitespace) becomes one space, and leading and trailing whitespace is removed.
4. **Strip final punctuation.** Remove every trailing character from the set `. , ! ? ; : …` (U+2026) with `rstrip(".,!?;:…")`, then remove trailing whitespace again with `rstrip()`.

Nothing else changes: no spelling correction, no removal of inner punctuation or quotes, and no Unicode normalization of letters. Normalization runs once. It is not repeated until the text stops changing.

| Typed | Normalized | q05 / q06 outcome |
|---|---|---|
| `  Didn’t   SEE. ` | `didn't see` | q05 correct |
| `did not see!!` | `did not see` | q05 correct |
| `didnt see` | `didnt see` | q05 correct (the missing apostrophe is a typing slip, not a grammar error) |
| `DID\tNOT\nSEE` | `did not see` | q05 correct |
| `don't see` | `don't see` | q05 incorrect |
| `Have been looking ?` | `have been looking` | q06 correct |
| `’ve LOOKED` | `'ve looked` | q06 correct |
| `are looking` | `are looking` | q06 incorrect |
| `have been looking for` | `have been looking for` | q06 incorrect (the blank holds only the verb form; `for` is already in the sentence) |
| `have been. !` | `have been.` | (only the last run of punctuation is stripped) |
| `...` | `` (empty) | rejected with 422 `VALIDATION_ERROR` before any lock (api-contract §5.10). Never graded. |

Accepted answers (the **first one is displayed** as `correct_answer` in the report's missed checkpoints):

| Item | accepted (in order) | Displayed |
|---|---|---|
| q05 | `didn't see`, `did not see`, `didnt see` | didn't see |
| q06 | `have been looking`, `'ve been looking`, `have looked`, `'ve looked` | have been looking |

Deliberately **not** accepted: q05 `haven't seen` / `hadn't seen` (wrong tense with *when I came in*), `don't see`, `did not saw`, `didn't saw`. q06 `are looking`, `looked`, `were looking`, `had been looking`, `has been looking`, and answers that repeat the subject (`we've been looking`), because the prompt already shows *We*.

---

## 7. Interpretation templates

These are used by the deterministic mock / fallback coach (`app/ai/mock_provider.py`) and given to the LLM as the reference register. All the English is A2-readable. None of them uses: wrong, fail, mistake, careless, easy, points, XP, level up, or exclamation chains (MAYA.md §8).

### 7.1 Deterministic strength and challenge

The report's `interpretation.strength` and `interpretation.challenge` must always equal these values (SHARED_CONTEXT §6). They are computed from the four scored skills of the attempt:

- **strength** = the skill with the highest `pct`. Ties go to the higher `correct` count, then to the fixed display order (grammar, listening, reading, vocabulary).
- **challenge** = chosen from the **other three** skills: the one with the lowest `pct`. Ties go to the higher incorrect count (`total − correct`), then to the fixed display order.

Strength and challenge are therefore always different skills, even when every skill has the same %. Check with the contract example (grammar 75, listening 50, reading 100, vocabulary 50): strength = reading. Listening and vocabulary tie at 50 with 1 incorrect each, so display order makes listening the challenge. This matches api-contract §7. The fallback `next_mission_id` maps the challenge to a mission (PD-010).

### 7.2 Can-do statement per suggested level

| Suggested level | Can-do statement |
|---|---|
| Pre-A1 | You can understand some very common words and numbers when people speak slowly and clearly. |
| A1 | You can understand simple signs, numbers and short questions, like asking the way in a station. |
| A2 | You can read short notices and messages and do simple travel tasks, like buying the right ticket. |
| B1 | You can follow clear announcements and explain what happened to you, even when plans change. |
| B2 | You can understand what people mean even when they don't say it directly, and talk about what could have happened. |

### 7.3 Skill bands

The band is chosen from the integer skill `pct`: **strong** ≥ 75 · **developing** 50–74 · **focus** < 50.

| Skill | strong (≥ 75%) | developing (50–74%) | focus (< 50%) |
|---|---|---|---|
| grammar | You build clear sentences, even with tricky verb forms. | Your sentences mostly work. Some verb forms still need care. | Verb forms are slowing you down. Short, clear sentences come first. |
| listening | You catch numbers and details in announcements. | You get the main idea when people speak. Some details slip past. | Conversations are moving faster than you are. |
| reading | You read signs, notices and messages quickly and well. | You understand most of what you read. Small details, like times and "if", can trip you up. | Written notices are hard for now. Read slowly and look for the key words. |
| vocabulary | You recognize common vocabulary quickly. | You know many everyday words. Phrases with two meanings are still tricky. | New words are your next step. Learn travel words in small groups. |

### 7.4 Recommendation per challenge skill (for the mock's `recommendation`)

| Challenge | Recommendation |
|---|---|
| grammar | Say one sentence about your day each evening, and check the verb. |
| listening | Listen for numbers first, then names. Play short announcements twice. |
| reading | Read the whole notice once, then look for times and the word "if". |
| vocabulary | Learn words in pairs that go together, like "single" and "return". |

**Suggested assembly for the mock `summary`** (the ai-coach-engineer owns the final shape): the can-do statement for the suggested level, then the strong line of the strength skill, then the line of the challenge skill for its own band. For example 3: "You can read short notices and messages and do simple travel tasks, like buying the right ticket. You read signs, notices and messages quickly and well. You get the main idea when people speak. Some details slip past."

---

## 8. Item-review checklist (run on every item)

Checks: **C1** exactly one defensible correct answer · **C2** plausible, diagnostic distractors (each one maps to a typical learner error) · **C3** language at the tagged level (stimulus and options are no harder than the construct) · **C4** the hint is a strategy that neither names nor eliminates an option · **C5** answerable from the stimulus and prompt alone (listening only from the audio) · **C6** original, natural British English, set in the mission · **C7** schema and integrity (validator plus self-check). It also stays meaningful whether or not the train has departed (items after checkpoint 7).

| Item | C1 | C2 — distractor → error it diagnoses | C3 | C4 | C5 | C6 | C7 | Result |
|---|---|---|---|---|---|---|---|---|
| q01 | ✓ | *Are* → agreement pulled by *platforms*; *Does*/*Do* → do-support overgeneralized to *be* | ✓ A1 | ✓ strategy (make the statement, then invert) | ✓ | ✓ | ✓ | **Pass** |
| q02 | ✓ | *5* → takes the time "oh five" for the platform; *11* → seven/eleven; *17* → seven/seventeen | ✓ A1, rate 0.85, key fact repeated | ✓ | ✓ only from the audio (the number never appears in the prompt or options as a word) | ✓ | ✓ 24 words | **Pass** |
| q03 | ✓ | *ticket office* → misses "closes"; *guard on the train* → ignores the "if" condition; *staff at the barriers* → a plausible guess not in the text | ✓ A2, 45 words | ✓ | ✓ | ✓ | ✓ | **Pass** |
| q04 | ✓ ("one journey only") | *return* → "going home = return"; *season ticket* → confuses time words; *railcard* → a discount card, not a ticket | ✓ A2 | ✓ | ✓ the definition is in the stimulus. The construct is the word meaning. | ✓ | ✓ | **Pass** |
| q05 | ✓ all forms listed | open item. Expected errors: *don't see*, *haven't seen*, *didn't saw* | ✓ A2 | ✓ | ✓ the verb cue *(not see)* is given | ✓ | ✓ one `___`, answers normalized | **Pass** |
| q06 | ✓ both present-perfect forms accepted | open item. Expected errors: *are looking* (L1 transfer), *looked*, *had been looking* | ✓ B1 | ✓ | ✓ the verb cue *(look)* is given | ✓ | ✓ one `___`, answers normalized | **Pass** |
| q07 | ✓ | *working again* → misses "out of order"; *side gate closed / take the lift* → latches on to *lift*; *buy new tickets* → misparses "show your ticket to a member of staff" | ✓ B1, rate 1.0. All options use equally correct reported speech, so grammar alone cannot answer it. | ✓ | ✓ only from the audio | ✓ | ✓ 34 words | **Pass** |
| q08 | ✓ (the prompt asks about the phrase, not about "what to do", so *show ticket* readings are excluded) | *Hold your ticket up* / *Keep your ticket safe* → literal *hold*; *Walk on quickly* → confuses *hold on* with *go on* | ✓ B1 | ✓ | ✓ | ✓ works in both branches (a guard checks tickets at the station) | ✓ | **Pass** |
| q09 | ✓ | *would have left* → *would* after *if*; *left* → second-conditional form; *have left* → present perfect | ✓ B2 | ✓ | ✓ | ✓ works in both branches (they ran either way) | ✓ | **Pass** |
| q10 | ✓ inference is unique: *head over there* = the café, and Rosa expects you | *wait outside* → misses "don't wait around outside"; *walk to the flat* → misreads "short walk"; *go to Sam's work* → latches on to "held up at work" | ✓ B2, 82 words | ✓ | ✓ | ✓ works in both branches ("when you get to Oxford", not "the station") | ✓ | **Pass** |

Result: **10 / 10 items pass.** Known and accepted limits:
- q04 and q08 are short and focused: each one measures a single lexical point.
- q02 and q07 audio reaches the browser (SHARED_CONTEXT §9 trade-off). Retaking after reading the report is practice, not re-assessment.
- q05 accepts `didnt see`, because the construct is the past simple negative, not punctuation.

---

## 9. Story facts the items fix (for the narrative-designer)

The items are fixed. Scenes wrap them and must not contradict them or give away an answer before its checkpoint.

- The train: **the 22:05 to Oxford**, **platform 7**. The student is going **home to Oxford**, one way, tonight. The London station is not named in any item.
- Ticket office closed (it closes at 21:30). Ticket machines are **next to the main entrance** (cards and cash).
- A gate "only for platforms one to four" (q05, the student is at the wrong gate).
- The **barriers for platform 7 are out of order**. Tickets are shown at the **side gate next to the lift** (q07).
- **Sam** is the student's flatmate in Oxford. Sam has been held up at work. Sam wants the student to wait at the **Night Owl café on George Street**, run by **Rosa** (q10).
- Speakers the scenes must provide: Station assistant (q01, q04, q06), Station announcer (q02, q07), Guard (q05, q08), a Passenger (q09), a phone message from Sam (q10), a printed notice (q03).
- **No leaks before a checkpoint:** no visible departure board or sign showing "Platform 7" before q02, no "out of order" sign before q07, no mention of *single* before q04, and no line that says *hold on* means *wait* before q08. Consequence scenes after a checkpoint may reveal what happened.
- **Plan B:** q08–q10 are written to make sense whether or not `train_departed` is set. q09 assumes only that the student and Maya ran. q10 is about arriving in Oxford by any means (a night bus reaches "the same place").
- **Alignment with SCRIPT.md Step A:** "the last train home" and "the night bus goes to the same place" both fit, because home is Oxford. A *red* London bus does not go to Oxford, though. Make Plan B an all-night coach or night bus **to Oxford** (a double-decker keeps the "top deck" line). Suggested checkpoint locations: q03 in the ticket hall (notice), q04 at the machines (not the café), q05 and q06 at the ticket barriers, q07 and q08 in the passage (announcement, then staff at the side gate), q09 and q10 on the platform. Flags: `wrong_ticket` fits the incorrect edge of **q04** (a return, a season ticket or a railcard is not the ticket for tonight). `wrong_platform` fits the incorrect edge of **q02**. `befriended_guard` fits the correct edge of **q05** or **q08** (both are the Guard). The platform-7 barriers are out of order (q07). If the `wrong_ticket` variant shows a barrier rejecting the ticket, put it at the gate for platforms 1–4 (q05), not at platform 7. The generic curious mood line "Look at that board…" must not be used at c02, because a board could show the platform.
