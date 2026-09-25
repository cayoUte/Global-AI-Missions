# THE LAST TRAIN — Screenplay (DRAFT, Step A)

> Owner: `narrative-designer`. Status: **Step A draft** — the item-independent parts of the story (premise, Maya's voice, flags, endings, Plan B, the shape of the night, minutes). The ten checkpoint scenes, the ok/fail consequences and Maya's per-checkpoint lines are written in Step B, around `items.json` exactly as the assessment-designer wrote it.
> Machine version: `mission.json` (same folder; not written yet). Backdrops: `docs/design/BACKDROPS.md`.
> Rules followed: PD-024 (1–3 short lines per narrative/consequence scene, ≤ 5 min for a practised presenter), MAYA.md §8 (no answers, no shaming, no game language), A2–B1 British English outside the items.

---

## 1. Premise (intro node, 3 lines, 58 words incl. Maya)

> **NARRATOR:** LONDON — 21:47. You have 18 minutes before the last train leaves.
> **NARRATOR:** It is the last train home tonight. After 22:05 there is only the slow night bus.
> **NARRATOR:** Under the departures board, a young woman in a long scarf waves at you.
> **MAYA (line):** Hi, I'm Maya. I'm on the same train. Let's not run — let's read.

Stakes: miss 22:05 and the night is long. Goal: reach the platform together. Maya: a translator who once stood in this station and understood nothing; tonight she travels with you.

---

## 2. The shape of the night (location sequence)

The station gets deeper and quieter as the clock runs down. Plan B turns out into the rain.

| Stage | Location | Backdrop | Checkpoints (planned, confirmed in Step B) | CEFR band (blueprint) |
|---|---|---|---|---|
| Arrival | Station concourse | `concourse_night` | intro, 1 | A1 |
| Tickets | Ticket hall | `ticket_hall` | 2, 3 | A1 → A2 |
| A pause | Late café | `station_cafe` | 4 | A2 |
| The gate | Ticket barriers | `ticket_barriers` | 5, 6 | A2 → B1 |
| Under the tracks | Passage to the platforms | `station_passage` | 7, 8 | B1 |
| The train | The platform | `platform_night` | 9, 10 | B2 |
| Home | On the train | `train_carriage` | endings made_it / made_it_with_maya | — |
| Plan B | Outside the station → bus stop | `station_exit_rain` → `bus_stop_night` | `train_departed` variants (checkpoint 7 consequences onward) | — |
| Plan B home | Top deck of the night bus | `night_bus_deck` | ending night_bus | — |

Listening items are motivated by what London stations really do at night: the departures announcement, a guard's radio, the platform announcer. Reading items are things you really read while hurrying: a message on your phone, a notice taped to a barrier, a timetable.

---

## 3. Flags (authored; max 3)

| Flag | Set on | What it changes later |
|---|---|---|
| `wrong_ticket` | the **incorrect** edge of the ticket-buying checkpoint | At the ticket barriers the ticket does not open the gate: the scene shows the red light and the guard waving you over (a chance to repair it by talking). Diary line mentions the ticket. |
| `wrong_platform` | the **incorrect** edge of the platform-announcement (listening) checkpoint | The next scene happens at the far, empty platform (`platform_far`); Maya notices the number on the sign and turns you round. The platform scenes mention the long walk back. |
| `befriended_guard` | the **correct** edge of the checkpoint where you talk to the guard | The guard remembers you: on the platform he waves and holds the door a second longer; in the `made_it` endings he nods through the window. A warm reward for understanding a person, not a point. |

`train_departed` is automatic (engine sets it when `minutes_left < 0`); it is **not** declared in `flags`. Variants on a node are checked in order, `train_departed` first, then the authored flag variants.

---

## 4. Story-minutes (path cost)

- Start 21:47, departure 22:05 → `minutes_available = 18`.
- Every checkpoint edge: **correct = 1**, **incorrect = 3**. Every `always` edge (narrative/consequence → next checkpoint) = **0**. Ending edges = 0.
- **Rescue** edges (Maya's shortcut, at most once): **1** minute, only on `incorrect`, proposed on checkpoints **8, 9, 10** (the passage and the platform, where Maya knows a shortcut or talks to someone). Confirmed in Step B.

| Path | Minutes | Clock at the end | Left | Ending |
|---|---|---|---|---|
| All correct | 10 | 21:57 | 8 | made_it |
| 4 incorrect | 18 | 22:05 | 0 | made_it ("Departing now") |
| 5 incorrect | 20 | 22:07 | −2 | night_bus |
| 10 incorrect | 30 | 22:17 | −12 | night_bus (the 22:20 bus still fits) |

When the train can first be gone: `minutes_left = 19 − k − 2·(misses so far)` before checkpoint k. With at most k−1 misses before checkpoint k, `minutes_left < 0` first becomes possible **after checkpoint 7** (six misses in 1–6 = 18 min, then any answer at 7). So every node from the checkpoint 7 consequences onward (c07_ok, c07_fail, c08 … c10 and their consequences, rescue scenes) carries a `train_departed` variant. The rescue can only happen when 0–2 minutes are left and the normal detour would miss the train, i.e. from checkpoint 7 on.

---

## 5. Plan B — the night bus (after `train_departed`)

The idea: the train does not wait, but the night does not end. At the first node after departure, the scene moves outside:

> **NARRATOR:** Through the gate you see it: the last train, pulling away.
> **MAYA:** Okay. It's gone. But the 22:20 night bus goes home too. Come on — it's just outside.

From then on, the remaining checkpoints happen **on the way to and at the bus stop** (`station_exit_rain`, `bus_stop_night`). Each checkpoint's variant re-motivates its item for the bus:

- a listening item becomes the station speakers still audible from the street, or the bus stop's talking timetable;
- a reading item becomes the notice on the bus shelter or a message on the phone;
- a grammar or vocabulary item becomes what you say to the driver, to a person in the queue, or what Maya asks you to check.

Tone: never "you failed". Maya says "we", makes a small joke, and the night bus ending is as warm as the train ending. The clock label reads "Train departed — Plan B" (server-side, F-06).

---

## 6. Endings

Chosen by the engine from the state (lower priority wins among matching conditions). The ending never changes the score.

| Priority | Key | Title | Condition | Backdrop |
|---|---|---|---|---|
| 1 | `made_it` | Made It | `min_minutes_left: 0`, `rescued: false` | `train_carriage` |
| 2 | `made_it_with_maya` | Made It Together | `min_minutes_left: 0`, `rescued: true` | `train_carriage` |
| 3 | `night_bus` | The Night Bus | `{}` (fallback; reached when the train has departed) | `night_bus_deck` |

### made_it — "Made It"
> **NARRATOR:** The doors close behind you. The train pulls out into the dark.
> **NARRATOR:** London slides past the window, one light at a time.
> **MAYA (closing):** We made it! And you got us here. I just carried the scarf.
> *Variant `befriended_guard`:* **NARRATOR:** On the platform, the guard from the barriers lifts his hand. You wave back.
> *Diary:* We caught the last train with time to spare.

### made_it_with_maya — "Made It Together"
> **NARRATOR:** You jump on. The doors close a second later.
> **NARRATOR:** Maya laughs and sits down, out of breath.
> **MAYA (closing):** Good team. Next time, you show me a shortcut.
> *Variant `befriended_guard`:* same guard wave line.
> *Diary:* We caught the last train together, thanks to Maya's shortcut.

### night_bus — "The Night Bus"
> **NARRATOR:** The red bus comes out of the rain at 22:20.
> **NARRATOR:** You take the front seats on the top deck. The city is all lights.
> **MAYA (closing):** The train's gone, but this bus goes to the same place. Honestly? The top deck has the better view.
> *Diary:* We missed the train, so we took the night bus home together.

---

## 7. Maya — generic mood lines (`companion.mood_lines`)

Used by the engine when a node has no specific Maya line. ≤ 2 sentences, ≤ 12 words each, no option ever named.

| Mood | Lines |
|---|---|
| curious | "Look at that board. What do you notice first?" · "Hm. Which way do you think?" · "Listen. The station is talking to us." |
| encouraging | "That's fine. We can fix this on the way." · "Take a breath. You understood most of it." · "One step at a time. We still have time." |
| worried | "The clock is moving. Let's think carefully." · "Okay. Focus with me for a second." · "We're a little late. One thing at a time." |
| proud | "You did that on your own." · "Look at you, reading London like a local." · "Nice. You didn't even need me there." |

---

## 8. Checkpoints (Step B — pending `items.json`)

For each of the ten checkpoints, Step B adds, in item order:
- the checkpoint scene (1–3 lines that make the decision a situation, plus the item's stimulus and prompt exactly as written),
- Maya's `intro` (what to pay attention to, never the answer), `reaction_ok`, `reaction_fail` (item-specific), and `reaction_rescue` on 8–10,
- `cNN_ok` and `cNN_fail` consequences (1–3 lines; the fail scene shows the misunderstanding and, where possible, lets the next scene repair it), and `cNN_rescue` on 8–10,
- the `train_departed` variant on every node from `c07_ok` onward, and flag variants where they apply.

Target size: intro + 10 checkpoints + 20 consequences + 3 rescue scenes + 3 endings = **37 nodes** (the brief's 30–35 target plus the three rescue scenes the engine needs as separate targets).
