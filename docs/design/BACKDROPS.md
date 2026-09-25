# BACKDROPS — The Last Train

> Owner: `narrative-designer`. Readers: `ux-ui-designer` (art direction), `frontend-engineer` (key → image/gradient), `story-graph-engineer` (validator may check that every `backdrop` in `mission.json` is listed here).
> Every `scene.backdrop` and `variants[].backdrop` in `content/missions/the-last-train/mission.json` uses a key from this table.
>
> **Reconcile with UI_SPEC:** these keys were proposed before `docs/design/UI_SPEC.md` existed. If the ux-ui-designer's spec lists different keys, the two lists must be reconciled at G1 (one of us renames; `mission.json` follows this file).

The night has one shape: the station gets **deeper and quieter** as the clock runs down (concourse → ticket hall → barriers → passage → platform → train). Plan B turns the other way, **out into the rain** (exit → bus stop → top deck). Colour temperature follows the mood: warm amber where people help, cold blue-grey where the student is alone, sodium orange on the street.

| Key | Location (as shown) | One-line visual description | Mood | Used by |
|---|---|---|---|---|
| `concourse_night` | Station concourse | A big London terminus at night: a glass roof over a wide concourse, a tall departures board glowing amber, the crowd thinning towards the gates. | Expectant, busy, a little overwhelming | intro, checkpoint 1 |
| `ticket_hall` | Ticket hall | A row of blue ticket machines and one lit ticket window with a tired clerk behind the glass; a short queue, a clock on the wall. | Fluorescent, practical, slightly anxious | checkpoints 2–3 |
| `station_cafe` | Late café | A small coffee kiosk with the shutter half down, steam from the machine, two stools and a chalkboard menu. | Warm pause, human | checkpoint 4 |
| `ticket_barriers` | Ticket barriers | A line of grey automatic barriers with small green and red lights; a guard in a hi-vis jacket with a radio on his shoulder. | Tense, a checkpoint in the literal sense | checkpoints 5–6 |
| `station_passage` | Passage to the platforms | A long tiled passage under the tracks: curved white tiles, posters, a moving walkway, footsteps echoing. | Hurried, echoing | checkpoints 7–8 |
| `platform_far` | The far platform | An empty platform at the edge of the station, one bench, a flickering sign, rails shining in the dark. Used when the student went the wrong way. | Lonely, cold, quiet | `wrong_platform` variants |
| `platform_night` | The platform | A long platform beside a waiting train with lit windows, a hanging clock over the tracks, a guard with a whistle at the far end. | Urgent, hopeful | checkpoints 9–10 |
| `train_carriage` | On the train | Inside a warm carriage: blue seats, a window with London's lights sliding past, two paper cups on the table. | Relief, warmth | endings `made_it`, `made_it_with_maya` |
| `station_exit_rain` | Outside the station | The station front at night in light rain: wet pavement, black cabs, red buses, the station clock above the doors. | Plan B, determined, not defeated | `train_departed` variants (first scene after the train leaves) |
| `bus_stop_night` | Night bus stop | A bus shelter with a lit timetable, a digital countdown ("22:20"), rain on the glass, a few quiet people waiting. | Calm, cool, companionable | `train_departed` variants on later checkpoints |
| `night_bus_deck` | Top deck of the night bus | The front seats of a red double-decker's top deck at night: the big window, city lights, rain drops, Maya's scarf on the seat. | Warm, cosy, dignified | ending `night_bus` |

## Notes for the ux-ui-designer

- Backdrops sit behind text: keep the lower 40% calm (low detail, darkened) so scene lines stay readable at 360 px.
- No brands, no logos, no real operator liveries. Red buses and black cabs are fine as generic London shapes; the station is a generic Victorian terminus, not a specific one.
- Maya never appears in the backdrop itself; she lives in her panel with four expressions.
- `platform_far` and `platform_night` can share one image with a different grade (colder, emptier) if time is short. Likewise `station_exit_rain` and `bus_stop_night`.
- Minimum viable set (if time runs out): `concourse_night`, `ticket_hall`, `ticket_barriers`, `platform_night`, `bus_stop_night`, `train_carriage`, `night_bus_deck`; the others fall back to the nearest one in this table order.
