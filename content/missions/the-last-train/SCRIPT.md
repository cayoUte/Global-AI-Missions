# THE LAST TRAIN — Screenplay

> Owner: `narrative-designer`. Status: **complete for review at G1** (Step A + Step B).
> Machine version: `mission.json` in this folder (37 nodes, 53 edges). Items: `items.json`, used exactly as written (prompts, stimuli and options are quoted verbatim below; answer keys are not shown). Backdrops: `docs/design/BACKDROPS.md` (the 8 keys of `docs/design/UI_SPEC.md` §6).
> Rules followed: PD-024 (1–3 short lines per narrative or consequence scene), MAYA.md §8 (no answers, no shaming, no game language), ASSESSMENT_SPEC §9 (story facts, no leaks before a checkpoint), A2–B1 British English outside the items.

**How to read §8.** Each checkpoint shows its scene, Maya's intro, the stimulus and the decision, then both branches: `_ok` (understood) and `_fail` (missed). Checkpoints 7, 8 and 10 also have `_rescue`, Maya's shortcut. Both branches go straight to the next checkpoint. *Variants* replace a scene's lines when a flag is set: the engine uses the first flag that matches, and `train_departed` always comes first. The planner shows the item's *hint* instead of Maya's intro only when the clock is tight (slack < 3).

---

## 1. Premise (intro node: 3 narrator lines plus Maya, about 55 words)

> **NARRATOR:** LONDON — 21:47. You have 18 minutes before the last train leaves.
> **NARRATOR:** It's the 22:05 to Oxford, the last train home tonight. Your flatmate Sam is waiting there.
> **NARRATOR:** Under the big station clock, a woman in a long scarf waves at you.
> **MAYA:** Hi, I'm Maya. I'm on the same train. Let's not run. Let's listen and read.

- **Stakes:** after 22:05 there's no train home, only a slow night bus.
- **Goal:** get to the train together.
- **Maya:** a translator who once stood in this station and couldn't understand a word. Tonight she travels with you.
- **Leaks avoided:** the intro shows a station clock, not a departures board, so nothing gives away the platform before checkpoint 2.

## 2. The shape of the night

The route goes deeper into the station as the clock runs down. Plan B takes it back out into the rain.

| # | Item | Decision in the story | Where | Backdrop | Who speaks |
|---|---|---|---|---|---|
| 1 | q01 grammar A1 | Ask the assistant the way | Station concourse | `concourse_night` | Station assistant |
| 2 | q02 listening A1 | Which platform did the announcer say? | Station concourse | `concourse_night` | Station announcer |
| 3 | q03 reading A2 | The office is closed: where do we buy tickets? | Ticket hall | `ticket_hall` | Notice on the glass |
| 4 | q04 vocabulary A2 | Which ticket does the assistant mean? | Ticket machines | `ticket_hall` | Station assistant |
| 5 | q05 grammar A2 | Apologise to the guard at the wrong gate | Ticket barriers | `concourse_night` | Guard |
| 6 | q06 grammar B1 | Tell the assistant how long you've been searching | The far gates | `concourse_night` | Station assistant |
| 7 | q07 listening B1 | What did the announcement about our train say? | Passage to the platforms | `platform` | Station announcer |
| 8 | q08 vocabulary B1 | What does the guard mean? | Side gate, platform 7 (Plan B: outside the station) | `platform` / `street_night` | Guard |
| 9 | q09 grammar B2 | Answer the passenger who sees you're out of breath | Platform 7 (Plan B: night bus stop) | `platform` / `night_bus` | Passenger |
| 10 | q10 reading B2 | What does Sam want you to do in Oxford? | At the train door (Plan B: night bus stop) | `platform` / `night_bus` | Message from Sam |

Why each listening and reading item happens in the story:
- q02: the evening announcement for the 22:05 train.
- q07: an announcement that stops you in the passage.
- q03: the notice taped to the closed ticket office.
- q10: a message from Sam that arrives just before you leave.

## 3. Flags (authored, 3)

| Flag | Set on | What it changes later |
|---|---|---|
| `wrong_platform` | `c02` **incorrect** | `c02_fail` happens on an empty far platform (`platform_empty`), where a cleaner gives the right number. `c06` becomes "First an empty platform, now a wall of gates…" with a Maya joke. `c07`: "This time you check every sign." |
| `wrong_ticket` | `c04` **incorrect** | `c05`: the ticket won't open the first barrier (it's the gate for platforms 1–4, not platform 7) and you start to worry. `c05_ok` / `c05_fail`: the guard says the ticket is fine, it's just the wrong gate. `c08`: you hold out the ticket from the machine. `c08_ok`: "Not the ticket I'd buy for one trip home. But it's valid." The misunderstanding gets noticed and fixed without any shaming. |
| `befriended_guard` | `c05` **correct** and `c08` **correct** | `c08` (if set at checkpoint 5): the same guard is waiting at the side gate ("Our friend from the barriers"). In `end_made_it` and `end_made_it_with_maya` the guard waves from the platform. |

`train_departed` is set automatically by the engine and isn't declared in `flags`. Where a node has several variants, the order is `train_departed`, then `befriended_guard`, then `wrong_ticket`.

## 4. Story-minutes

`minutes_available = 18` (21:47 → 22:05).

| Edge | Minutes | Notes |
|---|---|---|
| checkpoint → `_ok` (correct) | 1 | all 10 checkpoints |
| checkpoint → `_fail` (incorrect) | 3 | all 10 checkpoints: the detour happens in the fail scene (the long way round the shops, the empty platform, the queue, the long story…) |
| checkpoint → `_rescue` (incorrect, `rescue: true`) | 1 | **c07** (Maya knows the side gate), **c08** (Maya chats with the guard), **c10** (Maya holds the train door). Used at most once. The planner (CR-002) rescues only when the normal detour would lose the train and the rescue can still save it. |
| intro / `_ok` / `_fail` / `_rescue` → next checkpoint | 0 | |
| `c10_*` → endings | 0 | resolved by priority and condition |

| Path | Story-minutes | Final clock | Minutes left | Ending |
|---|---|---|---|---|
| **All correct** | **10** | 21:57 | 8 | made_it |
| 4 missed | 18 | 22:05 | 0 | made_it ("Departing now") |
| 4 missed, then a 5th at c07/c08/c10 with the rescue | 18–20 | 22:05 | ≥ 0 | made_it_with_maya |
| 5 missed (no rescue possible) | 20 | 22:07 | −2 | night_bus |
| All missed | 30 | 22:17 | −12 | night_bus (the 22:20 bus still fits) |

Validator (real output, see §7): **1,024 paths**, **10–30 story-minutes**. Paths per ending: made_it 386, made_it_with_maya 176, night_bus 462.

## 5. Plan B — the night bus to Oxford (`train_departed`)

The earliest the train can leave is right after checkpoint 7 (six misses in checkpoints 1–6 use all 18 minutes). **11 nodes** can be reached after that, and each has a `train_departed` variant, always listed first:

`c07_ok`, `c07_fail`, `c08`, `c08_ok`, `c08_fail`, `c09`, `c09_ok`, `c09_fail`, `c10`, `c10_ok`, `c10_fail`.

- **The moment it happens** (`c07_ok` / `c07_fail`, `platform_empty`): "Through the side gate, you see red lights. The last train is pulling away." Maya: "It's gone. But there's a night bus to Oxford at 22:20, just outside."
- **Checkpoints after departure** are always already on Plan B, so each one gets its own setting:
  - `c08`: outside the station in the rain (`street_night`). A guard is helping people from the last train, and Maya asks whether the train ticket works on the bus. The item's line "Hold on a minute. I'll just check your ticket." still fits exactly.
  - `c09`: stop B (`night_bus`). You're out of breath from running out of the station. The item only assumes that you ran.
  - `c10`: stop B. Sam's message arrives while you wait. The item is about arriving in Oxford by any means.
- **Consequence nodes from c08 on** can be the first scene after departure or a later one. Their variant lines work either way:
  - The guard says the ticket "works on the night bus to Oxford. Stop B, 22:20."
  - The passenger asks "Are you on the night bus to Oxford too?"
  - You text Sam "A bit later than planned!"
  - Maya's panel line: "No train for us tonight, but we have a plan: the 22:20 night bus to Oxford."
- **The bus:** a double-decker night bus **to Oxford** (not a red London bus, per UI_SPEC: "never red"), so the "top deck" line still works. The worst case (22:17) still catches the 22:20.
- **Rescue scenes** don't need a variant: a rescue always keeps the train catchable, and the validator doesn't list them.

## 6. Endings

| Priority | Key | Title | Condition | Backdrop | Maya's closing line |
|---|---|---|---|---|---|
| 1 | `made_it` | Made It | `min_minutes_left: 0`, `rescued: false` | `train_carriage` | "We made it! And you got us here." |
| 2 | `made_it_with_maya` | Made It Together | `min_minutes_left: 0`, `rescued: true` | `train_carriage` | "Good team. Next time, you show me a shortcut." |
| 3 | `night_bus` | The Night Bus | `{}` (fallback: the train has departed) | `night_bus` | "The train's gone, but this bus goes to the same place. Honestly? The top deck has the better view." |

None of the endings changes the score, and none of them sounds like a failure. Both train endings have a `befriended_guard` variant (the guard waves from the platform).

## 7. Validation and calibration (real outputs, 2026-09-24)

```
$ cd backend && uv run python scripts/validate_content.py
ok   content\missions\the-last-train\items.json
ok   content\missions\the-last-train\mission.json
ok   content\missions\the-last-train
content is valid

$ uv run python -m app.engine.cli validate --mission the-last-train
the-last-train: ok
  paths: 1024 | story-minutes: 10-30 | endings by path: made_it=386, made_it_with_maya=176, night_bus=462
  nodes reachable with train_departed: 11

$ uv run python -m app.engine.cli calibrate --mission the-last-train --profile all   (1,000 runs each)
A1                 made_it 10.6% | made_it_with_maya 14.4% | night_bus 75.0% | made the train 25.0%   (target ≤ 30%: met)
A2                 made_it 58.5% | made_it_with_maya 21.1% | night_bus 20.4% | made the train 79.6%   (target 50–80%: met)
B1                 made_it 96.0% | made_it_with_maya  2.9% | night_bus  1.1% | made the train 98.9%   (target ≥ 85%: met)
B2                 made_it 99.9% | made_it_with_maya  0.1% | night_bus  0.0% | made the train 100.0%
A2_weak_listening  made_it 40.3% | made_it_with_maya 25.2% | night_bus 34.5% | made the train 65.5%
```

Every target is met with the default costs (correct 1, incorrect 3, rescue 1), so no minutes were changed.

**Pace (PD-024).** Every path has 22 screens: the intro, 10 checkpoints, 10 consequences and 1 ending. Narrative and consequence scenes have 1–3 lines, and each Maya line is 1–2 short sentences. Outside the items, a path is about 640 words of story text (every checkpoint understood) to 770 (every checkpoint missed), counting scene lines, Maya's intros and reactions. A practised presenter clicking through at about 10 s per scene and 15–20 s per checkpoint needs about 4–5 minutes. A first-time learner who reads everything and listens twice needs about 8–10 minutes.

## 8. The screenplay, node by node

### `intro` — narrative · Station concourse · `concourse_night`

> **NARRATOR:** LONDON — 21:47. You have 18 minutes before the last train leaves.
> **NARRATOR:** It's the 22:05 to Oxford, the last train home tonight. Your flatmate Sam is waiting there.
> **NARRATOR:** Under the big station clock, a woman in a long scarf waves at you.
> **MAYA (panel):** Hi, I'm Maya. I'm on the same train. Let's not run. Let's listen and read.
> *Diary:* At 21:47 we met under the station clock, eighteen minutes before the last train to Oxford.

### `c01` — checkpoint 1 · `q01` (multiple_choice · grammar · A1) · Station concourse · `concourse_night`

> **NARRATOR:** The concourse is huge and full of people. Which way are the platforms?
> **NARRATOR:** A station assistant is standing by the information point.
> **MAYA (intro):** Let's ask her. A short, polite question is all we need.
> **[DIALOGUE — Station assistant]** "Good evening. Can I help you?"
> **DECISION:** Ask the assistant: '___ this the way to the platforms?'
> (a) Is · (b) Are · (c) Does · (d) Do
> *Hint (planner, only when slack < 3):* Say it as a statement first: 'This ... the way.' Then turn it into a question.
> *Diary:* We asked a station assistant the way to the platforms.

- **reaction_ok:** Nice question. Short and clear.
- **reaction_fail:** She got the idea, I think. The start of the question sounded a bit unusual.

#### `c01_ok` — understood (+1 min) · Station concourse · `concourse_night`

> **STATION ASSISTANT:** Yes, it is. Straight on, then left. They'll announce your platform soon.
> **MAYA (panel):** Good. Now we just need a platform number.
> *Diary:* The assistant understood us at once and sent us straight on.

#### `c01_fail` — missed (+3 min) · Station concourse · `concourse_night`

> **NARRATOR:** She needs a moment to understand. You try again, and she points the way.
> **NARRATOR:** You go the long way round the shops first.
> **MAYA (panel):** The scenic route. We still have time.
> *Diary:* The assistant needed a second try, and we took the long way round the shops.

### `c02` — checkpoint 2 · `q02` (multiple_choice · listening · A1) · Station concourse · `concourse_night`

> **NARRATOR:** A soft bell rings. The whole concourse goes quiet to listen.
> **MAYA (intro):** That's the announcer. Let's catch every word about our train.
> **[LISTEN — Station announcer, rate 0.85]** *"Good evening. The twenty-two oh five train to Oxford is now at platform seven. That's platform seven for the twenty-two oh five to Oxford."* (not shown as text before answering)
> **DECISION:** Which platform does the announcer say?
> (a) Platform 5 · (b) Platform 7 · (c) Platform 11 · (d) Platform 17
> *Hint (planner, only when slack < 3):* You will hear two numbers. Listen for the word 'platform' and the number right after it.
> *Diary:* We listened to the announcement for our train.

- **reaction_ok:** Good ears. You caught it first time.
- **reaction_fail:** Hm. There were two numbers in that. Let's make sure we have ours.

#### `c02_ok` — understood (+1 min) · Station concourse · `concourse_night`

> **NARRATOR:** Platform seven. You and Maya turn towards the gates.
> **MAYA (panel):** Wait. Tickets. We haven't got tickets yet.
> *Diary:* We caught the platform number: seven.

#### `c02_fail` — missed (+3 min, sets `wrong_platform`) · The far platform · `platform_empty`

> **NARRATOR:** You hurry to a platform at the far end. It's empty and cold.
> **CLEANER:** Oxford? That's platform seven, love. And you'll need tickets.
> **MAYA (panel):** Platform seven. Thank you! First, tickets.
> *Diary:* We went to an empty platform first. A cleaner told us: platform seven.

### `c03` — checkpoint 3 · `q03` (comprehension · reading · A2) · Ticket hall · `ticket_hall`

> **NARRATOR:** The ticket office window is dark. A notice is taped to the glass.
> **MAYA (intro):** The office is closed. Let's see what the notice says about tonight.
> **[NOTICE — Station notice]** "TICKET OFFICE / The ticket office closes at 21:30 tonight. / After 21:30, please buy your ticket from the machines next to the main entrance. They take cards and cash. / If the machines are not working, you can buy a ticket from the guard on the train."
> **DECISION:** It's after 21:30. Where should you try to buy your ticket first?
> (a) At the ticket office · (b) From the machines next to the main entrance · (c) From the guard on the train · (d) From the staff at the ticket barriers
> *Hint (planner, only when slack < 3):* Find the time in the notice first. Then read what it tells you to do after that time.
> *Diary:* We read the notice on the closed ticket office.

- **reaction_ok:** Good reading. The notice had a plan for us.
- **reaction_fail:** Hm. I think the time on that notice matters.

#### `c03_ok` — understood (+1 min) · Ticket hall · `ticket_hall`

> **NARRATOR:** The machines next to the main entrance glow blue. There's no queue.
> **MAYA (panel):** Lucky us. Let's go.
> *Diary:* We went straight to the ticket machines by the main entrance.

#### `c03_fail` — missed (+3 min) · Ticket hall · `ticket_hall`

> **NARRATOR:** You look for someone to sell you a ticket, but nobody can.
> **MAN BY THE WINDOW:** Machines, mate. Next to the main entrance.
> **MAYA (panel):** Back to the entrance. Now we know.
> *Diary:* We looked in the wrong place first, then found the machines by the main entrance.

### `c04` — checkpoint 4 · `q04` (vocabulary · vocabulary · A2) · Ticket machines · `ticket_hall`

> **NARRATOR:** The machine shows a long list of tickets. A station assistant comes over to help.
> **MAYA (intro):** So many buttons. Let's think about our trip tonight.
> **[DIALOGUE — Station assistant]** "So you're going home to Oxford tonight, and you're not coming back to London? Then you need a ticket for one journey only."
> **DECISION:** Which ticket does the assistant mean?
> (a) A single · (b) A return · (c) A season ticket · (d) A railcard
> *Hint (planner, only when slack < 3):* Count the journeys. How many times will you travel, and in which direction?
> *Diary:* We chose our tickets at the machines.

- **reaction_ok:** That's the one for tonight. Let's pay.
- **reaction_fail:** Hm. I'm not sure that's the ticket she meant. Let's see.

#### `c04_ok` — understood (+1 min) · Ticket machines · `ticket_hall`

> **NARRATOR:** The machine prints two singles to Oxford.
> **MAYA (panel):** One journey, one ticket. Now, the gates.
> *Diary:* We bought single tickets to Oxford.

#### `c04_fail` — missed (+3 min, sets `wrong_ticket`) · Ticket machines · `ticket_hall`

> **NARRATOR:** The machine asks more questions. You press back, then next, then back again.
> **NARRATOR:** At last it prints your ticket. The assistant raises an eyebrow, but the queue is waiting.
> **MAYA (panel):** Let's keep it and see what happens.
> *Diary:* We bought a ticket, but not the one the assistant meant.

### `c05` — checkpoint 5 · `q05` (fill_blank · grammar · A2) · Ticket barriers · `concourse_night`

> **NARRATOR:** You go to the first barriers you see and put your ticket in. Red light.
> **NARRATOR:** A guard walks over. He doesn't look happy.
> **MAYA (intro):** He's pointing at a sign. Let's say sorry, nice and clearly.
> **[DIALOGUE — Guard]** "This gate is only for platforms one to four. The sign is right there."
> **DECISION:** Sorry, I ___ (not see) it when I came in.
> (type the missing words)
> *Hint (planner, only when slack < 3):* Look at the time words at the end of the sentence. Is it now, or a finished time?
> *Diary:* At the first barriers we found, a guard stopped us.

*Variant `wrong_ticket`*:

> **NARRATOR:** You push your new ticket into the first barrier. Red light. Again. Red light.
> **NARRATOR:** A guard walks over. You look at your ticket and start to worry.
> **MAYA (panel):** Maybe it's the ticket. Maybe not. Let's listen first.
> *Diary:* Our ticket didn't open the first barrier, and a guard came over.

- **reaction_ok:** Nice apology. Look, he's smiling now.
- **reaction_fail:** He heard the 'sorry', I think. The rest got a bit lost.

#### `c05_ok` — understood (+1 min, sets `befriended_guard`) · Ticket barriers · `concourse_night`

> **GUARD:** No harm done. Platform seven's through the far gates.
> **NARRATOR:** He nods at you both and taps his radio. He'll remember you.
> **MAYA (panel):** A friend in the station. That helps.
> *Diary:* We apologised to the guard, and he sent us to the far gates with a smile.

*Variant `wrong_ticket`*:

> **GUARD:** No harm done. Your ticket's fine. It was just the wrong gate.
> **NARRATOR:** He points to the far gates and gives you a friendly nod.
> **MAYA (panel):** So it was the gate, not the ticket. Good.
> *Diary:* We apologised, and the guard told us our ticket was fine: wrong gate, not wrong ticket.

#### `c05_fail` — missed (+3 min) · Ticket barriers · `concourse_night`

> **NARRATOR:** The guard explains again, more slowly. A queue grows behind you.
> **NARRATOR:** At last he points to the far gates, and you squeeze out of the line.
> **MAYA (panel):** Far gates. We're getting closer.
> *Diary:* The guard had to explain twice, and we left the queue for the far gates.

*Variant `wrong_ticket`*:

> **NARRATOR:** The guard checks your ticket and explains again, slowly: wrong gate, not wrong ticket.
> **NARRATOR:** A queue grows behind you. You squeeze out towards the far gates.
> *Diary:* The guard explained twice: our ticket was okay, but we were at the wrong gate.

### `c06` — checkpoint 6 · `q06` (fill_blank · grammar · B1) · The far gates · `concourse_night`

> **NARRATOR:** More gates, more signs, more people. Which one is yours?
> **NARRATOR:** A station assistant sees your faces and comes over.
> **MAYA (intro):** She wants to help. Let's tell her our problem.
> **[DIALOGUE — Station assistant]** "You two look lost. Can I help?"
> **DECISION:** Yes, please. We ___ (look) for platform seven since we arrived.
> (type the missing words)
> *Hint (planner, only when slack < 3):* Notice the word 'since'. The search started in the past. Has it finished, or is it still going on?
> *Diary:* A station assistant saw that we were lost.

*Variant `wrong_platform`*:

> **NARRATOR:** First an empty platform, now a wall of gates. You still can't see a seven.
> **NARRATOR:** A station assistant sees your faces and comes over.
> **MAYA (panel):** This station really likes hiding our platform.

- **reaction_ok:** That told her the whole story in one sentence.
- **reaction_fail:** She got the idea. The time part came out a bit mixed up.

#### `c06_ok` — understood (+1 min) · The far gates · `concourse_night`

> **STATION ASSISTANT:** Since you arrived? You poor things. Platform seven is down that passage.
> **MAYA (panel):** Down the passage. Let's move.
> *Diary:* The assistant understood we'd been searching for ages and sent us down the passage.

#### `c06_fail` — missed (+3 min) · The far gates · `concourse_night`

> **NARRATOR:** The assistant thinks you've just arrived. She starts from the beginning: the map, the shops, the toilets.
> **NARRATOR:** Maya thanks her politely. Then you both walk fast.
> **MAYA (panel):** Kind woman. Very long map.
> *Diary:* The assistant thought we'd just arrived and gave us the full tour.

### `c07` — checkpoint 7 · `q07` (multiple_choice · listening · B1) · Passage to the platforms · `platform`

> **NARRATOR:** The passage under the tracks is long and loud. The speakers crackle again.
> **MAYA (intro):** It's about our train again. Let's hear the whole message.
> **[LISTEN — Station announcer, rate 1.0]** *"Passengers for the twenty-two oh five to Oxford: the barriers for platform seven are out of order. Please show your ticket to a member of staff at the side gate, next to the lift."* (not shown as text before answering)
> **DECISION:** What did the announcement say?
> (a) The barriers were out of order, so passengers should show their tickets to staff at the side gate. · (b) The barriers were working again, so passengers could go straight through. · (c) The side gate was closed, so passengers should take the lift to the platform. · (d) Passengers should buy new tickets from a member of staff by the lift.
> *Hint (planner, only when slack < 3):* Listen for the problem first, then for what passengers must do. Some words in the options are in the announcement too.
> *Diary:* In the passage, we heard an announcement about our train.

*Variant `wrong_platform`*:

> **NARRATOR:** The passage under the tracks is long and loud. This time you check every sign.
> **NARRATOR:** The speakers crackle again.

- **reaction_ok:** Good ears. That was fast, and you got all of it.
- **reaction_fail:** We heard our train, I think. What to do was less clear.
- **reaction_rescue:** Don't worry. I know this station. Stay close.

#### `c07_ok` — understood (+1 min) · Side gate, platform 7 · `platform`

> **NARRATOR:** At the end of the passage, the platform seven barriers are dark.
> **NARRATOR:** Next to the lift, a small side gate is open. A guard stands there.
> **MAYA (panel):** Side gate. Just like the announcement said.
> *Diary:* We went straight to the side gate by the lift.

*Variant `train_departed`* (Side gate, platform 7 · `platform_empty`):

> **NARRATOR:** Through the side gate, you see red lights. The last train is pulling away.
> **MAYA (panel):** It's gone. But there's a night bus to Oxford at 22:20, just outside.
> *Diary:* We reached the side gate just as the last train pulled away. Plan B: the night bus.

#### `c07_fail` — missed (+3 min) · Side gate, platform 7 · `platform`

> **NARRATOR:** You wait at the dark barriers and push your ticket in. Nothing. Again. Nothing.
> **MAN BEHIND YOU:** Side gate, mate. Next to the lift.
> **MAYA (panel):** The side gate. Let's go.
> *Diary:* We tried the dark barriers until a man sent us to the side gate by the lift.

*Variant `train_departed`* (Side gate, platform 7 · `platform_empty`):

> **MAN BEHIND YOU:** Side gate, mate. Next to the lift.
> **NARRATOR:** Through the side gate, you see red lights. The last train is pulling away.
> **MAYA (panel):** It's gone. But there's a night bus to Oxford at 22:20, just outside.
> *Diary:* We tried the dark barriers too long, and the last train pulled away. Plan B: the night bus.

#### `c07_rescue` — Maya's shortcut (rescue, +1 min) · Maya's shortcut · `arcade_shortcut`

> **NARRATOR:** Maya pulls you past the dark barriers, straight to a small gate by the lift.
> **NARRATOR:** Ten seconds later, you're at the front of the line.
> **MAYA (panel):** Old station trick. Side gate, by the lift.
> *Diary:* Maya knew a quick way to the side gate by the lift.

### `c08` — checkpoint 8 · `q08` (vocabulary · vocabulary · B1) · Side gate, platform 7 · `platform`

> **NARRATOR:** A guard stands at the side gate. You walk up with your ticket in your hand.
> **MAYA (intro):** He's friendly, but he wants something from us. What is it?
> **[DIALOGUE — Guard]** "Hold on a minute. I'll just check your ticket."
> **DECISION:** What does the guard mean by 'Hold on a minute'?
> (a) Wait for a moment. · (b) Hold your ticket up high. · (c) Walk on quickly. · (d) Keep your ticket safe for later.
> *Hint (planner, only when slack < 3):* A phrasal verb often means something different from its two words. Think about the whole phrase, not just 'hold'.
> *Diary:* At the side gate, a guard stopped us to check our tickets.

*Variant `train_departed`* (Outside the station · `street_night`):

> **NARRATOR:** Outside, it's raining. A guard in a bright jacket is helping people from the last train.
> **NARRATOR:** You show him your train ticket.
> **MAYA (panel):** Sometimes train tickets work on the night bus. Let's ask him.
> *Diary:* Outside the station, a guard helped people who had missed the last train.

*Variant `befriended_guard`*:

> **NARRATOR:** At the side gate, a familiar face: the guard from the first barriers. He came down in the lift.
> **MAYA (panel):** Look who it is. Our friend from the barriers.
> *Diary:* At the side gate, we met the friendly guard again.

*Variant `wrong_ticket`*:

> **NARRATOR:** A guard stands at the side gate. You hold out the ticket from the machine.
> **MAYA (panel):** Let's show him our tickets and see.

- **reaction_ok:** Nice. You read him perfectly.
- **reaction_fail:** Hm, I think 'hold' tricked us a little.
- **reaction_rescue:** Leave this to me. I'll talk to him.

#### `c08_ok` — understood (+1 min, sets `befriended_guard`) · Side gate, platform 7 · `platform`

> **NARRATOR:** You wait. He checks your ticket, smiles and opens the gate.
> **GUARD:** Platform seven. Go on, quickly.
> **MAYA (panel):** He likes you. I can tell.
> *Diary:* We waited while the guard checked our tickets, and he let us through.

*Variant `train_departed`* (Outside the station · `street_night`):

> **NARRATOR:** You wait while he checks your ticket.
> **GUARD:** This works on the night bus to Oxford. Stop B, 22:20.
> **MAYA (panel):** No train for us tonight, but we have a plan: the 22:20 night bus to Oxford.
> *Diary:* The guard checked our tickets: they worked on the night bus to Oxford.

*Variant `wrong_ticket`*:

> **NARRATOR:** You wait. He looks at your ticket for a long second.
> **GUARD:** Not the ticket I'd buy for one trip home. But it's valid. Go on.
> **MAYA (panel):** Phew. It works. Let's go.
> *Diary:* The guard checked our ticket: not the best one for tonight, but valid.

#### `c08_fail` — missed (+3 min) · Side gate, platform 7 · `platform`

> **GUARD:** Just wait there for me, please.
> **NARRATOR:** He checks two other tickets before yours. Then he waves you through.
> **MAYA (panel):** Slow and steady. We're nearly there.
> *Diary:* The guard had to ask us twice to wait while he checked the tickets.

*Variant `train_departed`* (Outside the station · `street_night`):

> **GUARD:** Just wait there for me, please.
> **NARRATOR:** He checks the whole queue first. Then: 'Fine on the night bus. Stop B, 22:20.'
> **MAYA (panel):** No train for us tonight, but we have a plan: the 22:20 night bus to Oxford.
> *Diary:* The guard asked us twice to wait, then told us our tickets worked on the night bus.

#### `c08_rescue` — Maya's shortcut (rescue, +1 min) · Maya's shortcut · `arcade_shortcut`

> **NARRATOR:** Maya chats with the guard. He laughs, checks both tickets at once and opens the gate.
> **MAYA (panel):** He's from Oxford too. Small world. Come on.
> *Diary:* Maya chatted with the guard, and he let us through quickly.

### `c09` — checkpoint 9 · `q09` (multiple_choice · grammar · B2) · Platform 7 · `platform`

> **NARRATOR:** Platform seven. The train is here, doors open, lights on.
> **NARRATOR:** A woman with a bike looks at you both and laughs.
> **MAYA (intro):** Catch your breath first. Then answer her.
> **[DIALOGUE — Passenger]** "You're both out of breath! Did you run all the way here?"
> **DECISION:** Answer the passenger: 'Yes! If we ___ earlier, we wouldn't have had to run.'
> (a) had left · (b) would have left · (c) left · (d) have left
> *Hint (planner, only when slack < 3):* Read the second half of the sentence first. It tells you the time and the kind of 'if' sentence.
> *Diary:* On the platform, a passenger noticed we were out of breath.

*Variant `train_departed`* (Night bus stop · `night_bus`):

> **NARRATOR:** At stop B, the sign says: Oxford, 22:20. You're both breathing hard.
> **NARRATOR:** A woman in the queue looks at you and laughs.
> *Diary:* At the night bus stop, a woman noticed we were out of breath.

- **reaction_ok:** Lovely sentence. And very true.
- **reaction_fail:** She got the idea. That 'if' sentence got a little tangled.

#### `c09_ok` — understood (+1 min) · Platform 7 · `platform`

> **PASSENGER:** Story of my life. The front carriages are quieter.
> **NARRATOR:** You walk to the front of the train together.
> **MAYA (panel):** Front carriage. Nearly home.
> *Diary:* We joked with a passenger about leaving too late.

*Variant `train_departed`* (Night bus stop · `night_bus`):

> **PASSENGER:** Story of my life. Are you on the night bus to Oxford too? Sit upstairs, at the front.
> **MAYA (panel):** No train for us, but the top deck sounds good.
> *Diary:* We joked with a passenger about leaving too late. She told us to sit upstairs.

#### `c09_fail` — missed (+3 min) · Platform 7 · `platform`

> **PASSENGER:** Sorry? Oh, I know the feeling!
> **NARRATOR:** She tells you a long story about her own last train. You listen politely as the minutes go.
> **MAYA (panel):** Nice woman. Long story.
> *Diary:* A passenger told us a long story about her own last train.

*Variant `train_departed`* (Night bus stop · `night_bus`):

> **PASSENGER:** Sorry? Oh, I know the feeling!
> **NARRATOR:** She tells you a long story about the night she missed her last train. You listen politely.
> **MAYA (panel):** No train for us tonight, but we have a plan: the 22:20 night bus to Oxford.
> *Diary:* A passenger told us a long story about the night she missed her last train.

### `c10` — checkpoint 10 · `q10` (comprehension · reading · B2) · At the train door · `platform`

> **NARRATOR:** Your phone buzzes. It's a long message from Sam, your flatmate in Oxford.
> **MAYA (intro):** Sam writes a lot. Let's read the whole thing, calmly.
> **[MESSAGE — From: Sam]** "Change of plan, sorry! I've been held up at work and there's no way I'll be finished before midnight. Please don't wait around outside when you get to Oxford: it's freezing, and that part of town isn't exactly lively at night. The Night Owl café on George Street stays open late, and Rosa, who runs it, knows you're coming. I'll head over there the moment I'm done. Our flat's only a short walk from the café, so we can walk back together."
> **DECISION:** What does Sam want you to do when you get to Oxford?
> (a) Wait outside until Sam finishes work. · (b) Go to the café on George Street and wait for Sam there. · (c) Walk to the flat and wait at the door. · (d) Go to Sam's work and meet there.
> *Hint (planner, only when slack < 3):* The plan is not in one sentence. Read to the end and put the pieces together.
> *Diary:* At the train door, Sam sent us a long message about the plan in Oxford.

*Variant `train_departed`* (Night bus stop · `night_bus`):

> **NARRATOR:** While you wait for the bus, your phone buzzes. It's a long message from Sam.
> *Diary:* At the bus stop, Sam sent us a long message about the plan in Oxford.

- **reaction_ok:** Nice reading. Sam's plan is a good one.
- **reaction_fail:** Hm. I don't think that's Sam's plan. Let's read the end again.
- **reaction_rescue:** Reply later. Get on, the doors are closing!

#### `c10_ok` — understood (+1 min) · At the train door · `platform`

> **NARRATOR:** You text back: 'See you at the Night Owl. Say hi to Rosa.'
> **NARRATOR:** Maya holds the door, and you step on.
> **MAYA (panel):** The Night Owl? I love that place.
> *Diary:* We understood Sam's plan: wait at the Night Owl café with Rosa.

*Variant `train_departed`* (Night bus stop · `night_bus`):

> **NARRATOR:** You text back: 'See you at the Night Owl. A bit later than planned!'
> **MAYA (panel):** Same café, just later. Sam won't mind.
> *Diary:* We understood Sam's plan and texted that we'd be a bit late.

#### `c10_fail` — missed (+3 min) · At the train door · `platform`

> **NARRATOR:** You start to reply. Maya reads over your shoulder and points at the last lines.
> **NARRATOR:** You read it again, slowly: George Street, the café, Rosa. Now the plan makes sense.
> **NARRATOR:** Behind you, the doors start to beep.
> **MAYA (panel):** Got it now? Quick, let's get on.
> *Diary:* We read Sam's message twice before the plan made sense: the café on George Street.

*Variant `train_departed`* (Night bus stop · `night_bus`):

> **NARRATOR:** You start to reply. Maya reads over your shoulder and points at the last lines.
> **NARRATOR:** You read it again, slowly: George Street, the café, Rosa. Now the plan makes sense.
> **MAYA (panel):** Same café, just later. Sam won't mind.
> *Diary:* We read Sam's message twice before the plan made sense: the café on George Street.

#### `c10_rescue` — Maya's shortcut (rescue, +1 min) · At the train door · `platform`

> **NARRATOR:** Maya holds the door open with one hand.
> **NARRATOR:** You look once more: the café on George Street, Rosa, Sam. Now it makes sense.
> **MAYA (panel):** Read it again on the train. In you get.
> *Diary:* Maya held the train door while we read Sam's message again.

### Endings

#### `end_made_it` — **Made It** (`made_it`, priority 1, condition `{"min_minutes_left": 0, "rescued": false}`) · On the 22:05 to Oxford · `train_carriage`

> **NARRATOR:** You find two seats by the window. At 22:05 exactly, the doors close.
> **NARRATOR:** London slides past, one light at a time.
> **MAYA (closing):** We made it! And you got us here.
> *Diary:* We caught the last train to Oxford.

*Variant `befriended_guard`*:

> **NARRATOR:** You find two seats by the window. At 22:05 exactly, the doors close.
> **NARRATOR:** On the platform, the guard lifts his hand. You wave back.
> **NARRATOR:** London slides past, one light at a time.
> *Diary:* We caught the last train to Oxford, and the guard waved us off.

#### `end_made_it_with_maya` — **Made It Together** (`made_it_with_maya`, priority 2, condition `{"min_minutes_left": 0, "rescued": true}`) · On the 22:05 to Oxford · `train_carriage`

> **NARRATOR:** You jump on. The doors close right behind you.
> **NARRATOR:** Maya drops into a seat, laughing and out of breath.
> **MAYA (closing):** Good team. Next time, you show me a shortcut.
> *Diary:* We caught the last train together, thanks to Maya's shortcut.

*Variant `befriended_guard`*:

> **NARRATOR:** You jump on. The doors close right behind you.
> **NARRATOR:** On the platform, the guard lifts his hand. You wave back.
> **NARRATOR:** Maya drops into a seat, laughing and out of breath.
> *Diary:* We caught the last train together, thanks to Maya's shortcut, and the guard waved us off.

#### `end_night_bus` — **The Night Bus** (`night_bus`, priority 3, condition `{}`) · The night bus to Oxford · `night_bus`

> **NARRATOR:** At 22:20, the night bus to Oxford comes out of the rain.
> **NARRATOR:** You take the front seats on the top deck. London is all lights.
> **MAYA (closing):** The train's gone, but this bus goes to the same place. Honestly? The top deck has the better view.
> *Diary:* The last train left without us, so we took the night bus to Oxford together.

## 9. Maya — generic mood lines (`companion.mood_lines`)

The engine falls back to these when a node has no Maya line of its own. Every node in this mission has one, so in practice they show up only in rare engine fallbacks. None of them names an option. There's deliberately no "Look at that board…" line, because a board could show the platform before checkpoint 2 (ASSESSMENT_SPEC §9).

| Mood | Lines |
|---|---|
| curious | "Look around. What do you notice first?" · "Hm. Which way do you think?" · "Listen. The station is talking to us." |
| encouraging | "That's fine. We can fix this on the way." · "Take a breath. You understood most of it." · "One step at a time. We still have time." |
| worried | "The clock is moving. Let's think carefully." · "Okay. Focus with me for a second." · "We're a little late. One thing at a time." |
| proud | "You did that on your own." · "Look at you, reading London like a local." · "Nice. You didn't even need me there." |

## 10. Leak check (ASSESSMENT_SPEC §9)

- No departures board and no "Platform 7" before `c02`. `c01_ok` says only "They'll announce your platform soon".
- No "out of order" before `c07`. At `c05` the barrier shows a red light because it's the wrong gate. `c07`'s scene says only that the speakers crackle.
- No "single" before `c04`. It first appears in `c04_ok`.
- Nothing explains "hold on" before `c08`. The meaning only comes out in `c08_fail` ("Just wait there for me, please.").
- Maya's intros tell the student what to pay attention to. The item's hint appears only when the planner decides `hint`.
