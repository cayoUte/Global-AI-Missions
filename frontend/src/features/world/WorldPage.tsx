import { useQuery } from '@tanstack/react-query'
import { ArrowRight } from 'lucide-react'
import { Link, useLocation } from 'react-router'

import { api } from '../../api/client'
import { WORLD_KEY } from '../../api/queryKeys'
import type { Greeting, Snapshot } from '../../api/types'
import { AppShell, PageHeading } from '../../components/AppShell'
import { Backdrop } from '../../components/Backdrop'
import { Button } from '../../components/Button'
import { InlineNotice } from '../../components/InlineNotice'
import { MayaPortrait } from '../../components/Maya'
import { Skeleton } from '../../components/Skeleton'
import { SkillBar } from '../../components/SkillBar'
import { plural } from '../../lib/format'
import type { CheckInState } from '../auth/session'
import { MissionCardView } from './MissionCardView'

export function WorldPage() {
  const world = useQuery({ queryKey: WORLD_KEY, queryFn: () => api.world() })
  const arrival = (useLocation().state as CheckInState | null) ?? {}

  return (
    <AppShell>
      <PageHeading srOnly>English World</PageHeading>
      {arrival.notice ? (
        <InlineNotice tone="info" message={arrival.notice} className="mb-6" />
      ) : null}
      {world.isPending ? (
        <WorldSkeleton />
      ) : world.isError ? (
        <InlineNotice
          tone="problem"
          message="The lights went out for a moment. Try again."
          action={
            <Button
              variant="secondary"
              loading={world.isFetching}
              loadingLabel="One moment…"
              onClick={() => world.refetch()}
            >
              Try again
            </Button>
          }
        />
      ) : (
        <div className="grid gap-8 lg:grid-cols-[1fr_20rem]">
          <div className="space-y-8">
            <GreetingCard name={world.data.student.display_name} greeting={world.data.greeting} />
            <section aria-labelledby="missions-heading" className="space-y-4">
              <h2 id="missions-heading" className="font-display text-2xl font-semibold">
                Missions
              </h2>
              <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                {world.data.cards.map((card) => (
                  <MissionCardView key={card.mission_id} card={card} />
                ))}
              </div>
            </section>
          </div>
          <div>
            <SnapshotCard snapshot={world.data.snapshot} />
          </div>
        </div>
      )}
    </AppShell>
  )
}

function GreetingCard({ name, greeting }: { name: string; greeting: Greeting }) {
  return (
    <section
      aria-label="Maya's greeting"
      className="relative overflow-hidden rounded-card bg-ink-800 p-4 shadow-card md:p-6"
    >
      <Backdrop backdropKey="concourse_night" className="opacity-60" />
      <div className="relative flex items-start gap-4">
        <MayaPortrait mood={greeting.mood} size={72} className="md:hidden" />
        <MayaPortrait mood={greeting.mood} size={96} className="hidden md:block" />
        <div className="min-w-0 space-y-2">
          <p className="font-display text-2xl font-semibold">Welcome, {name}.</p>
          <p className="text-xs font-bold tracking-wide text-maya-300 uppercase">Maya</p>
          <p className="text-lg">{greeting.text}</p>
        </div>
      </div>
    </section>
  )
}

function SnapshotCard({ snapshot }: { snapshot: Snapshot }) {
  const played = snapshot.missions_played
  return (
    <section
      aria-labelledby="snapshot-heading"
      className="space-y-4 rounded-card bg-ink-800 p-4 lg:sticky lg:top-20"
    >
      <h2 id="snapshot-heading" className="font-bold">
        Your English today
      </h2>
      {played === 0 || !snapshot.profile ? (
        <p className="text-fog-200">
          Your story starts tonight. Your progress will appear here after your first mission.
        </p>
      ) : (
        <>
          {snapshot.latest_label ? (
            <p className="font-display text-xl">{snapshot.latest_label}</p>
          ) : null}
          <div className="space-y-3">
            {snapshot.profile.skills.map((s) => (
              <SkillBar key={s.skill} skill={s.skill} pct={s.pct} size="sm" />
            ))}
          </div>
          <p className="text-sm text-fog-400">
            Based on your last {snapshot.profile.based_on_attempts}{' '}
            {plural(snapshot.profile.based_on_attempts, 'mission', 'missions')} · {played}{' '}
            {plural(played, 'mission', 'missions')} played
          </p>
        </>
      )}
      <Link
        to="/progress"
        className="inline-flex min-h-11 items-center gap-2 font-bold text-amber-400 hover:text-amber-200"
      >
        See your progress <ArrowRight aria-hidden="true" className="size-5" />
      </Link>
    </section>
  )
}

function WorldSkeleton() {
  return (
    <div className="grid gap-8 lg:grid-cols-[1fr_20rem]" aria-busy="true">
      <div className="space-y-8">
        <div className="flex gap-4 rounded-card bg-ink-800 p-4 md:p-6">
          <Skeleton className="size-[72px] shrink-0 rounded-full" />
          <div className="flex-1 space-y-3">
            <Skeleton className="h-8 w-2/3" />
            <Skeleton className="h-4 w-1/4" />
            <Skeleton className="h-6 w-full" />
          </div>
        </div>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <Skeleton className="h-64 md:col-span-2" />
          <Skeleton className="h-56" />
          <Skeleton className="h-56" />
          <Skeleton className="h-56" />
          <Skeleton className="h-56" />
        </div>
      </div>
      <Skeleton className="h-64" />
    </div>
  )
}
