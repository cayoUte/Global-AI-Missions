# UI SPEC — Global AI Missions · "London after dark"

> Owner: `ux-ui-designer`. Readers: frontend-engineer (builds from this without a design tool), narrative-designer (backdrop keys, §6), qa-engineer (a11y and anti-pattern checks, §8–§9).
> Sources: `docs/agents/SHARED_CONTEXT.md` (§2, §3, §7), `docs/product/PRODUCT.md` (§5, §9, §10), `docs/product/MAYA.md`, `docs/product/DECISIONS_LOG.md` (PD-001…PD-031), `docs/contracts/api-contract.md` (frozen G0), `docs/contracts/CHANGE_REQUESTS.md` (F-06, F-09, F-10, F-11, F-12).
> If this file and PRODUCT/the contract disagree, they win; tell the ux-ui-designer.
> Assets: `frontend/src/styles/tokens.css` (theme), `frontend/src/styles/backdrops.css` (backdrop layer), `frontend/src/assets/maya/{curious,encouraging,worried,proud}.svg`, `frontend/src/assets/backdrops/{arches,platform,skyline,bus,carriage}.svg`.

Contents: 1 Principles · 2 Visual language · 3 Tokens · 4 Layout · 5 Components · 6 Backdrops · 7 Motion · 8 Accessibility · 9 Screens · 10 Microcopy · 11 Handoff notes and open questions

---

## 1. Principles

1. **You are in the scene, not in a test.** In the mission the screen is a place: a backdrop, a departure board and Maya beside you. The only progress indicator is the story clock.
2. **Numbers once, first, in full.** No number, level or outcome appears during the mission. On the Mission Report the numbers come first, plain and with no clicks (PD-001).
3. **Nothing punishes.** Outcomes arrive through Maya's line and the next scene. The UI has no correctness color at all: the theme **removes Tailwind's default palette**, so there is no `green-*` or `red-*` utility to reach for.
4. **One decision per screen.** One prompt, large targets, then **Confirm**.
5. **Warm light = Maya.** Amber is the station (board, actions, focus). The peach glow (`maya-300`) belongs only to Maya.
6. **Light on the device.** CSS gradients and five small inline SVG silhouettes (all under 2.5 KB, inlined by Vite), three Google Fonts, Framer Motion as the only animation library, Lucide icons. No photos, video or canvas.
7. **Plain words where the evaluator looks.** Submit mission, Progress, Global score, Result per skill, Correct, Incorrect, Suggested level, Attempt record and Attempt history stay plain (PD-002). Their headings are plain text, not styled as departure boards.

### Forbidden anti-patterns (QA: each one is a defect)

| Never | Instead |
|---|---|
| "Question 3/10", "3/10" progress bars, step dots, % complete during the mission | The story clock label (`21:53 · 12 min to departure`) |
| Green ticks, red crosses, ✓/✗, green/red option tints, shake animations, success/failure sounds during the mission | Maya's reaction line plus the consequence scene; chosen option keeps a neutral "selected" style |
| Points, XP, coins, stars, badges, trophies, "level up", leaderboards | The report's plain numbers; "Maya's pick" is the only marker |
| Confetti, fireworks, streak flames, streak counters, combo counters | A calm crossfade into the ending |
| Revealing, eliminating or greying out an option after Confirm | Every option keeps its style; only the student's own selection stays marked |
| A "Hint" or "Ask Maya" button, a chat box for Maya | Maya speaks only when the planner decides (PD-012, MAYA §8.9) |
| A transcript beside the Listen button | Only the PD-014 fallback (speech unavailable) or the report's "Checkpoints to revisit" |
| Real transport-operator branding (the roundel, the Johnston typeface, the Underground map colors) | The generic enamel `sign-700` plate and the generic amber board |
| Emojis, exclamation chains, ALL-CAPS sentences (short uppercase *labels* are fine) | MAYA §3 voice |

---

## 2. Visual language — "London after dark"

- **Night.** Backgrounds run from deep ink (`ink-950`) to navy (`ink-700`); the sky in each backdrop is a vertical navy gradient.
- **Sodium amber departure board.** The story clock, the timetable stimulus, the Diary clock times and the primary action use `amber-400` on `ink-950`, set in **Share Tech Mono** with wide tracking. The board has a thin `amber-600` inner frame and a soft amber glow (`shadow-board`).
- **Warm light around Maya.** Her portrait sits in a peach radial glow (`shadow-lamp`, drawn into the SVG). Her name label and her bubble edge use `maya-300`.
- **Paper.** Things you hold in your hand (the boarding pass at Check-in, a station notice, the missed-checkpoint cards in the report) are cream paper (`paper-50`) with ink text.
- **Type.**
  - **Atkinson Hyperlegible** for dialogue and all UI: designed for low-vision legibility, with clear differences between I/l/1 and O/0.
  - **Fraunces** for titles, endings and Maya's report voice, which gives a cinematic, warm serif.
  - **Share Tech Mono** for boards only: story clock, timetable, Diary times, the password in the demo panel.
- **Icons.** Lucide (MIT) via `lucide-react`, 20 px, stroke 2, always next to a text label or with an `aria-label`. Icons used: `Pause`, `Volume2`, `Lock`, `NotebookPen`, `Lightbulb`, `Footprints`, `TrainFront`, `Bus`, `LogOut`, `Eye`, `EyeOff`, `WifiOff`, `RotateCw`, `ArrowRight`, `CircleAlert`.

### Fonts — add to `frontend/index.html` `<head>` (frontend-engineer owns the file)

```html
<meta name="theme-color" content="#0a1122" />
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link
  rel="stylesheet"
  href="https://fonts.googleapis.com/css2?family=Atkinson+Hyperlegible:ital,wght@0,400;0,700;1,400&family=Fraunces:opsz,wght@9..144,500;9..144,600&family=Share+Tech+Mono&display=swap"
/>
```

All three are SIL OFL. The fallbacks in `tokens.css` keep the app readable offline. Self-hosting via `@fontsource/*` is the production option (§11).

---

## 3. Tokens

Everything lives in `frontend/src/styles/tokens.css` as a Tailwind v4 `@theme static` block. Every token is both a CSS variable and a utility (`bg-ink-900`, `text-amber-400`, `font-board`, `rounded-card`, `shadow-lamp`, `ease-scene`, `max-w-player`, `animate-waveform`). `static` means every variable is always emitted, so Framer Motion and inline SVG can read `var(--color-…)`. There is no `tailwind.config` / `theme.extend` (F-12).

### 3.1 Color

| Token | Hex | Use |
|---|---|---|
| `ink-950` | `#060a14` | Board panels, backdrop floor, text on amber buttons |
| `ink-900` | `#0a1122` | Page background (`html`) |
| `ink-800` | `#111a30` | Cards, dialogue box (at `/95` over backdrops) |
| `ink-700` | `#19243f` | Raised surfaces, skeletons, bar tracks, selected table row |
| `ink-600` | `#26345a` | Decorative hairlines only (1.54:1); never the only edge of a control |
| `line-strong` | `#7483a6` | Input borders, choice-card borders, locked-card dashed border (non-text, ≥ 3:1) |
| `fog-50` | `#f4f1e8` | Primary text |
| `fog-200` | `#cdd3e0` | Secondary text, speaker labels |
| `fog-400` | `#9aa5bd` | Muted text (meta, footnotes, "x of n") |
| `amber-200` | `#ffd699` | Hover/pressed for amber things |
| `amber-400` | `#ffb547` | Board text, primary buttons, focus ring, skill-bar fill, selected choice ring |
| `amber-600` | `#b87314` | Decorative: board frame, dividers |
| `maya-300` | `#f7b58c` | Maya's name, her bubble's left edge, "Maya's pick" text |
| `paper-50` / `paper-300` | `#f5efe0` / `#d9ccab` | Paper surface / its edge and perforation |
| `paper-ink` / `paper-muted` | `#1d2233` / `#5b5443` | Text on paper; also the focus ring on paper |
| `sign-700` | `#123a73` | Generic enamel station sign (vocabulary/sign stimuli) |
| `phone-700` | `#23304f` | Phone message bubble (message stimuli) |

There is no error or success color. System errors are `fog-50` text, a `CircleAlert` icon and a `line-strong` left border (on paper: `paper-ink` text and edge).

### 3.2 Contrast (WCAG 2.2, computed with the relative-luminance formula)

Text pairs need ≥ 4.5:1 (AA). Non-text UI (focus rings, input borders, bar fills) needs ≥ 3:1.

| Foreground | Background | Ratio | Result | Where |
|---|---|---|---|---|
| fog-50 | ink-900 | 16.66 | AAA | Body text |
| fog-50 | ink-800 | 15.31 | AAA | Card text |
| fog-50 | ink-700 | 13.62 | AAA | Raised surfaces |
| fog-50 | dialogue worst case `#1f2331`* | 13.84 | AAA | Dialogue text over the brightest backdrop pixel |
| fog-200 | ink-900 / ink-800 / ink-700 | 12.53 / 11.52 / 10.25 | AAA | Secondary text |
| fog-200 | dialogue worst case | 10.42 | AAA | Speaker labels |
| fog-400 | ink-950 / ink-900 / ink-800 / ink-700 | 8.00 / 7.61 / 6.99 / 6.22 | AA+ | Muted text (lowest text pair: 6.22) |
| amber-400 | ink-950 / ink-900 / ink-800 / ink-700 | 11.26 / 10.71 / 9.84 / 8.75 | AAA | Board digits, amber labels |
| amber-200 | ink-800 | 12.63 | AAA | Hover text |
| ink-950 | amber-400 / amber-200 | 11.26 / 14.45 | AAA | Primary button label / hover |
| fog-50 | selected-card tint `#2e2d33`** | 12.08 | AAA | Text of the selected choice card |
| maya-300 | ink-800 / ink-700 | 9.84 / 8.75 | AAA | Maya's name |
| paper-ink | paper-50 | 13.78 | AAA | Boarding pass, notices, revisit cards |
| paper-muted | paper-50 | 6.55 | AA | Secondary text on paper |
| fog-50 / amber-200 | sign-700 | 9.90 / 8.16 | AAA | Station sign |
| fog-50 / fog-200 | phone-700 | 11.57 / 8.70 | AAA | Phone message |
| *non-text* amber-400 ring | ink-900 | 10.71 | ≥ 3 | Focus ring on night |
| *non-text* paper-ink ring | paper-50 | 13.78 | ≥ 3 | Focus ring on paper |
| *non-text* line-strong | ink-900 / ink-800 | 4.96 / 4.56 | ≥ 3 | Input and choice-card borders |
| *non-text* amber-400 fill | ink-700 track | 8.75 | ≥ 3 | Skill bars |
| ~~amber-400 ring~~ | paper-50 | 1.53 | **fail** | Never: paper surfaces switch the ring to ink (`.surface-paper`) |

\* `ink-800` at 94% over `amber-400`: the worst case for a translucent dialogue box. \*\* `amber-400` at 12% over `ink-800`.
Text placed directly on a backdrop (location kicker, ending title) always sits on the backdrop's `::after` scrim or on an `ink-950/70` pill. It never sits on raw gradient.

### 3.3 Type scale (mobile first; the step-ups are named per screen)

| Utility | Size / line | Use |
|---|---|---|
| `text-xs` | 13 / 20 px | Tags ("Multiple choice · Grammar · A2"), footnote, board sub-label. Never for sentences in the mission |
| `text-sm` | 15 / 22 | Meta, table cells, "x of n" |
| `text-base` | 17 / 26 | Body; dialogue and choice text on mobile (minimum in the mission) |
| `text-lg` | 19 / 28 | Dialogue and choices at `md+`; prompt on mobile |
| `text-xl` | 22 / 30 | Card titles; Maya's report voice on mobile |
| `text-2xl` | 28 / 34 | Screen headings; clock time on mobile; report label on mobile |
| `text-3xl` | 36 / 42 | Report label at `md+`; ending title |
| `text-4xl` | 48 / 48 | Clock time at `lg+`; Global score figure |

Weights: Atkinson 400 and 700; Fraunces 500 and 600; Share Tech Mono 400 with `tracking-board` (0.08em). Numbers in tables and bars use `tabular-nums`.

### 3.4 Spacing, layout widths, radii, shadows, layers

- Spacing: Tailwind's 4 px base (`p-4` = 16 px). Gutters: `px-4` (360+), `md:px-6`, `lg:px-8`. Vertical rhythm between sections: `space-y-8` on mobile, `md:space-y-12`.
- Widths: `max-w-reading` 40rem (report text, dialogue), `max-w-player` 48rem (Mission Player column, report page), `max-w-world` 70rem (English World, Progress).
- Radii: `rounded-board` 4 px (board, tags) · `rounded-control` 10 px (buttons, inputs) · `rounded-card` 16 px (cards, dialogue, choices) · `rounded-sheet` 24 px (boarding pass) · `rounded-full` (portraits, pills).
- Shadows: `shadow-card`, `shadow-raised`, `shadow-board` (amber frame + glow), `shadow-lamp` (Maya), `shadow-selected` (2 px amber ring + glow for the selected choice).
- Layers (`z-*`): backdrop 0 · scene content 10 · top bar 20 · sticky action bar 30 · offline banner 40. No modals in the MVP.

### 3.5 Motion tokens

| Token | Value | Reduced motion |
|---|---|---|
| `--motion-instant` | 100 ms | 100 ms |
| `--motion-quick` | 180 ms (hover, selection, bubble) | 0 |
| `--motion-scene` | 400 ms (scene crossfade, **Must**) | 120 ms, opacity only |
| `--motion-consequence` | 500 ms (reaction → consequence) | 120 ms, opacity only |
| `--motion-flip` | 240 ms (clock flip, Should) | 0 |
| `--typewriter-cps` | 30 (Should) | 0 = full text at once |
| `ease-scene` / `ease-enter` / `ease-exit` | `(.4,0,.2,1)` / `(.16,1,.3,1)` / `(.7,0,.84,0)` | Same |
| `animate-skeleton` (Must), `animate-maya-idle`, `animate-waveform`, `animate-lamp-flicker` (Should) | See tokens.css | Stopped (global reduced-motion rule) |

---

## 4. Layout and breakpoints

Mobile first. Design at **360 px**, then Tailwind defaults `sm` 640 · `md` 768 · `lg` 1024 · `xl` 1280. Check at 1440 px. There is never horizontal page scroll; long words wrap (`break-words`).

**App shell** (English World, Progress, Mission Report, Teacher page):

- Top bar, `h-14`, `bg-ink-950/80` with backdrop blur and a bottom `ink-600` hairline.
  - Left: wordmark "Global AI Missions" (Fraunces 600, `text-lg`).
  - Right: **Check out** (`LogOut` icon + text, ghost button).
- Nav: links **English World** and **Progress**.
  - Below 768 px: a two-tab segmented row under the bar (`h-11`, each half-width).
  - From 768 px: inline in the bar.
  - Active tab: amber 2 px underline + `aria-current="page"`, so it is not marked by color alone.
- Content: `mx-auto max-w-world px-4 md:px-6 lg:px-8 py-6 md:py-10`.

**The Mission Player has no shell.** It is full-bleed, with its own top bar (§9.3). Check-in has no shell either.

---

## 5. Component inventory (only what the MVP uses)

Props are the design contract. Types come from `src/api/schema.d.ts`. Every interactive component has hover, `focus-visible` (global amber ring), active, disabled and loading states as listed.

| Component | Props | States and rules |
|---|---|---|
| `Button` | `variant: 'primary' \| 'secondary' \| 'ghost' \| 'paper'`, `size: 'md' \| 'lg'`, `loading?: boolean`, `loadingLabel?`, `icon?` | `min-h-11` (44 px), `lg` = `min-h-14`. **primary** `bg-amber-400 text-ink-950 font-bold rounded-control`, hover `bg-amber-200`. **secondary** `border border-line-strong text-fog-50`, hover `bg-ink-700`. **ghost** text only, hover underline. **paper** (on paper) `bg-paper-ink text-paper-50`. Disabled: `opacity-60 cursor-not-allowed` plus `aria-disabled`. Loading: disabled, and the label is replaced by `loadingLabel` (e.g. "Checking in…"). Never a spinner alone. |
| `DepartureBoard` (story clock) | `clock: Clock` | See §9.3.2. `font-board`, `bg-ink-950`, `shadow-board`, `rounded-board`. |
| `Backdrop` | `backdropKey: string` | `<div className="backdrop" data-backdrop={key} aria-hidden />`, §6. |
| `MayaPortrait` | `mood: Mood`, `size: 40 \| 56 \| 72 \| 96 \| 128`, `decorative?: boolean` | `<img src={maya[mood]} width height>`; `alt` = "Maya, looking {mood}" unless decorative (`alt=""` when "Maya" is written next to it). Circle, `shadow-lamp`. Mood change: crossfade `motion-quick`. Idle (Should): `animate-maya-idle` on the wrapper. |
| `MayaBubble` | `line: string \| null`, `kind: 'line' \| 'hint' \| 'rescue' \| 'reaction' \| 'waiting'`, `mood` | `bg-ink-800/95 rounded-card border-l-4 border-maya-300 px-4 py-3`. Name label "Maya" (`text-xs font-bold uppercase tracking-wide text-maya-300`). Text `text-base md:text-lg`. `hint` looks the same as `line` (no "Hint" label, PRODUCT §10). `rescue` adds the kicker "Maya's shortcut" (`Footprints` icon) and `shadow-lamp`. `waiting` = "One moment…" in italics. `null` → not rendered. Enter: fade + 4 px rise, `ease-enter`, `motion-quick`. |
| `DialogueBox` | `lines: {speaker, text}[]` | `bg-ink-800/95 rounded-card shadow-raised p-4 md:p-5`. Speakers: `narrator` → no label, `text-fog-50`. `maya` → label "Maya" in `maya-300`. `you` → label "You" in `amber-400`. Anything else → the raw name in `fog-200` (`text-xs uppercase font-bold`). A speaker label shows only when the speaker changes. Lines are `<p>`s with `space-y-2`. Typewriter (Should) §7. |
| `SceneKicker` | `location: string` | `text-xs font-bold uppercase tracking-board text-fog-200`, on an `ink-950/70` pill (text only, no icon). |
| `ChoiceCard` / `ChoiceGroup` | `options: {id,text}[]`, `value`, `onChange`, `locked`, `layout: 'stack' \| 'grid'` | See §9.3.4. `role="radiogroup"` / `role="radio"`, roving tabindex. |
| `GapInput` | `prompt` (with one `___`), `value`, `onChange`, `locked`, `onSubmit` | See §9.3.4 fill_blank. |
| `Stimulus` | `stimulus: Stimulus \| null` | One renderer per `stimulus.kind`: `audio` → `Announcement`, `dialogue` → speech bubble, `message` → `PhoneMessage`, `notice` → `NoticePaper`, `timetable` → `TimetableBoard`, `sign` → `SignPlate`. §9.3.4. |
| `Announcement` | `speaker`, `audioScript`, `rate` | States: idle / speaking / played / unavailable (PD-014). §9.3.4. |
| `ActionBar` | `primary: {label, onClick, disabled, loading}` | Mobile: `sticky bottom-0`, `bg-ink-950/90` blur, `pb-[max(1rem,env(safe-area-inset-bottom))]`, full-width `Button lg`. `lg+`: inline under the decision area, right-aligned, with a keyboard hint "Enter" (`<kbd>`, `text-xs text-fog-400`). |
| `InlineNotice` | `tone: 'info' \| 'problem'`, `title?`, `message`, `action?` | `bg-ink-800 border-l-4 border-line-strong rounded-card p-4`, with `CircleAlert` (problem) or `WifiOff` (offline). `role="alert"` for problem, `role="status"` for info. On paper: `paper-ink` text and edge. |
| `OfflineBanner` | none (reads `navigator.onLine` + `online`/`offline` events) | Top of the viewport, `z-40`, `bg-ink-950 text-fog-50 text-sm`, `WifiOff` icon, `role="status"`. |
| `Skeleton` | `className` | `bg-ink-700 rounded-card animate-skeleton`, same size as the real block (no layout jump). |
| `SkillBar` | `skill`, `pct`, `correct?`, `total?`, `size: 'md' \| 'sm'` | Row: skill name (`text-sm font-bold`), "x of n" (`text-fog-400`, only when given), % as text (`tabular-nums`, right). Track `h-2 md` / `h-1.5 sm`, `bg-ink-700 rounded-full`. Fill `bg-amber-400`, width `pct%`. `role="img"` with `aria-label="Grammar 75%, 3 of 4"`. The % is always written, so color is never the signal. 0% shows an empty track and "0%". |
| `Tag` | `text` | `text-xs font-bold uppercase tracking-wide text-fog-200 border border-line-strong rounded-board px-2 py-0.5`. Used for "Multiple choice · Grammar · A2", skill focus, CEFR range. |
| `OutcomeMarker` | `outcome: 'understood' \| 'missed'` | Report only. Understood = filled circle ● + "Understood". Missed = hollow ring ○ + "Missed". Both `fog-200`, **same color**: shape + word carry it. |
| `MissionCard` | `card: MissionCard` | §9.2.3. |
| `MayasPickMarker` | none | Pill `bg-ink-950 border border-maya-300 text-maya-300 text-xs font-bold` with a 20 px decorative portrait + "Maya's pick". Card gets `shadow-lamp`. |
| `BoardingPass` | children | §9.1. `surface-paper` class (switches the focus ring to ink). |
| `DiaryTimeline` | `entries: DiaryEntry[]` | §9.5. |
| `HistoryTable` | `rows: HistoryRow[]` | §9.6. |

Loading-label rule: every async button shows a text loading label, and the whole region gets `aria-busy="true"`.

---

## 6. Backdrops (proposal for the narrative-designer's `docs/design/BACKDROPS.md`)

`BACKDROPS.md` does not exist yet. These are the keys the frontend already renders (`backdrops.css`). The narrative-designer should adopt them, or send new ones to the ux-ui-designer. Adding a key is about six lines of CSS. **An unknown key renders `concourse_night`**, so a typo never blanks the scene. Keys follow `^[a-z][a-z0-9_]{0,47}$` (mission.schema).

| Key | Scene | Silhouette | Light |
|---|---|---|---|
| `concourse_night` | Station concourse, intro, the departures hall (**default**) | `arches.svg` (train-shed ribs, arcade, hanging clock) | Amber board glow high centre |
| `ticket_hall` | Ticket machines, ticket office queue | `arches.svg`, lower | Cool machine glow left, amber right |
| `platform` | Any platform (use `location` for "Platform 6") | `platform.svg` (canopy, sodium lamps, amber safety line, rails) | Sodium haze along the lamps |
| `platform_empty` | Plan B after `train_departed`: the empty platform | `platform.svg` | One dim lamp, darker sky: calm, not grim |
| `arcade_shortcut` | Maya's rescue ("I know a shortcut through the arcade") | `arches.svg`, closer | Maya's peach light + shop glow |
| `street_night` | Outside the station, the street, the walk to the bus stop | `skyline.svg` (generic rooftops, dome, spire, lit windows) | Moon haze, street glow |
| `night_bus` | Plan B bus stop, top deck, ending `night_bus` | `bus.svg` over `skyline.svg` (generic double-decker in ink, lit windows, never red) | Warm bus glow |
| `train_carriage` | Inside the train, endings `made_it` and `made_it_with_maya` | `carriage.svg` (windows, seat backs) | City lights sliding past the windows |

Suggested defaults: intro → `concourse_night`; ticket checkpoints → `ticket_hall`; announcements and the guard → `platform`; every `train_departed` variant → `platform_empty`, `street_night` or `night_bus`; rescue edge target → `arcade_shortcut`; endings → `train_carriage` / `night_bus`.

**Rendering.**

- The scene root is `relative min-h-dvh overflow-hidden`.
- Mobile: the backdrop is `fixed inset-0` behind the scrolling content, so the top ~35% of the viewport shows the scene and the scrim darkens the bottom under the dialogue.
- `lg+`: the backdrop stays fixed; content sits in the centred column.
- Silhouettes occupy the bottom 58–100% of the backdrop with `background-size: cover`. The platform and bus keys anchor off-centre so the lamps and the bus stay in frame at 360 px (verified with headless Chrome at 180×320 and 560×320).

---

## 7. Motion

Framer Motion is the only animation library. Wrap the app in `<MotionConfig reducedMotion="user">` and use these constants. Put them in `src/lib/motion.ts`; they mirror `tokens.css`.

```ts
export const MOTION = { quick: 0.18, scene: 0.4, consequence: 0.5, flip: 0.24, reduced: 0.12 } // seconds
export const EASE = { scene: [0.4, 0, 0.2, 1], enter: [0.16, 1, 0.3, 1], exit: [0.7, 0, 0.84, 0] } as const
export const TYPEWRITER_CPS = 30
```

| Motion | Priority | Spec | Reduced motion |
|---|---|---|---|
| **Scene crossfade** | **Must** | Two layers, keyed by `node.id`. (1) Backdrop: `AnimatePresence` (default sync mode), both backdrops absolutely stacked, opacity 0→1 / 1→0 over `MOTION.scene` (400 ms), `EASE.scene`. When the key doesn't change, nothing animates. (2) Content column: `mode="wait"`, exit opacity→0 in 150 ms, enter opacity 0→1 + `y: 8→0` in 250 ms, `EASE.enter`. Total < 600 ms (PRODUCT §5.3). | Opacity only, 120 ms, no `y` |
| Consequence handoff | Must | After Confirm, the portrait swaps to the new mood and the bubble shows `maya_line`. The scene crossfades to the consequence in `MOTION.consequence`. **No forced wait, no auto-advance** (PD-024): the student presses Continue. | 120 ms fade |
| Selection | Must | Choice card ring and tint over 180 ms; no scale, no bounce. | Instant |
| Skeleton pulse | Must | `animate-skeleton` | Static |
| Typewriter | Should (after G2) | 30 chars/s, line by line, scene lines only (never prompt, options, documents or Maya's hint). **Skippable:** a click or tap on the dialogue box, Space, or the first press of Continue/Enter completes the text; the second press advances. The live region receives the full text at once (§8). No typing sound. | Off: full text |
| Clock flip | Should | Only the characters that change: old char `rotateX 0→-90` (120 ms), new `90→0` (120 ms), per-char `inline-block`, `perspective: 400px`. Fires when `clock.time` changes. | Text swaps instantly |
| Maya idle | Should | `animate-maya-idle` (2 px float, 6 s). Paused while the bubble is entering. | Off |
| Listening waveform | Should | Five `w-1 rounded-full bg-amber-400` bars, `animate-waveform` with `animation-delay` 0/120/240/360/480 ms, only while speaking; 25% height when idle. | Static bars |
| Lamp flicker | Could | `animate-lamp-flicker` on the platform backdrop | Off |

Never: shake, bounce, spring overshoot on outcomes, confetti, particle effects, parallax on scroll, autoplaying audio.

> Built 2026-09-25 (frontend-engineer): Typewriter (`lib/useTypewriter.ts`; Continue is gated only on narrative/consequence nodes, Confirm never waits for it; the untyped rest of a line stays in the layout as `invisible` text, so nothing jumps), Clock flip (`FlipText` in `DepartureBoard`, time part only; the sub-label swaps instantly) and Maya idle (the scene portrait; paused for `motion-quick` while a new bubble enters). Keyboard E2E presses Enter twice on narrative nodes: the first completes the text, the second advances.

---

## 8. Accessibility

**Keyboard — Mission Player**

| Key | Action | When |
|---|---|---|
| `1`–`4` | Select option N (does not confirm) | Choice checkpoints, focus not in a text input |
| Arrow keys | Move focus and selection within the choice group (radio pattern) | Focus in the group |
| `Enter` | **Confirm** if something is selected (or the trimmed gap text is non-empty); **Continue** on narrative/consequence nodes; **Submit mission** is *not* bound to Enter (it is a deliberate button press) | Anywhere in the player except on another button, which keeps its native Enter |
| `L` | **Listen** / **Listen again** | Checkpoints with an audio stimulus, focus not in a text input |
| `Space` | Complete the typewriter text (Should) | Focus not on a control |
| `Tab` | Order: Pause → board (not focusable) → dialogue (not focusable) → Listen → choices / gap → Confirm/Continue | Always |

Show the hints at `lg+` only: number badges on the cards, and `<kbd>Enter</kbd>` beside the action. Shortcuts must not fire while a modifier key is pressed or while an IME is composing.

**Focus management**

- On every new node, move focus programmatically (`preventScroll: false`):
  - on a checkpoint, to the choice group (`tabindex=-1`, `aria-labelledby` = the prompt id) or to the gap input;
  - otherwise, to the **Continue** button.
- On route change, move focus to the page `h1`.
- Never trap focus.
- After a 409 resync, focus the new node's target the same way.

**Live regions**

- The player has **one** `aria-live="polite"` region (visually hidden, `role="log"`, `aria-relevant="additions"`). On each node it receives one block: `"{location}. {clock.label}. {speaker}: {text} … Maya: {maya.line}"`.
  - After an answer, the block starts with Maya's reaction.
  - The clock and dialogue themselves are not live, so nothing is announced twice.
  - Typewriter text is never streamed to it.
- Busy/failure messages (`InlineNotice`) use `role="status"` or `role="alert"`.
- The Ending's submit loading uses `role="status"`: "Maya is reading your Diary…".

**Structure**

- One `h1` per screen. The Mission Player's `h1` is visually hidden: "The Last Train — {location}".
- The report uses real `h2`s with the plain headings.
- The Progress table is a real `<table>` with `<caption>`, `scope="col"` headers and `<abbr title>` for abbreviated skills.
- Choice groups: `role="radiogroup"` + `role="radio"` + `aria-checked`. After Confirm the group is `aria-disabled="true"` and each radio is `aria-disabled`.
- The gap input has `aria-label="Your words for the gap"` and `aria-describedby` pointing to a visually hidden copy of the sentence with "blank" in place of `___`.

**Never by color alone**

- Selected choice: amber ring + tint **and** a filled number badge (shape) **and** `aria-checked`.
- Outcome markers in the report: shape + word.
- Active nav: underline + `aria-current`.
- Skill bars: the % is written.
- Locked card: `Lock` icon + text.
- Plan B clock: the label text says "Train departed — Plan B".

**Targets and text**

- Every target is ≥ 44×44 px (`min-h-11`, icon buttons `size-11`); choice cards ≥ 56 px tall.
- Text reflows to 200% zoom without loss.
- Dialogue never drops below 17 px, and line length stays ≤ 70ch (`max-w-reading`).

**Media.** Speech plays only on a user gesture (Listen). No autoplay.

**Language.** `<html lang="en">` is already set.

---

## 9. Screens

### 9.1 Check-in — a boarding pass

**Layout (360 px).**

- Full-screen `Backdrop` `street_night`.
- Centred column `max-w-[26rem] px-4 py-8`, holding the **BoardingPass** (`bg-paper-50 text-paper-ink rounded-sheet shadow-raised surface-paper`) with two parts separated by a perforation:
  - The perforation is a dashed `paper-300` line with two 12 px half-circle notches cut at the edges (`radial-gradient` masks). It is decorative (`aria-hidden`).
  - **Header:** kicker `BOARDING PASS` (`font-board text-xs tracking-board text-paper-muted`); wordmark "Global AI Missions" (`font-display text-2xl`); tagline "Tonight, your English gets you home."
  - **Journey strip** (decorative, `aria-hidden`, `font-board`): `FROM London · TO Home · DEPARTS 22:05 · PLATFORM —`, as a 2×2 grid on mobile and one row at `sm+`.
  - **Form:**
    - Labelled **Email** (`type=email autocomplete=username inputmode=email`) and **Password** (`autocomplete=current-password`), plus a show/hide toggle (`Eye`/`EyeOff`, 44 px, `aria-pressed`, label "Show password").
    - Inputs: `bg-paper-50 border border-paper-muted rounded-control min-h-11 px-3 text-base`.
    - Primary **Check in** button: `paper` variant, full width, `min-h-14`.
  - **Stub** (below the perforation, demo mode only): the Demo accounts panel.
- `lg+`: the pass widens to `max-w-[40rem]`. Header and form sit on the left; the stub becomes a right-hand column separated by a vertical perforation.

**Demo accounts panel** (PD-018; data only from `GET /api/config`).

- Heading "Demo accounts".
- One row per account: name + role ("Ana · student"), the email in `font-board`, the purpose in `text-sm text-paper-muted`, and a secondary **Use this account** button (fills email and password, focuses **Check in**, does not submit).
- Footer: "Password for all demo accounts:" plus the password in `font-board`.
- Hidden when `demo_mode` is false.
- It never blocks the form: the form renders first, and the panel appears when config arrives (it sits below, so nothing jumps).

**States**

| State | Behaviour and copy |
|---|---|
| Idle | Email is focused on load (desktop only; no autofocus on mobile, so the keyboard doesn't cover the pass). |
| Client validation | Presence and email shape only, shown on submit under the field: "Enter your email." / "Enter an email like name@example.com." / "Enter your password." (`CircleAlert` + text, `aria-describedby`, `aria-invalid`). |
| Loading | Button disabled, label "Checking in…"; fields read-only. |
| Wrong credentials (401) | `InlineNotice` above the button: "That email and password don't match." Keep the email and clear the password. |
| Rate limited (429) | "Too many tries. Wait a minute and check in again." Keep the email. |
| Network / 5xx | "We couldn't reach Global AI. Check your connection and try again." Keep the email. |
| Session expired (arrived via 401 elsewhere) | Info notice above the form: "Your session ended. Check in again — your mission is saved." |
| Offline | `OfflineBanner` + the network copy on submit. |
| Already authenticated | Redirect home; show nothing (a blank ink screen for at most one frame). |

There is no sign-up, reset or social login, and no link pretends to be one.

### 9.2 English World

**Layout.**

- Shell.
- Mobile order: Greeting → Missions board → Progress snapshot → (demo) "Watch a simulated run".
- `lg+`: a two-column grid `grid-cols-[1fr_20rem] gap-8`. The left column holds the greeting and the board; the right column holds the snapshot (`sticky top-20`).
- `h1` (visually hidden): "English World".

**9.2.1 Maya's greeting card.**

- `bg-ink-800 rounded-card shadow-card p-4 md:p-6`, with a subtle `backdrop` of `concourse_night` inside it: an `overflow-hidden` rounded box with the scrim.
- Row: `MayaPortrait` (72 px mobile / 96 px `md`, mood = `greeting.mood`).
- Kicker: "Welcome, {display_name}." (`font-display text-2xl`).
- Then "Maya" (`text-xs uppercase text-maya-300`) and the greeting text (`text-lg`) in a `MayaBubble` style without the bubble background.
- Source `first_meeting` shows the canonical PD-022 line verbatim; `memory` shows the stored text verbatim.

**9.2.2 Progress snapshot** ("Your English today").

- `bg-ink-800 rounded-card p-4`.
- Latest label (`font-display text-xl`, e.g. "A2 · The Last Train — 70%").
- Four `SkillBar size=sm` from `snapshot.profile.skills`, in the fixed order grammar, listening, reading, vocabulary.
- Meta: "Based on your last {based_on_attempts} missions · {missions_played} missions played". Use the singular "mission" for 1.
- Link **See your progress** (`ArrowRight`).
- **Empty** (`missions_played = 0`): "Your story starts tonight. Your progress will appear here after your first mission." plus **See your progress** (still visible). No bars and no zeros.

**9.2.3 Missions board.**

- `h2` "Missions".
- Grid: `grid-cols-1 md:grid-cols-2 gap-4`. The card whose `playable` is true spans both columns at `md+` as the featured card, with a 96 px `platform` backdrop strip across its top.
- Cards are in `sort_order`. Each card is an `<article>` (`bg-ink-800 rounded-card shadow-card p-4 md:p-5`). The whole card is **not** a link; the CTA is.

Card anatomy, top to bottom:

1. The status strip (`font-board text-xs uppercase tracking-board`, on `ink-950`), with the state label left and the zone right.
2. The title (`font-display text-xl`).
3. The skill-focus tags ("Grammar", "Listening", …) and the CEFR range tag (`Pre-A1` display rule; "A1–B2").
4. The teaser (`text-fog-200`).
5. The state line.
6. The CTA.
7. The "Maya's pick" marker, top-right, when `is_maya_pick`.

Zone display: `world_zone` slug → words, title case ("the-station" → "The Station").

| `state` | Strip label | State line | Primary CTA | Secondary |
|---|---|---|---|---|
| `available` | AVAILABLE (amber) | teaser only | **Start mission** (primary, `TrainFront`) | — |
| `in_progress` | IN PROGRESS (amber) | Board line `{open_attempt.clock.time} · {open_attempt.location}` ("21:55 · Platform 4") | **Continue your mission** (primary) | — |
| `waiting_to_submit` | WAITING TO SUBMIT (amber) | "Ending reached: {open_attempt.ending.title}" | **Submit mission** (primary; opens the Ending) | — |
| `completed` | COMPLETED (fog-200) | `latest_result.label` (`text-lg font-bold`) + "Played {attempts_submitted} time(s)" | **Play again** (primary) | **View Mission Report** (secondary) |
| `locked` | LOCKED (fog-400), `Lock` icon | `Lock` + unlock hint ("Opens after your first Mission Report on The Last Train.") | none | — |
| `in_preparation` | IN PREPARATION (maya-300), `NotebookPen` icon | "Maya is preparing this mission." | none | — |

- Locked cards have a `border border-dashed border-line-strong` and `bg-ink-900`. Their text stays `fog-200` or higher (not dimmed below AA). They are not focusable.
- `in_progress` / `waiting_to_submit` also show `latest_result.label` in `text-sm text-fog-400` when it exists (F-04).
- "Maya's pick" appears on at most one card, and never when there are no submitted attempts.
- CTA behaviour: **Start mission** and **Play again** call start and route to the player. **Continue your mission** and **Submit mission** route to the player with `open_attempt.attempt_id`. Loading label "Opening…".

**States**

| State | Spec |
|---|---|
| Loading | Greeting skeleton (72 px circle + three lines), five card skeletons (the first spanning two columns at `md+`), snapshot skeleton (four bars). Same heights as the real blocks. |
| Empty | Not applicable to the board (the catalog always has five). Snapshot empty per 9.2.2. |
| Error | Replace the content area with `InlineNotice problem`: "The lights went out for a moment. Try again." + **Try again**. Nothing half-rendered. |
| Offline | `OfflineBanner`; if the fetch fails, the error state. |
| Start fails | Inline under the card's CTA: "The lights went out for a moment. Try again." |

### 9.3 Mission Player

#### 9.3.1 Wireframes

Mobile, 360 × 740, checkpoint with a listening stimulus:

```
┌──────────────────────────────────────┐
│ [‖ Pause]              ╔═══════════╗ │ top bar h-14, transparent, over the backdrop
│                        ║ 21:53     ║ │ DepartureBoard: time text-2xl
│                        ║ 12 MIN TO ║ │ remainder of label text-xs, wraps to 2 lines
│                        ║ DEPARTURE ║ │
│                        ╚═══════════╝ │
│   ░░░ backdrop: platform ░░░░░░░░░░  │ ~30vh of scene visible
│   ░░ lamps ░░ amber safety line ░░░  │
│ ( PLATFORM 6 )                       │ SceneKicker pill
│ ┌──────────────────────────────────┐ │
│ │ The speakers crackle above the   │ │ DialogueBox (narrator: no label)
│ │ crowd.                           │ │
│ └──────────────────────────────────┘ │
│ (◕‿◕) MAYA                           │ MayaPortrait 56 + MayaBubble
│  ▌ Listen for the number, not the    │ (a hint looks exactly like any line)
│  ▌ name.                             │
│ ┌──────────────────────────────────┐ │ Announcement
│ │ STATION ANNOUNCER    ▁▃▅▃▁       │ │ speaker + waveform (Should)
│ │ [ [spk] Listen                    ] │ │ secondary lg button, 56 px
│ └──────────────────────────────────┘ │
│ Which platform does the announcer    │ prompt text-lg bold
│ say?                                 │
│ ┌──────────────────────────────────┐ │
│ │ (1) Platform two                 │ │ ChoiceCard ≥ 56 px
│ └──────────────────────────────────┘ │
│ ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓ │
│ ┃ (●2) Platform six                ┃ │ selected: amber ring + tint + filled badge
│ ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛ │
│ ┌──────────────────────────────────┐ │
│ │ (3) Platform sixteen             │ │
│ └──────────────────────────────────┘ │
├──────────────────────────────────────┤
│ [            Confirm             ]   │ ActionBar sticky, primary lg
└──────────────────────────────────────┘
```

Desktop, 1280+ (`lg`): two columns inside `max-w-[64rem]`. Maya's column is sticky.

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ [‖ Pause]      THE LAST TRAIN                          ╔══════════════════╗  │
│                                                        ║ 21:53            ║  │ time text-4xl
│                                                        ║ 12 MIN TO DEPART.║  │
│                                                        ╚══════════════════╝  │
│ ░░░░░░░░░░░░░░░░░░░░░░ full-bleed backdrop (fixed) ░░░░░░░░░░░░░░░░░░░░░░░░░ │
│  ┌──────────────┐   ( PLATFORM 6 )                                           │
│  │   (◕‿◕)      │   ┌──────────────────────────────────────────────────────┐ │
│  │  Maya 128px  │   │ The speakers crackle above the crowd.                 │ │
│  │  lamp glow   │   └──────────────────────────────────────────────────────┘ │
│  ├──────────────┤   ┌ Announcement ───────────────────────────────────────┐  │
│  │ MAYA         │   │ STATION ANNOUNCER  ▁▃▅▃▁   [[spk] Listen again]  (L)    │  │
│  │ Listen for   │   └──────────────────────────────────────────────────────┘ │
│  │ the number,  │   Which platform does the announcer say?                   │
│  │ not the name.│   [1  Platform two        ]  [2  Platform six      ]      │ 2-col if all ≤ 28 chars
│  └──────────────┘   [3  Platform sixteen    ]                                │
│   sticky 15rem                                       Enter  [  Confirm  ]  │ inline ActionBar
└──────────────────────────────────────────────────────────────────────────────┘
```

Mobile layout rules:

- A single column (`max-w-player mx-auto px-4`) that starts at `pt-[32vh]`, so the backdrop shows above it.
- The column scrolls; the backdrop is fixed.
- On a node change, scroll to the top of the column (`scrollIntoView({block:'start'})` on the kicker).

Tablet (`md`): the same single column, with the portrait at 72 px and text at `text-lg`.

#### 9.3.2 Story clock — `DepartureBoard`

- `bg-ink-950 rounded-board shadow-board px-3 py-2 font-board text-amber-400 tracking-board uppercase`, min width 8.5rem, `lg:` 13rem.
- Render `clock.label` **verbatim** (F-06). For layout only, split on the first " · ": the first part (the time) in `text-2xl lg:text-4xl tabular-nums`, the rest in `text-xs lg:text-sm`. With no " · ", show the whole label at the small size.
- The element has `aria-label={clock.label}`, and its children are `aria-hidden`. `uppercase` is CSS only, so screen readers get the mixed-case label.

| Clock | Example (server label) | Style |
|---|---|---|
| Normal | `21:53 · 12 min to departure` | Amber on ink-950 |
| Tight (1–2 min) | `22:04 · 1 min to departure` | **Unchanged.** No red, no pulse; Maya's worried mood carries the tension |
| Zero | `22:05 · Departing now` | Unchanged. The Should-flip still applies |
| Departed | `22:07 · Train departed — Plan B` | Text `fog-200`, frame `ink-600` (the board "switches off"), plus a `Bus` icon before the sub-label. The words carry the meaning |

- It is never a countdown, never ticks by itself and never shows seconds.
- It updates only when a new StateView arrives, with the flip (Should) on changed characters.

#### 9.3.3 Scene, Maya, decision, consequence

- **Top bar** (`h-14`, `bg-gradient-to-b from-ink-950/80 to-transparent`):
  - Left: **Pause** (ghost, `Pause` icon + text) → navigate to the English World. No confirm dialog: the run is on the server.
  - Centre (`md+`): `mission_title` in `font-display text-sm text-fog-200`.
  - Right: `DepartureBoard`.
- **Scene**: `SceneKicker(location)` → `DialogueBox(scene.lines)`. Narrative nodes have ≤ 3 lines (PD-024).
- **Maya.** `MayaPortrait(maya.mood)` and `MayaBubble(maya.line)`:
  - `decision = hint` → `kind='hint'`, visually the same as a line, shown **before** the choices.
  - `decision = rescue` → `kind='rescue'`: the kicker "Maya's shortcut" with `Footprints`, `shadow-lamp` on the portrait, and the portrait at the next size up for this node. Framed as teamwork; the backdrop is typically `arcade_shortcut`.
  - `line = null` → the portrait only.
  - On mobile, Maya sits between the dialogue and the decision. At `lg+` she is in the sticky left column.
- **Decision area** (checkpoints only): `Stimulus` → prompt (`text-lg font-bold`, `id` for `aria-labelledby`, rendered as plain text; for `fill_blank` the prompt *is* the gap sentence) → answer renderer (§9.3.4) → `ActionBar` **Confirm**.
  - Confirm is disabled until an option is selected, or until the trimmed text is 1–80 chars.
  - It sends exactly one request.
- **Narrative / consequence nodes**: the `ActionBar` is **Continue** (primary) → `advance`.
- **After Confirm** (order matters):
  1. Immediately lock the group (`aria-disabled`). The chosen card keeps its selected style; nothing else changes (no reveal, no dimming of other options). Confirm shows "One moment…" as its loading label only if the response takes > 1 s.
  2. On `200 {maya_line, state}`, swap the portrait to `state.maya.mood` and crossfade the scene (§7) to `state.node`.
  3. The bubble shows `maya_line` (`kind='reaction'`, or `'rescue'` when `state.maya.decision = 'rescue'`). If `state.maya.line` is non-null and different, render it as a second paragraph in the same bubble.
  4. The live region announces reaction + scene.
  5. **Continue** gets focus.

  After a reload on a consequence node, only `state.maya.line` exists. That is acceptable.
- **Ending node** (`status = completed`): render the Ending (§9.4) inside the player route.

#### 9.3.4 Renderers — one per item type (the stimulus renderer follows `stimulus.kind`)

The **answer renderer** is chosen by `checkpoint.type`. The **stimulus renderer** is chosen by `stimulus.kind` (F-09), so every combination is covered.

**`multiple_choice` → decision cards.**

- `ChoiceGroup layout='stack'` (switch to `grid md:grid-cols-2` when every option is ≤ 28 characters).
- Card: `min-h-14 w-full rounded-card border border-line-strong bg-ink-800/95 px-4 py-3 text-left text-base md:text-lg flex gap-3 items-center`.
- Number badge: a `size-7 rounded-full border border-line-strong font-board text-sm` with the digit "1"…"4".
- Hover: `bg-ink-700`.
- Selected: `shadow-selected`, `bg-amber-400/12`, `border-amber-400`, badge `bg-amber-400 text-ink-950` (filled shape), `aria-checked="true"`.
- Locked: `cursor-default`, no hover; the selected card keeps its style. **No option ever changes color, shows ✓/✗ or is struck through.**
- These are decisions in the story ("Ask the guard", "Run to platform 6"). The layout never numbers them as questions.

**`fill_blank` → an inline gap inside the spoken line.**

- Rendered as the student's own speech bubble: label "You" (`amber-400`), `bg-ink-800/95 rounded-card p-4 text-lg`.
- The prompt is split on the single `___` (F-09). The text before, the `GapInput`, and the text after flow inline.
- `GapInput`:
  - `inline-block min-w-[6ch] max-w-full w-[calc(var(--chars)*1ch+2ch)]`, where `--chars` is the current length (min 6, max 18; wraps to its own line on narrow screens).
  - `bg-ink-950 border-b-2 border-amber-400 rounded-t-board px-2 py-1 text-amber-200 font-bold`.
  - `maxLength=80`, `autocomplete=off autocorrect=off autocapitalize=off spellcheck=false` (spellcheck would suggest answers), `enterKeyHint="done"`.
  - Enter confirms when the trimmed text is non-empty.
- If `stimulus` is a `dialogue` from another speaker (e.g. the clerk's question), render it as a bubble above.
- Locked: the input becomes `readOnly` and keeps the typed text; no styling change.
- Placeholder: none (a placeholder could hint at a word form). The helper under the bubble reads "Type the missing words." in `text-sm text-fog-400`.

**`comprehension` → a diegetic document, then decision cards.**

| `stimulus.kind` | Renderer |
|---|---|
| `message` | **PhoneMessage**: a phone card `max-w-[22rem] mx-auto bg-ink-950 rounded-sheet p-3 border border-ink-600`. Header row: `speaker` ("From: Sam") in `text-sm font-bold text-fog-200` + a decorative time (`clock.time`, `font-board text-xs`). The message bubble is `bg-phone-700 rounded-card rounded-tl-board p-3 text-base`, `whitespace-pre-line`. |
| `notice` | **NoticePaper**: `surface-paper bg-paper-50 text-paper-ink rounded-card p-4 shadow-raised`, with a 4 px `paper-300` top rule. Heading = `speaker` ("Station notice") in `text-sm font-bold uppercase tracking-wide`. Body `text-base whitespace-pre-line`. Tilt `rotate-[-0.6deg]` at `md+` only (static, fine under reduced motion). |
| `timetable` | **TimetableBoard**: `bg-ink-950 shadow-board rounded-board p-3 font-board text-amber-400 text-sm md:text-base`. Rows split on `\n`, each row `whitespace-pre` in the mono font (keeps column alignment). The first row is the header (`text-fog-200`). Horizontal overflow scrolls *inside* the board (`overflow-x-auto`, `tabindex=0`, `aria-label="Timetable"`), never the page. |
| `sign` | **SignPlate**: `bg-sign-700 text-fog-50 rounded-board border-2 border-fog-50/80 px-4 py-3 text-center text-xl font-bold tracking-wide`, with a `speaker` caption below it (`text-xs text-fog-400`) if present. Generic enamel sign; no real operator's roundel or typeface. |
| `dialogue` | A speech bubble with the speaker label (as in `DialogueBox`). |

Layout: the document sits above the prompt on mobile. At `lg+`, the document and the choices sit side by side (`grid-cols-2 gap-6`, document first) so there is no scrolling between reading and deciding.

**`vocabulary` → an object or sign, then choice cards.**

- If there is a stimulus (usually `sign` or `notice`), render it as above, at `SignPlate` size `text-2xl` (the "object").
- If `stimulus = null`, the prompt stands alone under the scene.
- Choices: `ChoiceGroup layout='grid'`, `grid-cols-2` when every option is ≤ 18 characters (single words), otherwise a stack. Cards `min-h-14`, text centred.

**Listening (any choice type whose `stimulus.kind = audio`) → a platform announcement.**

- **Announcement panel:** `bg-ink-950/90 rounded-card border border-ink-600 p-4`. Header: a `Volume2` icon + `speaker` ("Station announcer", `text-xs uppercase font-bold text-fog-200`) + the waveform (Should). Then the **Listen** button (secondary `lg`, full width on mobile).
- **Playback:** `speechSynthesis.speak(new SpeechSynthesisUtterance(audio_script))`, with `rate = stimulus.rate`, `lang = 'en-GB'`, and a voice that is the first `en-GB` voice, else the first `en-*`, else the default. Pressing Listen while speaking cancels and restarts.

| State | Button label | Other |
|---|---|---|
| Idle (never played) | **Listen** | Waveform bars at rest |
| Speaking | **Listening…** (still pressable = restart) | Waveform animates (Should); `aria-live` status "Playing the announcement." |
| Played | **Listen again** (unlimited, PD-013) | — |
| Unavailable (PD-014) | Button hidden | `InlineNotice info`: "Audio isn't available on this device" + the announcement as text in a `TimetableBoard`-styled panel (`font-sans`, not mono, for readability) headed by `speaker`. The story continues. |

- **Unavailable means** `!('speechSynthesis' in window)`, or the utterance fires `onerror` with an error other than `interrupted` / `canceled`. After the first failure, switch to the fallback for the rest of the session.
- Choices are enabled before the first Listen: the student may answer. The prompt sits after the panel, so it is read in order.
- **No transcript is ever rendered** outside the fallback. The transcript appears later only in "Checkpoints to revisit".

#### 9.3.5 Mission Player states

| State | Spec |
|---|---|
| Initial loading (no StateView yet) | Backdrop `concourse_night`, the board as a skeleton (`— · —`), Maya curious with the bubble "One moment…". No blocking spinner. |
| Between nodes | The current scene stays visible and the controls are disabled (`aria-busy`). After 1 s, the bubble shows "One moment…" (`kind='waiting'`). |
| Request failed (network / 5xx / timeout 15 s) | `InlineNotice problem` above the ActionBar: "The signal dropped. Your place in the story is saved." + **Try again** (retries the same request with the same body). The selection and typed text are kept. |
| 409 (any) | Silent: render `details.state` and continue (§8 focus rules). The student never sees a conflict. |
| 404 | Replace the column with `InlineNotice`: "We couldn't find this mission run." + **Back to the English World**. Keep the backdrop. |
| 401 | Route to Check-in with the session-ended notice. |
| Offline | `OfflineBanner` with the text "The signal dropped. Your place in the story is saved."; the Confirm/Continue failure falls into the error state above. |
| Empty | Not applicable. |

### 9.4 Ending

**Layout.**

- Full-bleed backdrop from `scene.backdrop` (`train_carriage` or `night_bus` suggested).
- Column `max-w-reading mx-auto px-4 pt-[28vh]`:
  - The ending kicker "The end of the night" (`text-xs uppercase tracking-board text-fog-200`).
  - The **ending title** (`font-display text-3xl`, e.g. "Night Bus").
  - The final `DepartureBoard` (inline, left-aligned).
  - The `DialogueBox` with the closing lines.
  - Maya's closing line: `MayaPortrait` 96 px (`maya.mood`, usually proud) + bubble.
  - Then the actions: primary `lg` **Submit mission** (full width on mobile) with the helper line below it: "Maya will read your Diary and prepare your Mission Report." (`text-sm text-fog-200`).
- **No score, level, count or "results" word** (PD-004). No confetti.
- The three endings share one layout and differ only by backdrop, title and lines. The night bus is as warm as the others: the amber bus windows are the brightest thing on screen.

| State | Spec |
|---|---|
| Submitting | The button is disabled with the label "Maya is reading your Diary…". The portrait switches to **curious**, with `animate-maya-idle` (Should). `role="status"` announces the same text. Up to ~10 s; never a spinner alone. |
| Error | `InlineNotice problem`: "Your Diary is safe, but we couldn't finish the report. Try again." + **Try again** (submit is idempotent). |
| Reload / return from "Waiting to submit" | The same screen (the StateView with `status=completed`). |
| `status = submitted` | Redirect to the Mission Report. |

### 9.5 Mission Report

**Layout.**

- Shell.
- Column `max-w-player mx-auto`.
- Blocks in the fixed order of PD-001, separated by `border-t border-ink-600 pt-8 mt-8`.
- **No tabs, accordions or "show more" anywhere** (everything visible; PRODUCT §5.5).
- The page `h1` is the report label.

```
┌──────────────────────────────────────────────┐ 360 px
│ ENGLISH ASSESSMENT · MISSION REPORT          │ kicker text-xs fog-200
│ A2 · The Last Train — 70%                    │ h1 font-display text-2xl (md: 3xl)
│ ┌────────────┬────────────┬────────────┐     │ 3 stat tiles, grid-cols-3
│ │Global score│  Correct   │ Incorrect  │     │ label text-xs
│ │    70%     │     7      │     3      │     │ value text-4xl / 2xl tabular-nums
│ └────────────┴────────────┴────────────┘     │
│ Result per skill                             │ h2 (plain)
│ Grammar      3 of 4                   75%    │ SkillBar md
│ ████████████████████░░░░░░░                  │
│ Listening    1 of 2                   50%    │
│ Reading      2 of 2                  100%    │
│ Vocabulary   1 of 2                   50%    │
│ Speaking isn't measured in this mission yet. │ muted note (PD-017)
│ Suggested level                              │ h2
│ ┌────┐ 70% points to B1. B1 needs 2 of 3 B1  │ CEFR chip font-display 3xl
│ │ A2 │ checkpoints — you had 1 — so your     │ + reason verbatim (PD-015)
│ └────┘ suggested level is A2.                │
│ Attempt record                               │ h2, <dl> 2 cols
│ Attempt        3                             │
│ Submitted      24 Sep 2026 · 21:58           │ local time
│ Ending         Made It, With Maya            │
│ Story-minutes  16                            │
│ Maya's shortcut Used                         │
│ Hints from Maya 2                            │
├──────────────────────────────────────────────┤
│ (◕‿◕) Maya                                   │ portrait 96 + lamp glow
│ "You can follow signs and short messages     │ summary font-display text-xl (md: 2xl)
│  without help. …"                            │
│ Strongest tonight   Reading                  │ two rows, text-lg
│ To practise next    Listening                │
│ Tonight, listen for numbers first, then      │ recommendation text-lg
│ names.                                       │
│ About this feedback: Written by Maya using   │ footnote text-xs fog-400
│ Claude.                                      │
├──────────────────────────────────────────────┤
│ Maya has prepared your next mission          │ h2
│ ┌──────────────────────────────────────────┐ │ compact MissionCard
│ │ NIGHT RADIO            [Listening]       │ │
│ │ It trains listening, the skill that was  │ │ next_mission.reason
│ │ hardest tonight.                         │ │
│ │ [pen] Maya is preparing this mission.        │ │ or [lock] + unlock_hint
│ └──────────────────────────────────────────┘ │
├──────────────────────────────────────────────┤
│ Diary                                        │ h2
│ 21:47 ┃ STATION CONCOURSE                    │ board-font amber time │ rail
│       ┃ We reached the concourse with …      │
│ 21:47 ┃ PLATFORM 6                           │
│       ● An announcement echoed across …      │ checkpoint node on the rail
│       ┃ [MULTIPLE CHOICE · LISTENING · A1]   │ Tag
│       ┃ ○ Missed   [bulb] Maya's hint            │ OutcomeMarker + hint marker
│ 21:58 ┃ ARCADE                               │
│       ┃ [steps] Maya's shortcut                    │ rescue marker
│   …   ┃                                      │
├──────────────────────────────────────────────┤
│ Checkpoints to revisit                       │ h2
│ ┌ paper card ──────────────────────────────┐ │ surface-paper
│ │ MULTIPLE CHOICE · LISTENING · A1         │ │
│ │ Which platform does the announcer say?   │ │
│ │ Transcript: "…"                          │ │ listening only
│ │ Your answer     Platform two             │ │
│ │ Correct answer  Platform six             │ │
│ │ Why: The announcer says 'six'; …         │ │
│ │ Maya's tip: Listen for the number, …     │ │
│ └──────────────────────────────────────────┘ │
│ [ Back to the English World ] [See your      │ primary + secondary; stacked on mobile
│                                progress ]    │
└──────────────────────────────────────────────┘
```

Block details:

1. **The result.**
   - Stat tiles: `bg-ink-800 rounded-card p-3 text-center`. Label `text-xs uppercase text-fog-200` ("Global score", "Correct", "Incorrect"). Value `font-display` (Global score `text-4xl text-amber-400`; the counts `text-2xl md:text-3xl text-fog-50`). Correct and Incorrect share the same neutral style: no green/red here either.
   - Suggested level: the chip is `size-16 rounded-card bg-ink-950 shadow-board font-display text-3xl text-amber-400 grid place-items-center`, with the `cefr` display label. The `reason` is rendered verbatim.
   - Attempt record `<dl>`:
     - "Attempt" = `attempt_number`.
     - "Submitted" = local date and time `D MMM YYYY · HH:mm`.
     - "Ending" = `ending.title`.
     - "Story-minutes" = `story_minutes_used`.
     - "Maya's shortcut" = "Used" / "Not used".
     - "Hints from Maya" = `hints_received`.
2. **Maya's interpretation.**
   - Portrait mood rule (UI-only, deterministic): `score_pct ≥ 70` → proud, otherwise encouraging (see §11).
   - `summary` is in the large voice. `strength` and `challenge` are mapped to display names (Grammar, Listening, Reading, Vocabulary) under the labels "Strongest tonight" and "To practise next". Then the `recommendation`.
   - Footnote by `feedback_source.status`: `ready` → "About this feedback: Written by Maya using {provider_label}."; `fallback` → "About this feedback: Written by Maya from her notebook (offline feedback)." It is never styled as an error.
3. **Next mission.** A compact card with `title`, skill tags, `reason`, and the state line (`in_preparation` → `NotebookPen` + "Maya is preparing this mission."; `locked` → `Lock` + `unlock_hint`). No CTA (not playable, PD-007).
4. **Diary** (`<ol>`).
   - A left rail (`border-l-2 border-ink-600`, `ml-14`). The time column is `w-14 font-board text-amber-400 text-sm`.
   - Each entry: the location (`text-xs uppercase tracking-board text-fog-200`) and `text` (`text-base`).
   - Checkpoint entries: a 10 px rail dot and the `Tag` "{Type} · {Skill} · {CEFR}", with type display names "Multiple choice", "Fill in the blank", "Comprehension", "Vocabulary" (PD-029). Then the `OutcomeMarker`.
   - `maya_decision = hint` → `Lightbulb` + "Maya's hint". `rescue` → `Footprints` + "Maya's shortcut". Both in `maya-300` text, with icon and word.
   - The last entry (the ending) shows the ending title in `font-display`.
   - It reads like a journal: past tense lines from content, no "Q1…Q10" numbering.
5. **Checkpoints to revisit.**
   - One paper card per `missed` item: `surface-paper bg-paper-50 text-paper-ink rounded-card p-4`.
   - Contents: the `Tag` (paper variant: `border-paper-muted text-paper-muted`) → the prompt (`font-bold`; `fill_blank` shows `___` literally) → the stimulus, compact (audio → "Transcript" + `audio_script` in italics, speaker label; other kinds → the text in a `paper-300` bordered box) → a `<dl>` with "Your answer" and "Correct answer" (the labels carry the meaning; the values are `font-bold`, same color) → "Why:" + `explanation` → "Maya's tip:" + `maya_tip`.
   - **Empty:** "Nothing to revisit tonight. You understood every checkpoint."

**Actions**: at the end, **Back to the English World** (primary) and **See your progress** (secondary). Stacked full width on mobile, inline at `sm+`.

| State | Spec |
|---|---|
| Loading | Skeletons in block order: label line, 3 tiles, 4 bars, level chip + 2 lines, `dl` 6 lines, portrait + 3 lines, card, 5 diary rows. Arriving from Submit, the Ending's loading state covers it (don't show both). |
| Error (fetch) | "We couldn't open this Mission Report. Try again." + **Try again**. |
| 404 | "We couldn't find this Mission Report." + **Back to the English World** (same text for not-owned and missing). |
| 409 `MISSION_NOT_FINISHED` | Redirect to the Mission Player (it renders the Ending when `completed`). |
| Offline | `OfflineBanner` + the error state on a failed fetch. |
| Empty | Not applicable. |

### 9.6 Progress

**Layout.**

- Shell, `max-w-world`.
- `h1` "Progress".
- Order: open-attempt row → "Your English today" → **Attempt history** → "Maya's notes".
- `lg+`: the profile and Maya's notes sit side by side (`grid-cols-2`) under the table.

- **Open attempt** (if `open_attempt`): a `bg-ink-800 rounded-card p-4 border-l-4 border-amber-400` row.
  - `in_progress` → "In progress — {mission_title}" + a board chip with `clock.label` + **Continue your mission**.
  - `completed` → "Waiting to submit — {mission_title}" + **Submit mission**.
  - Both route to the player.
- **Your English today** (profile): four `SkillBar md` + "Based on your last {n} mission(s)."
- **Attempt history** (plain `h2`). A `<table>` with `<caption class="sr-only">Attempt history, newest first</caption>` and a visible note "Newest first" (`text-xs text-fog-400`).

  | Breakpoint | Columns |
  |---|---|
  | < 768 px (fits 328 px) | **Attempt** (link "Attempt 4" + date `24 Sep` below, `text-sm`) · **Level** (`suggested_cefr` chip + `score_pct%` below) · **Gr** · **Li** · **Re** · **Vo** (`<abbr title="Grammar">`, etc.) |
  | ≥ 768 px | Attempt · Date · Mission · Ending · Result (`label`) · Correct · Incorrect · Grammar · Listening · Reading · Vocabulary |

  - Per-skill cells: `pct%` (`tabular-nums text-sm`) with a micro-bar under it (`h-1 bg-ink-700`, fill `bg-amber-400` at `pct%` width, `aria-hidden`). Reading down a column is the trend (no chart library).
  - The level column/label per row is the suggested-level history.
  - Row: `hover:bg-ink-700`; the link in the first cell opens `/reports/{attempt_id}` (the whole row is clickable via an `::after` overlay on the link, so there is still only one tab stop per row).
  - `attempt_number` is per mission, so show "Attempt {n}" plus the mission title on `md+` (mobile: all rows are The Last Train in the MVP).
- **Maya's notes**: a list of up to 5 notes, newest first, each a `MayaBubble`-styled card (no portrait per note; one 56 px portrait by the heading) with the date in `text-xs text-fog-400`. If there are none (but history exists): "Maya hasn't written in her notebook yet."

| State | Spec |
|---|---|
| Loading | Skeleton: the open-attempt row, 4 bars, 4 table rows, 2 notes (the "chart placeholder" of PRODUCT §5.6 = the table skeleton). |
| Empty (`history = []` and no open attempt) | Maya curious (96 px) + "Your story starts tonight. Play The Last Train and your progress will appear here." + **Go to the English World** (primary). If there is an open attempt but no history, show the open-attempt row above the empty message. |
| Error | "We couldn't load your progress. Try again." + **Try again**. |
| Offline | `OfflineBanner` + the error state on a failed fetch. |

No ranks, no comparisons with other students, no chart library. A Chart is a Should after G3: an inline SVG polyline per skill, built from the same rows.

### 9.7 Teacher landing (PD-019, Must if the stretch is not built)

> Superseded 2026-09-25: the §9.8 Teacher view is built, so teachers and admins land on it. Kept for the record.

- Shell without the English World/Progress nav.
- `h1` "Hello, {display_name}."
- Body: "The teacher view isn't part of this build. Your roles are shown through the API." + **Check out**.
- A student opening a teacher URL is redirected to the English World with the info notice "That page is for teachers."

### 9.8 Stretch — Teacher view

> Built 2026-09-25 (frontend-engineer, `frontend/src/features/teacher/TeacherPage.tsx`). Choices made in the build:
> - `h1` "Hello, {display_name}."; each class is an `h2` with a quiet line "{teacher_name} · {n} student(s)" (useful for an admin, who sees every class).
> - The small-screen Level chip is the part of `latest_label` before the first " · " (a layout-only split, like the story clock); `md+` shows the label verbatim.
> - Missing values (no report, no profile, no activity) show "—"; the table has no links or buttons (PD-030).
> - The picker keeps the selected class in `?class=`; a teacher with no classes sees "No classes yet."
> - The table caption is "Students in {class name}"; the student name is the row header (`th scope="row"`).

- Shell (teacher nav: "Classes").
- A class picker (a `<select>` styled as `secondary`) when there are 2+ classes.
- A table, the same pattern as Attempt history:
  - < 768: Student · Level (from `latest_label` chip) · Gr · Li · Re · Vo.
  - ≥ 768: Student · Missions played · Latest report · Grammar · Listening · Reading · Vocabulary · Last activity.
- Profile cells use the micro-bars. There is no drill-in (PD-030).
- States: loading (skeleton rows), empty "No students in this class yet.", error "We couldn't load your class." + **Try again**, not-found → the same error copy.

### 9.9 Stretch — Simulated replay (demo mode only)

- Reached from "Watch a simulated run" (a ghost link at the bottom of the English World, only when `demo_mode`).
- Page: `h1` "Simulated run". A profile segmented control (A1 · A2 · B1 · B2 · A2 weak listening; `role="radiogroup"`) + **Run simulation** (primary).
- Result: the ending title, "Story-minutes used: N", then a `DiaryTimeline`-styled list from `steps`:
  - the clock;
  - `node_id` as muted text;
  - the `OutcomeMarker` for checkpoints;
  - the Maya decision marker (quiet shows nothing; hint / rescue as in the Diary);
  - a small mood portrait (40 px).
- A **Play** button reveals the steps one by one every 400 ms (instant under reduced motion); **Show all** reveals them all. Never options, answers or prompts.
- States: loading "Running the simulation…", error "The simulation couldn't run." + **Try again**, hidden when not in demo mode.

### 9.10 Global

- **Route guard loading:** `ink-900` screen + "One moment…" (`text-fog-200`, centred, `role="status"`) after 300 ms.
- **Unknown route:** "This platform doesn't exist." + **Back to the English World** (students) / **Check in** (anonymous).
- **Offline:** `OfflineBanner` "You're offline. We'll reconnect when the signal comes back." (in the Mission Player: "The signal dropped. Your place in the story is saved.").

---

## 10. Microcopy (every user-facing string introduced by this spec; PRODUCT §10 wins on conflict)

| Where | String |
|---|---|
| Check-in | "BOARDING PASS" · "Tonight, your English gets you home." · "Email" · "Password" · "Show password" / "Hide password" · **Check in** · "Checking in…" |
| Check-in validation | "Enter your email." · "Enter an email like name@example.com." · "Enter your password." |
| Check-in errors | "That email and password don't match." · "Too many tries. Wait a minute and check in again." · "We couldn't reach Global AI. Check your connection and try again." · "Your session ended. Check in again — your mission is saved." |
| Demo panel | "Demo accounts" · **Use this account** · "Password for all demo accounts:" |
| Shell | "Global AI Missions" · **English World** · **Progress** · **Check out** |
| World | "Welcome, {name}." · "Maya" · "Missions" · **Start mission** · **Continue your mission** · **Submit mission** · **Play again** · **View Mission Report** · "Opening…" · "Ending reached: {title}" · "Played {n} time" / "Played {n} times" · "Maya is preparing this mission." · "Maya's pick" · "Watch a simulated run" |
| Card strip | "AVAILABLE" · "IN PROGRESS" · "WAITING TO SUBMIT" · "COMPLETED" · "LOCKED" · "IN PREPARATION" |
| Snapshot | "Your English today" · "Based on your last {n} mission(s) · {m} mission(s) played" · **See your progress** · "Your story starts tonight. Your progress will appear here after your first mission." |
| World error | "The lights went out for a moment. Try again." · **Try again** |
| Player | **Pause** · **Continue** · **Confirm** · "One moment…" · "Maya's shortcut" · "Type the missing words." · "Your words for the gap" (a11y) · **Listen** · "Listening…" · **Listen again** · "Playing the announcement." (a11y) · "Audio isn't available on this device" · "Timetable" (a11y) |
| Player errors | "The signal dropped. Your place in the story is saved." · "We couldn't find this mission run." · **Back to the English World** |
| Ending | "The end of the night" · **Submit mission** · "Maya will read your Diary and prepare your Mission Report." · "Maya is reading your Diary…" · "Your Diary is safe, but we couldn't finish the report. Try again." |
| Report | "English Assessment · Mission Report" · "Global score" · "Correct" · "Incorrect" · "Result per skill" · "{x} of {n}" · "Speaking isn't measured in this mission yet." · "Suggested level" · "Attempt record" · "Attempt" · "Submitted" · "Ending" · "Story-minutes" · "Maya's shortcut" · "Used" / "Not used" · "Hints from Maya" · "Strongest tonight" · "To practise next" · "About this feedback: Written by Maya using {provider_label}." · "About this feedback: Written by Maya from her notebook (offline feedback)." · "Maya has prepared your next mission" · "Diary" · "Understood" · "Missed" · "Maya's hint" · "Checkpoints to revisit" · "Transcript" · "Your answer" · "Correct answer" · "Why:" · "Maya's tip:" · "Nothing to revisit tonight. You understood every checkpoint." · **See your progress** |
| Report errors | "We couldn't open this Mission Report. Try again." · "We couldn't find this Mission Report." |
| Progress | "Progress" · "In progress — {mission}" · "Waiting to submit — {mission}" · "Your English today" · "Attempt history" · "Newest first" · "Attempt {n}" · "Maya's notes" · "Maya hasn't written in her notebook yet." · "Your story starts tonight. Play The Last Train and your progress will appear here." · **Go to the English World** · "We couldn't load your progress. Try again." |
| Type names (report only) | "Multiple choice" · "Fill in the blank" · "Comprehension" · "Vocabulary" |
| Skill names | "Grammar" · "Listening" · "Reading" · "Vocabulary" (abbr. "Gr", "Li", "Re", "Vo") |
| Teacher | "Hello, {name}." · "The teacher view isn't part of this build. Your roles are shown through the API." (superseded, §9.7) · "That page is for teachers." · "Classes" · "Class" (picker label) · "Students in {class}" (caption) · "Student" · "Missions played" · "Latest report" · "Level" · "Last activity" · "{teacher} · {n} student(s)" · "No classes yet." · "No students in this class yet." · "We couldn't load your class." |
| Replay | "Simulated run" · **Run simulation** · "Running the simulation…" · **Play** · **Show all** · "The simulation couldn't run." |
| Global | "One moment…" · "This platform doesn't exist." · "You're offline. We'll reconnect when the signal comes back." |

Server-built strings are rendered **verbatim** and never rebuilt on the client (F-06): `clock.label`, report `label`, `suggested_level.reason`, `latest_label`, `greeting.text`, `unlock_hint`, `next_mission.reason`, and all scene and Maya lines.

---

## 11. Handoff notes and open questions

**For the frontend-engineer (must know)**

1. `tokens.css` uses `@theme static` and **resets the default palette** (`--color-*: initial`).
   - `slate-*`, `red-*`, `green-*` and so on no longer exist. The skeleton's placeholder `bg-slate-950` in `App.tsx` now generates nothing; replace it with `bg-ink-900` (the `html` base already paints `ink-900`).
   - `bg-transparent`, `text-current` and `inherit` still work. There is no `white`: paper inputs use `bg-paper-50` + `border-paper-muted`.
2. Add the Google Fonts `<link>` (§2) to `frontend/index.html`, and the dependency `lucide-react` (MIT).
3. `tokens.css` imports `backdrops.css`; nothing else to wire. Render backdrops as `<div className="backdrop" data-backdrop={key} aria-hidden />`. The SVGs are inlined as data URIs by Vite.
4. Maya: `import curious from '../assets/maya/curious.svg'` (Vite URL import) → `<img src={curious} alt="Maya, looking curious" />`. Map `mood → src` in one object in `components/`.
5. Global focus ring and reduced-motion rules are in `tokens.css` (`@layer base`). Add the class `surface-paper` to paper containers so their focus ring turns ink.
6. Durations for Framer Motion: the constants in §7 (seconds). Wrap the app in `<MotionConfig reducedMotion="user">`.
7. Render server strings verbatim (§10 last line). The client never computes %, level or correctness; bar widths are the only arithmetic (`width: pct%`).
8. Speech: `en-GB` voice preference, `rate` from the stimulus, restart on re-press, and the fallback rules in §9.3.4.
9. Verified here: `npm run build`, `npm run lint`, `npm run format:check` and `npm test` pass with these files. `tokens.css` + `backdrops.css` add about 2 KB gzip to the CSS.

**Backdrop keys** (§6) are a proposal for `docs/design/BACKDROPS.md` (narrative-designer): `concourse_night` (default), `ticket_hall`, `platform`, `platform_empty`, `arcade_shortcut`, `street_night`, `night_bus`, `train_carriage`.

**Open questions for product** (defaults already taken so nobody is blocked; change them if you disagree)

1. **Report portrait mood.** The Report has no Maya mood field. Default: proud when `score_pct ≥ 70`, otherwise encouraging (UI-only). Alternative: a `mood` field in `interpretation` (a CR to the tech-lead).
2. **Story-minutes on the report.** `attempt_record` has `story_minutes_used` but not `minutes_available`, so the UI shows "16" rather than "16 of 18". Keep it, or add `minutes_available` (a CR)?
3. **Zone display name.** `world_zone` is a slug; the UI title-cases it ("the-station" → "The Station"). Fine, or add a `world_zone_label` to the catalog?
4. **Listening before answering.** Default: the choices are enabled before the first **Listen** (nothing forces a play). Confirm, or require one play before Confirm?
5. **Reaction line after a reload.** `maya_line` exists only in the answer response; a reload on the consequence node shows only `state.maya.line`. Acceptable for the MVP?
6. **World greeting heading.** "Welcome, {name}." above Maya's line (the first-meeting line starts "Hi, I'm Maya", so a "Hi, {name}" heading would repeat itself). OK?
7. **Diary length.** All steps are shown (about 25 rows) with no collapsing, per PRODUCT §5.5. OK at 360 px? The alternative is to show only checkpoints and hint/rescue moments.
8. **Fonts.** Google Fonts CDN for the MVP (a third-party request on every load). Self-hosting via `@fontsource` is the production answer; a DECISIONS.md line may be worth it.
