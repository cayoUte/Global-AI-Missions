# BACKDROPS — The Last Train

> Owner: `narrative-designer`. Readers: `ux-ui-designer` (art direction), `frontend-engineer` (key → `backdrops.css`), `story-graph-engineer`.
> **Reconciled with `docs/design/UI_SPEC.md` §6.** `mission.json` uses only the 8 keys the frontend already renders. An unknown key falls back to `concourse_night`, so there are no other keys. Every `scene.backdrop` and `variants[].backdrop` in `content/missions/the-last-train/mission.json` is one of the keys below.

The night has one shape. The route goes **deeper into the station** as the clock runs down: concourse → ticket hall → barriers → passage → platform → train. Plan B goes the other way, **out into the rain**: the street, then the night bus stop, then the top deck.

| Key | One-line visual description | Mood | Used by (mission.json) |
|---|---|---|---|
| `concourse_night` | A big Victorian station at night: train-shed ribs, an arcade of closed shops, a hanging clock, warm amber light high in the centre. The departures board is never readable. | Expectant, busy, a little overwhelming | `intro`; checkpoints 1–2 and their consequences (except `c02_fail`); checkpoints 5–6 at the ticket barriers and the far gates, with their consequences |
| `ticket_hall` | Ticket machines glowing cool blue on the left, the dark ticket office window with a notice on the glass on the right, a short queue. | Fluorescent, practical, slightly anxious | checkpoints 3–4 (notice, machines) and their consequences |
| `platform` | A platform under a canopy, sodium lamps, the amber safety line, rails. The `location` names the exact place (passage, side gate, platform 7, train door). | Urgent, hopeful | checkpoints 7–10 and their consequences on the train path; `c10_rescue` (Maya holds the door) |
| `platform_empty` | The same platform with one dim lamp and a darker sky: empty, calm, not grim. | Lonely, quiet | `c02_fail` (the far, empty platform: `wrong_platform`); `train_departed` variants of `c07_ok` / `c07_fail` (the train pulls away) |
| `arcade_shortcut` | Closer on the station arcade, shop glow and Maya's warm peach light: the way only a local knows. | Teamwork, relief | `c07_rescue` (Maya's route to the side gate), `c08_rescue` (Maya talks the guard round) |
| `street_night` | Outside the station in light rain: generic rooftops, a dome and a spire, lit windows, a wet pavement. | Plan B, determined, not defeated | `train_departed` variants of `c08`, `c08_ok`, `c08_fail` (the guard checks tickets for the night bus) |
| `night_bus` | A generic double-decker (in ink, never red, no livery) with warm lit windows at a stop, over the skyline. It is the night bus **to Oxford**. | Warm, cosy, dignified | `train_departed` variants of `c09`, `c09_ok`, `c09_fail`, `c10`, `c10_ok`, `c10_fail` (stop B); ending `end_night_bus` (top deck) |
| `train_carriage` | Inside a warm carriage: windows, seat backs, London's lights sliding past. | Relief, warmth | endings `end_made_it`, `end_made_it_with_maya` |

## Mapping from the Step A proposal (retired keys)

| Step A key | Now |
|---|---|
| `ticket_barriers`, `station_passage` | `concourse_night` (barriers, far gates) and `platform` (passage, side gate); `location` carries the difference |
| `side_gate`, `platform_night` | `platform` |
| `platform_far` | `platform_empty` |
| `station_cafe` | dropped (checkpoint 4 moved to the machines, per ASSESSMENT_SPEC §9) |
| `station_exit_rain` | `street_night` |
| `bus_stop_night`, `night_bus_deck` | `night_bus` |
| `train_carriage`, `concourse_night`, `ticket_hall` | unchanged |

## Notes for the ux-ui-designer

- No brands, logos or real operator liveries. The station is a generic London terminus and is never named in any item.
- `concourse_night` must not show a readable platform number: no platform may appear before checkpoint 2 (ASSESSMENT_SPEC §9).
- `platform` must not show an "out of order" sign on the barriers: that may not appear before checkpoint 7.
- Maya never appears in the backdrop. She stays in her panel.
