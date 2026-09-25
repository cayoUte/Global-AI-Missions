import { useMutation } from '@tanstack/react-query'
import { useReducedMotion } from 'framer-motion'
import { Footprints, Lightbulb } from 'lucide-react'
import { useEffect, useRef, useState, type FormEvent } from 'react'
import { Link, useSearchParams } from 'react-router'

import { api } from '../../api/client'
import type { SimulationProfile, SimulationResponse, SimulationStep } from '../../api/types'
import { AppShell, PageHeading } from '../../components/AppShell'
import { TEACHER_NAV } from '../../components/nav'
import { Button } from '../../components/Button'
import { buttonClasses } from '../../components/buttonClasses'
import { InlineNotice } from '../../components/InlineNotice'
import { MayaPortrait } from '../../components/Maya'
import { OutcomeMarker } from '../../components/OutcomeMarker'
import { Skeleton } from '../../components/Skeleton'
import { splitClockLabel } from '../../lib/format'
import { homeFor, useConfig, useMe } from '../auth/session'
import { parseSeed } from './seed'

const PROFILES: { value: SimulationProfile; label: string }[] = [
  { value: 'A1', label: 'A1' },
  { value: 'A2', label: 'A2' },
  { value: 'B1', label: 'B1' },
  { value: 'B2', label: 'B2' },
  { value: 'A2_weak_listening', label: 'A2 weak listening' },
]
const KIND_NAMES: Record<SimulationStep['kind'], string> = {
  narrative: 'Scene',
  checkpoint: 'Checkpoint',
  consequence: 'Consequence',
  ending: 'Ending',
}
const STEP_MS = 400 // one step revealed every 400 ms while playing (UI_SPEC §9.9)
/**
 * Simulated replay (PRODUCT §5.8, UI_SPEC §9.9), demo mode only: the engine's simulated student
 * plays a mission and the page replays its path. The server sends nodes, clock, outcomes and Maya's
 * decisions only; no prompts, options or answers exist in the response or on this page.
 */
export function ReplayPage() {
  const me = useMe()
  const config = useConfig()
  const [params] = useSearchParams()
  const missionId = params.get('mission')
  const home = me.data ? homeFor(me.data) : '/world'
  const student = me.data?.role === 'student'

  let body
  if (config.isPending) body = <Skeleton className="h-40" />
  else if (config.isError)
    body = (
      <InlineNotice
        tone="problem"
        message="The simulation couldn't run."
        action={
          <Button variant="secondary" onClick={() => config.refetch()}>
            Try again
          </Button>
        }
      />
    )
  else if (!config.data.demo_mode || !missionId)
    body = (
      <InlineNotice
        tone="info"
        message={
          config.data.demo_mode
            ? 'Open the simulated run from a mission in the English World.'
            : 'The simulated run is only available in demo mode.'
        }
        action={
          <Link to={home} className={buttonClasses('secondary')}>
            {student ? 'Back to the English World' : 'Back to Classes'}
          </Link>
        }
      />
    )
  else body = <Simulator missionId={missionId} />

  return (
    <AppShell navItems={student ? undefined : TEACHER_NAV} width="player">
      <div className="space-y-6">
        <PageHeading className="font-display text-2xl font-semibold">Simulated run</PageHeading>
        {body}
      </div>
    </AppShell>
  )
}

function Simulator({ missionId }: { missionId: string }) {
  const reduced = useReducedMotion() === true
  const [profile, setProfile] = useState<SimulationProfile>('A2')
  const [seedText, setSeedText] = useState('1')
  const seed = parseSeed(seedText)

  const run = useMutation({
    mutationFn: (vars: { profile: SimulationProfile; seed: number }) =>
      api.simulate(missionId, vars.profile, vars.seed),
  })

  const onSubmit = (event: FormEvent) => {
    event.preventDefault()
    if (seed === null || run.isPending) return
    run.mutate({ profile, seed })
  }

  return (
    <div className="space-y-6">
      <p className="max-w-reading text-fog-200">
        A simulated student, not a real one: the story engine plays the mission at the level you
        pick. You see the path, the story clock, what was understood or missed and what Maya
        decided. Questions and answers are never shown.
      </p>

      <form onSubmit={onSubmit} className="space-y-4 rounded-card bg-ink-800 p-4">
        <fieldset className="space-y-2">
          <legend className="text-sm font-bold">Simulated student&apos;s level</legend>
          <div className="flex flex-wrap gap-2">
            {PROFILES.map((option) => (
              <label
                key={option.value}
                className="group flex min-h-11 cursor-pointer items-center gap-2 rounded-control border border-line-strong px-3 has-checked:border-amber-400 has-checked:bg-amber-400/12 has-checked:font-bold has-focus-visible:outline-2 has-focus-visible:outline-offset-2 has-focus-visible:outline-amber-400"
              >
                <input
                  type="radio"
                  name="profile"
                  value={option.value}
                  checked={profile === option.value}
                  onChange={() => setProfile(option.value)}
                  className="sr-only"
                />
                <span
                  aria-hidden="true"
                  className="size-2.5 rounded-full border-2 border-fog-200 group-has-checked:border-amber-400 group-has-checked:bg-amber-400"
                />
                {option.label}
              </label>
            ))}
          </div>
        </fieldset>
        <div className="space-y-1">
          <label htmlFor="replay-seed" className="block text-sm font-bold">
            Seed
          </label>
          <input
            id="replay-seed"
            inputMode="numeric"
            autoComplete="off"
            value={seedText}
            onChange={(event) => setSeedText(event.target.value)}
            aria-describedby="replay-seed-help"
            aria-invalid={seed === null || undefined}
            className="min-h-11 w-40 rounded-control border border-line-strong bg-ink-900 px-3 font-board text-fog-50 tabular-nums"
          />
          <p id="replay-seed-help" className="text-sm text-fog-400">
            A whole number from 0 to 1000000. The same level and seed always replay the same run.
          </p>
        </div>
        <Button
          type="submit"
          disabled={seed === null}
          loading={run.isPending}
          loadingLabel="Running the simulation…"
        >
          Run simulation
        </Button>
      </form>

      {run.isPending ? (
        <p role="status" className="text-fog-200">
          Running the simulation…
        </p>
      ) : run.isError ? (
        <InlineNotice
          tone="problem"
          message="The simulation couldn't run."
          action={
            <Button variant="secondary" onClick={() => run.mutate(run.variables)}>
              Try again
            </Button>
          }
        />
      ) : run.data ? (
        <Result key={run.submittedAt} data={run.data} reduced={reduced} />
      ) : null}
    </div>
  )
}

/** One run's replay; remounted per run, so it starts playing from the first step. */
function Result({ data, reduced }: { data: SimulationResponse; reduced: boolean }) {
  const total = data.steps.length
  // Reduced motion shows the whole path at once (UI_SPEC §9.9).
  const [revealed, setRevealed] = useState(reduced ? total : 0)
  const [playing, setPlaying] = useState(!reduced)
  const done = revealed >= total
  const running = playing && !done
  const headingRef = useRef<HTMLHeadingElement>(null)
  const profileLabel = PROFILES.find((p) => p.value === data.profile)?.label ?? data.profile

  useEffect(() => {
    headingRef.current?.focus({ preventScroll: true })
  }, [])

  useEffect(() => {
    if (!running) return
    const timer = setInterval(() => setRevealed((n) => Math.min(total, n + 1)), STEP_MS)
    return () => clearInterval(timer)
  }, [running, total])

  const play = () => {
    if (done) setRevealed(0)
    setPlaying(!running)
  }

  return (
    <section aria-labelledby="replay-result" className="space-y-4">
      <div className="rounded-card border-l-4 border-amber-400 bg-ink-800 p-4">
        <p className="text-xs font-bold tracking-board text-fog-200 uppercase">
          Simulated student · {profileLabel} · seed {data.seed}
        </p>
        <h2
          ref={headingRef}
          id="replay-result"
          tabIndex={-1}
          className="font-display text-xl font-semibold outline-none"
        >
          Ending reached: {data.ending.title}
        </h2>
        <p className="text-fog-200">Story-minutes used: {data.story_minutes_used}</p>
      </div>

      <div className="flex flex-wrap gap-2">
        <Button variant="secondary" onClick={play}>
          {running ? 'Pause' : 'Play'}
        </Button>
        <Button
          variant="ghost"
          disabled={done}
          onClick={() => {
            setPlaying(false)
            setRevealed(total)
          }}
        >
          Show all
        </Button>
      </div>

      <ol aria-label="Simulated path" className="space-y-0">
        {data.steps.slice(0, revealed).map((step) => (
          <StepItem key={step.seq} step={step} />
        ))}
      </ol>
    </section>
  )
}

function StepItem({ step }: { step: SimulationStep }) {
  const [time, rest] = splitClockLabel(step.clock.label)
  return (
    <li className="grid grid-cols-[3.5rem_1fr]">
      <span
        className={`pt-0.5 font-board text-sm tabular-nums ${step.clock.train_departed ? 'text-fog-200' : 'text-amber-400'}`}
      >
        {time}
      </span>
      <div className="relative flex gap-3 border-l-2 border-ink-600 pb-5 pl-4">
        <div className="min-w-0 flex-1 space-y-1">
          {rest ? (
            <p className="font-board text-xs tracking-board text-fog-200 uppercase">{rest}</p>
          ) : null}
          <p className="text-sm">
            {KIND_NAMES[step.kind]} <span className="text-fog-400">· {step.node_id}</span>
          </p>
          {step.outcome ? <OutcomeMarker outcome={step.outcome} /> : null}
          {step.maya_decision === 'hint' ? (
            <p className="flex items-center gap-1.5 text-sm font-bold text-maya-300">
              <Lightbulb aria-hidden="true" className="size-4" /> Maya&apos;s hint
            </p>
          ) : null}
          {step.maya_decision === 'rescue' ? (
            <p className="flex items-center gap-1.5 text-sm font-bold text-maya-300">
              <Footprints aria-hidden="true" className="size-4" /> Maya&apos;s shortcut
            </p>
          ) : null}
        </div>
        <MayaPortrait mood={step.maya_mood} size={40} />
      </div>
    </li>
  )
}
