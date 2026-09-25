import { Lock, NotebookPen, TrainFront } from 'lucide-react'
import { Link, useNavigate } from 'react-router'

import type { CardState, MissionCard } from '../../api/types'
import { Backdrop } from '../../components/Backdrop'
import { Button } from '../../components/Button'
import { buttonClasses } from '../../components/buttonClasses'
import { MayaPortrait } from '../../components/Maya'
import { Tag } from '../../components/Tag'
import { cefrLabel, plural, skillName, zoneName } from '../../lib/format'
import { playerPath, reportPath, useStartMission } from '../mission/navigation'

const STRIP: Record<CardState, { label: string; tone: string }> = {
  available: { label: 'AVAILABLE', tone: 'text-amber-400' },
  in_progress: { label: 'IN PROGRESS', tone: 'text-amber-400' },
  waiting_to_submit: { label: 'WAITING TO SUBMIT', tone: 'text-amber-400' },
  completed: { label: 'COMPLETED', tone: 'text-fog-200' },
  locked: { label: 'LOCKED', tone: 'text-fog-400' },
  in_preparation: { label: 'IN PREPARATION', tone: 'text-maya-300' },
}

export function MayasPickMarker() {
  return (
    <span className="inline-flex items-center gap-1.5 rounded-full border border-maya-300 bg-ink-950 py-0.5 pr-2.5 pl-0.5 text-xs font-bold text-maya-300">
      <MayaPortrait mood="encouraging" size={20} decorative />
      Maya&apos;s pick
    </span>
  )
}

export function MissionCardView({ card }: { card: MissionCard }) {
  const start = useStartMission()
  const navigate = useNavigate()
  const strip = STRIP[card.state]
  const locked = card.state === 'locked'
  const featured = card.playable
  const cefr = `${cefrLabel(card.cefr_range.min)}–${cefrLabel(card.cefr_range.max)}`
  const open = card.open_attempt

  return (
    <article
      aria-labelledby={`card-${card.mission_id}`}
      className={`relative overflow-hidden rounded-card shadow-card ${featured ? 'md:col-span-2' : ''} ${
        locked ? 'border border-dashed border-line-strong bg-ink-900' : 'bg-ink-800'
      } ${card.is_maya_pick ? 'shadow-lamp' : ''}`}
    >
      {featured ? (
        <div className="relative h-24">
          <Backdrop backdropKey="platform" />
        </div>
      ) : null}
      <div className="flex items-center justify-between gap-2 bg-ink-950 px-4 py-1.5 font-board text-xs tracking-board uppercase md:px-5">
        <span className={`inline-flex items-center gap-1.5 ${strip.tone}`}>
          {card.state === 'locked' ? <Lock aria-hidden="true" className="size-4" /> : null}
          {card.state === 'in_preparation' ? (
            <NotebookPen aria-hidden="true" className="size-4" />
          ) : null}
          {strip.label}
        </span>
        <span className="text-fog-200">{zoneName(card.world_zone)}</span>
      </div>
      <div className="space-y-3 p-4 md:p-5">
        <div className="flex items-start justify-between gap-2">
          <h3 id={`card-${card.mission_id}`} className="font-display text-xl font-semibold">
            {card.title}
          </h3>
          {card.is_maya_pick ? <MayasPickMarker /> : null}
        </div>
        <div className="flex flex-wrap gap-2">
          {card.skill_focus.map((skill) => (
            <Tag key={skill} text={skillName(skill)} />
          ))}
          <Tag text={cefr} />
        </div>
        <p className="text-fog-200">{card.teaser}</p>

        {card.state === 'in_progress' && open ? (
          <p className="inline-block rounded-board bg-ink-950 px-2 py-1 font-board text-sm tracking-board text-amber-400">
            {open.clock.time} · {open.location}
          </p>
        ) : null}
        {card.state === 'waiting_to_submit' && open?.ending ? (
          <p>Ending reached: {open.ending.title}</p>
        ) : null}
        {(card.state === 'in_progress' || card.state === 'waiting_to_submit') &&
        card.latest_result ? (
          <p className="text-sm text-fog-400">{card.latest_result.label}</p>
        ) : null}
        {card.state === 'completed' && card.latest_result ? (
          <div>
            <p className="text-lg font-bold">{card.latest_result.label}</p>
            <p className="text-sm text-fog-400">
              Played {card.attempts_submitted} {plural(card.attempts_submitted, 'time', 'times')}
            </p>
          </div>
        ) : null}
        {card.state === 'locked' ? (
          <p className="flex items-start gap-2 text-fog-200">
            <Lock aria-hidden="true" className="mt-1 size-4 shrink-0" />
            {card.unlock_hint}
          </p>
        ) : null}
        {card.state === 'in_preparation' ? (
          <p className="flex items-center gap-2 text-fog-200">
            <NotebookPen aria-hidden="true" className="size-4 shrink-0" />
            Maya is preparing this mission.
          </p>
        ) : null}

        <div className="flex flex-col gap-2 sm:flex-row">
          {card.state === 'available' || card.state === 'completed' ? (
            <Button
              size="lg"
              icon={<TrainFront className="size-5" />}
              loading={start.isPending}
              loadingLabel="Opening…"
              onClick={() => start.mutate(card.mission_id)}
            >
              {card.state === 'available' ? 'Start mission' : 'Play again'}
            </Button>
          ) : null}
          {(card.state === 'in_progress' || card.state === 'waiting_to_submit') && open ? (
            <Button
              size="lg"
              onClick={() => navigate(playerPath(card.mission_id, open.attempt_id))}
            >
              {card.state === 'in_progress' ? 'Continue your mission' : 'Submit mission'}
            </Button>
          ) : null}
          {card.state === 'completed' && card.latest_result ? (
            <Link
              to={reportPath(card.latest_result.attempt_id)}
              className={buttonClasses('secondary', 'lg')}
            >
              View Mission Report
            </Link>
          ) : null}
        </div>
        {start.isError ? (
          <p role="alert" className="text-sm">
            The lights went out for a moment. Try again.
          </p>
        ) : null}
      </div>
    </article>
  )
}
