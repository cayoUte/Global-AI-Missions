import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router'

import { api } from '../../api/client'
import { PROGRESS_KEY } from '../../api/queryKeys'
import type { HistoryRow, ProgressResponse, SkillScore } from '../../api/types'
import { AppShell, PageHeading } from '../../components/AppShell'
import { Button } from '../../components/Button'
import { buttonClasses } from '../../components/buttonClasses'
import { InlineNotice } from '../../components/InlineNotice'
import { MayaPortrait } from '../../components/Maya'
import { Skeleton } from '../../components/Skeleton'
import { SkillBar } from '../../components/SkillBar'
import { SkillCell } from '../../components/SkillCell'
import { cefrLabel, plural, shortDate, skillAbbr, skillName, SCORED_SKILLS } from '../../lib/format'
import { playerPath, reportPath } from '../mission/navigation'

export function ProgressPage() {
  const progress = useQuery({ queryKey: PROGRESS_KEY, queryFn: () => api.progress() })
  return (
    <AppShell>
      <PageHeading className="mb-6 font-display text-2xl font-semibold">Progress</PageHeading>
      {progress.isPending ? (
        <ProgressSkeleton />
      ) : progress.isError ? (
        <InlineNotice
          tone="problem"
          message="We couldn't load your progress. Try again."
          action={
            <Button
              variant="secondary"
              loading={progress.isFetching}
              loadingLabel="One moment…"
              onClick={() => progress.refetch()}
            >
              Try again
            </Button>
          }
        />
      ) : (
        <ProgressView data={progress.data} />
      )}
    </AppShell>
  )
}

function ProgressView({ data }: { data: ProgressResponse }) {
  const open = data.open_attempt
  const empty = data.history.length === 0
  return (
    <div className="space-y-8 md:space-y-12">
      {open ? (
        <div className="flex flex-col gap-3 rounded-card border-l-4 border-amber-400 bg-ink-800 p-4 sm:flex-row sm:items-center">
          <p className="font-bold">
            {open.status === 'in_progress' ? 'In progress' : 'Waiting to submit'} —{' '}
            {open.mission_title}
          </p>
          {open.status === 'in_progress' ? (
            <span className="rounded-board bg-ink-950 px-2 py-1 font-board text-sm tracking-board text-amber-400">
              {open.clock.label}
            </span>
          ) : null}
          <Link
            to={playerPath(open.mission_id, open.attempt_id)}
            className={buttonClasses('primary', 'md', 'sm:ml-auto')}
          >
            {open.status === 'in_progress' ? 'Continue your mission' : 'Submit mission'}
          </Link>
        </div>
      ) : null}

      {empty ? (
        <div className="flex flex-col items-center gap-4 py-8 text-center">
          <MayaPortrait mood="curious" size={96} />
          <p className="max-w-reading text-lg">
            Your story starts tonight. Play The Last Train and your progress will appear here.
          </p>
          <Link to="/world" className={buttonClasses('primary', 'lg')}>
            Go to the English World
          </Link>
        </div>
      ) : (
        <>
          <section aria-labelledby="history-heading" className="space-y-3">
            <div className="flex items-baseline justify-between gap-2">
              <h2 id="history-heading" className="text-xl font-bold">
                Attempt history
              </h2>
              <p className="text-xs text-fog-400">Newest first</p>
            </div>
            <HistoryTable rows={data.history} />
          </section>

          <div className="grid gap-8 lg:grid-cols-2">
            {data.profile ? (
              <section
                aria-labelledby="profile-heading"
                className="space-y-3 rounded-card bg-ink-800 p-4"
              >
                <h2 id="profile-heading" className="text-xl font-bold">
                  Your English today
                </h2>
                {data.profile.skills.map((s) => (
                  <SkillBar key={s.skill} skill={s.skill} pct={s.pct} />
                ))}
                <p className="text-sm text-fog-400">
                  Based on your last {data.profile.based_on_attempts}{' '}
                  {plural(data.profile.based_on_attempts, 'mission', 'missions')}.
                </p>
              </section>
            ) : null}

            <section aria-labelledby="notes-heading" className="space-y-3">
              <div className="flex items-center gap-3">
                <MayaPortrait mood="encouraging" size={56} decorative />
                <h2 id="notes-heading" className="text-xl font-bold">
                  Maya&apos;s notes
                </h2>
              </div>
              {data.notes.length === 0 ? (
                <p className="text-fog-200">Maya hasn&apos;t written in her notebook yet.</p>
              ) : (
                <ul className="space-y-3">
                  {data.notes.map((note, index) => (
                    <li
                      key={index}
                      className="rounded-card border-l-4 border-maya-300 bg-ink-800/95 px-4 py-3"
                    >
                      <p className="text-xs text-fog-400">{shortDate(note.created_at)}</p>
                      <p>{note.text}</p>
                    </li>
                  ))}
                </ul>
              )}
            </section>
          </div>
        </>
      )}
    </div>
  )
}

function skillOf(row: HistoryRow, skill: SkillScore['skill']) {
  return row.skills.find((s) => s.skill === skill)
}

/** A real table; reading down a skill column is the trend, the level column the level history. */
function HistoryTable({ rows }: { rows: HistoryRow[] }) {
  const head = 'px-2 py-2 text-left text-xs font-bold tracking-wide text-fog-200 uppercase'
  return (
    <div className="overflow-x-auto rounded-card bg-ink-800">
      <table className="w-full border-collapse">
        <caption className="sr-only">Attempt history, newest first</caption>
        <thead>
          <tr className="border-b border-ink-600">
            <th scope="col" className={head}>
              Attempt
            </th>
            <th scope="col" className={`${head} hidden md:table-cell`}>
              Date
            </th>
            <th scope="col" className={`${head} hidden md:table-cell`}>
              Mission
            </th>
            <th scope="col" className={`${head} hidden md:table-cell`}>
              Ending
            </th>
            <th scope="col" className={head}>
              <span className="md:hidden">Level</span>
              <span className="hidden md:inline">Result</span>
            </th>
            <th scope="col" className={`${head} hidden md:table-cell`}>
              Correct
            </th>
            <th scope="col" className={`${head} hidden md:table-cell`}>
              Incorrect
            </th>
            {SCORED_SKILLS.map((skill) => (
              <th key={skill} scope="col" className={head}>
                <abbr title={skillName(skill)} className="no-underline md:hidden">
                  {skillAbbr(skill)}
                </abbr>
                <span className="hidden md:inline">{skillName(skill)}</span>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr
              key={row.attempt_id}
              className="relative border-b border-ink-600 last:border-b-0 hover:bg-ink-700"
            >
              <td className="px-2 py-2">
                <Link
                  to={reportPath(row.attempt_id)}
                  className="font-bold text-amber-400 after:absolute after:inset-0 hover:text-amber-200"
                >
                  Attempt {row.attempt_number}
                </Link>
                <span className="block text-sm text-fog-400 md:hidden">
                  {shortDate(row.submitted_at)}
                </span>
              </td>
              <td className="hidden px-2 py-2 text-sm md:table-cell">
                {shortDate(row.submitted_at)}
              </td>
              <td className="hidden px-2 py-2 text-sm md:table-cell">{row.mission_title}</td>
              <td className="hidden px-2 py-2 text-sm md:table-cell">{row.ending.title}</td>
              <td className="px-2 py-2 text-sm">
                <span className="md:hidden">
                  <span className="inline-block rounded-board bg-ink-950 px-1.5 font-display whitespace-nowrap text-amber-400">
                    {cefrLabel(row.suggested_cefr)}
                  </span>
                  <span className="block tabular-nums">{row.score_pct}%</span>
                </span>
                <span className="hidden md:inline">{row.label}</span>
              </td>
              <td className="hidden px-2 py-2 text-sm tabular-nums md:table-cell">{row.correct}</td>
              <td className="hidden px-2 py-2 text-sm tabular-nums md:table-cell">
                {row.incorrect}
              </td>
              {SCORED_SKILLS.map((skill) => (
                <SkillCell key={skill} pct={skillOf(row, skill)?.pct} />
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function ProgressSkeleton() {
  return (
    <div className="space-y-6" aria-busy="true">
      <Skeleton className="h-16" />
      {[0, 1, 2, 3].map((i) => (
        <Skeleton key={i} className="h-12" />
      ))}
      <div className="grid gap-6 lg:grid-cols-2">
        <Skeleton className="h-48" />
        <Skeleton className="h-48" />
      </div>
    </div>
  )
}
