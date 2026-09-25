# Story graph engine

A mission is a **state-space search problem**. This package models it with the standard library
only (no FastAPI, SQLAlchemy, pydantic or I/O except `cli.py`), deterministically. Services
import from `app.engine` only; the public API is documented in `__init__.py`.

## Classic search concepts in the code

| Concept | Where | In The Last Train |
|---|---|---|
| Agent (human) | the student, through the API | perceives the scene, chooses an option or types |
| Agent (Maya) | `maya.decide` | perceives the state, acts: `quiet`, `hint`, `rescue` |
| Simulated agent | `simulator.SimulatedStudent` | a stochastic policy `P(correct \| skill, cefr)` per profile |
| State `s` | `state.State` | `(node_id, minutes_left, flags, rescued, maya_mood)`, frozen |
| Initial state | `state.initial_state` | `start_node`, `minutes_available`, no flags, `curious` |
| `ACTIONS(s)` | `transition.actions` | a checkpoint's option ids, one `type` template for fill-blank, `CONTINUE` elsewhere, none at an ending |
| `RESULT(s, a)` | `transition.result` → `advance` | grades (the only reader of answer keys), picks the edge, applies minutes, flag effects, the automatic `train_departed`, Maya's rescue, the mood and ending resolution |
| Goal test | `transition.is_goal` | `kind == "ending"` (three goal nodes) |
| Path cost | `Edge.minutes` | story-minutes: correct 1, detour 3, rescue 1 |
| Node (state, parent, action, cost) | persisted step (backend) → `diary.StepRecord` | following the parent pointers back from the ending **is** the Diary (`diary.build_diary`) |
| Frontier | `heuristic.compute_h` (priority queue), `validator` (BFS queue, DFS stack) | |
| Explored set | `h` dict in `compute_h`, `explored` in the validator's BFS | the path DFS has none on purpose: it must enumerate every path |
| Heuristic `h(n)` | `heuristic.compute_h` | exact minimum story-minutes to an ending over non-rescue edges, computed once by Dijkstra on the reversed graph |
| Admissible | `h(n) ≤ true cost-to-go` | it is the minimum over all non-rescue paths (every remaining answer correct); rescue edges are never cheaper than correct edges. Tested on all 1,024 paths |
| Consistent | `h(n) ≤ c(n, n′) + h(n′)` | shortest-path distances satisfy the triangle inequality. Tested on every non-rescue edge |

## Maya the planner

`slack = minutes_left − h(node)`: the minutes to spare if every remaining answer is correct.

- **On arrival at a checkpoint:** `slack < 3` → `hint` (the item's strategy line, never the answer), else `quiet`.
- **After an incorrect answer:** `rescue` when the train has not departed, no rescue was used, a rescue edge exists, **the normal detour would lose the train even with perfect play from there** (`minutes_left − c_detour − h(detour) < 0`) and the rescue keeps it catchable (`minutes_left − c_rescue − h(rescue) ≥ 0`). This one-step lookahead refines §5's literal "the detour would make `minutes_left < 0`", so Maya never spends her one rescue on a train that is lost anyway (CR-001).
- **Mood FSM** (`next_mood`), after each answer: incorrect → `worried` if `slack < 3` else `encouraging`; correct → `encouraging` if `slack < 3` or she was `worried` (worry recovers gradually), else `proud`. Starts `curious`.
- **Lines:** reaction = `reaction_rescue` / `reaction_ok` / `reaction_fail`, else a mood line. StateView line = the hint on `hint`, else the variant's or node's Maya line (`intro` on checkpoints), else a mood line.
- No minimax or alpha-beta: Maya and the student cooperate, there is no adversary. No machine learning.

## Validator (`validator.validate`)

Content integrity (3–4 options with unique ids, `correct_option_id` among them; fill-blank with `options: null`, ≥ 1 non-empty accepted answer and exactly one `___`; duplicates after normalization are warnings; every item on exactly one checkpoint) → BFS reachability, edge shape per node kind, declared flags, no dead ends → Kahn's topological sort (no cycles) → DFS over every outcome path: the same 10 checkpoints in the same order, the 4/2/2/2 type × skill blueprint, CEFR `A1 A1 A2 A2 A2 B1 B1 B1 B2 B2`, a Plan-B (`train_departed`) variant on every non-ending node reachable after departure, path count, min/max story-minutes and paths per ending.

```
uv run python -m app.engine.cli validate            # every folder in content/missions
uv run python -m app.engine.cli calibrate --profile all
uv run python -m app.engine.cli simulate --profile B1 --seed 7
```

## Calibration

Informational run (not a gate), 1,000 seeded runs per profile (seeds 0–999). `P(correct)` depends
on the gap between the item's CEFR and the profile's: −3: 0.97 · −2: 0.95 · −1: 0.90 · 0: 0.75 ·
+1: 0.45 · +2: 0.25 · +3: 0.12; `A2_weak_listening` is A2 with −0.30 on listening.

**Mission: `_fixture`** (the real `the-last-train` is not written yet; rerun after G1 and adjust
edge minutes once). 18 minutes available; edges: correct 1, detour 3, rescue 1 (from checkpoint
7 on). **1,024 paths**, **10–30 story-minutes**; paths per ending: made_it 386, made_it_with_maya
246, night_bus 392. 11 nodes are reachable after departure; the earliest is right after
checkpoint 7.

| Profile | made_it | made_it_with_maya | night_bus | made the train | §5 target |
|---|---|---|---|---|---|
| A1 | 10.6% | 17.7% | 71.7% | 28.3% | ≤ 30% (met) |
| A2 | 58.5% | 24.9% | 16.6% | 83.4% | 50–80% (3.4 points above) |
| B1 | 96.0% | 3.5% | 0.5% | 99.5% | ≥ 85% (met) |
| B2 | 99.9% | 0.1% | 0.0% | 100.0% | — |
| A2_weak_listening | 41.4% | 28.9% | 29.7% | 70.3% | — |

Thresholds and why: `hint` at `slack < 3` (§5): 3 minutes is one detour, so Maya starts helping
exactly when one more miss would cost the train. The rescue lookahead uses the same `h`. The
A2 deviation is documented, not fixed: tightening the fixture's clock would change the
walking-skeleton numbers the other engineers test against, and the real mission gets its own
one-time minute adjustment.
