import { useQuery } from '@tanstack/react-query'
import { Footprints, Lightbulb, Lock, NotebookPen } from 'lucide-react'
import { Link, Navigate, useParams } from 'react-router'

import { api } from '../../api/client'
import { isApiError } from '../../api/http'
import type { DiaryEntry, MissedCheckpoint, NextMission, Report, StateView } from '../../api/types'
import { AppShell, PageHeading } from '../../components/AppShell'
import { Button } from '../../components/Button'
import { buttonClasses } from '../../components/buttonClasses'
import { InlineNotice } from '../../components/InlineNotice'
import { MayaPortrait } from '../../components/Maya'
import { OutcomeMarker } from '../../components/OutcomeMarker'
import { Skeleton } from '../../components/Skeleton'
import { SkillBar } from '../../components/SkillBar'
import { Tag } from '../../components/Tag'
import { cefrLabel, checkpointTag, dateTime, skillName } from '../../lib/format'
import { reportKey } from '../../api/queryKeys'
import { playerPath } from '../mission/navigation'

export function ReportPage() {
  const { attemptId = '' } = useParams()
  const report = useQuery({
    queryKey: reportKey(attemptId),
    queryFn: () => api.report(attemptId),
    staleTime: Infinity, // a submitted report never changes
    retry: (count, error) =>
      !(isApiError(error) && [401, 404, 409].includes(error.status)) && count < 1,
  })

  if (report.isError && isApiError(report.error)) {
    const state = report.error.details?.state as StateView | undefined
    if (report.error.status === 409 && state)
      return <Navigate to={playerPath(state.mission_id, state.attempt_id)} replace />
  }

  return (
    <AppShell width="player">
      {report.isPending ? (
        <ReportSkeleton />
      ) : report.isError ? (
        isApiError(report.error) && report.error.status === 404 ? (
          <>
            <PageHeading className="sr-only">Mission Report</PageHeading>
            <InlineNotice
              tone="problem"
              message="We couldn't find this Mission Report."
              action={
                <Link to="/world" className={buttonClasses('secondary')}>
                  Back to the English World
                </Link>
              }
            />
          </>
        ) : (
          <>
            <PageHeading className="sr-only">Mission Report</PageHeading>
            <InlineNotice
              tone="problem"
              message="We couldn't open this Mission Report. Try again."
              action={
                <Button
                  variant="secondary"
                  loading={report.isFetching}
                  loadingLabel="One moment…"
                  onClick={() => report.refetch()}
                >
                  Try again
                </Button>
              }
            />
          </>
        )
      ) : (
        <ReportView report={report.data} />
      )}
    </AppShell>
  )
}

const SECTION = 'mt-8 space-y-4 border-t border-ink-600 pt-8'

function ReportView({ report }: { report: Report }) {
  const { result, attempt_record: record } = report
  return (
    <article>
      {/* 1. The result: plain, first, no clicks (PD-001). */}
      <section aria-labelledby="report-label" className="space-y-6">
        <div>
          <p className="text-xs font-bold tracking-wide text-fog-200 uppercase">
            English Assessment · Mission Report
          </p>
          <PageHeading className="font-display text-2xl font-semibold md:text-3xl">
            <span id="report-label">{report.label}</span>
          </PageHeading>
        </div>

        <dl className="grid grid-cols-3 gap-3">
          <StatTile label="Global score" value={`${result.score_pct}%`} highlight />
          <StatTile label="Correct" value={String(result.correct)} />
          <StatTile label="Incorrect" value={String(result.incorrect)} />
        </dl>

        <div className="space-y-3">
          <h2 className="text-xl font-bold">Result per skill</h2>
          {result.skills.map((s) => (
            <SkillBar
              key={s.skill}
              skill={s.skill}
              pct={s.pct}
              correct={s.correct}
              total={s.total}
            />
          ))}
          {result.unmeasured_skills.includes('speaking') ? (
            <p className="text-sm text-fog-400">
              Speaking isn&apos;t measured in this mission yet.
            </p>
          ) : null}
        </div>

        <div className="space-y-3">
          <h2 className="text-xl font-bold">Suggested level</h2>
          <div className="flex items-center gap-4">
            <span
              className={`grid h-16 min-w-16 shrink-0 place-items-center rounded-card bg-ink-950 px-2 font-display whitespace-nowrap text-amber-400 shadow-board ${
                result.suggested_level.cefr === 'PRE_A1' ? 'text-2xl' : 'text-3xl'
              }`}
            >
              {cefrLabel(result.suggested_level.cefr)}
            </span>
            <p>{result.suggested_level.reason}</p>
          </div>
        </div>

        <div className="space-y-3">
          <h2 className="text-xl font-bold">Attempt record</h2>
          <dl className="grid grid-cols-[auto_1fr] gap-x-6 gap-y-1">
            <RecordRow term="Attempt" value={String(record.attempt_number)} />
            <RecordRow term="Submitted" value={dateTime(record.submitted_at)} />
            <RecordRow term="Ending" value={record.ending.title} />
            <RecordRow term="Story-minutes" value={String(record.story_minutes_used)} />
            <RecordRow term="Maya's shortcut" value={record.rescue_used ? 'Used' : 'Not used'} />
            <RecordRow term="Hints from Maya" value={String(record.hints_received)} />
          </dl>
        </div>
      </section>

      {/* 2. Maya's interpretation. Portrait mood from the score (PD-032, UI-only). */}
      <section aria-labelledby="maya-reading" className={SECTION}>
        <h2 id="maya-reading" className="sr-only">
          Maya&apos;s interpretation
        </h2>
        <div className="flex items-start gap-4">
          <MayaPortrait
            mood={result.score_pct >= 70 ? 'proud' : 'encouraging'}
            size={96}
            className="hidden sm:block"
          />
          <MayaPortrait
            mood={result.score_pct >= 70 ? 'proud' : 'encouraging'}
            size={56}
            className="sm:hidden"
          />
          <div className="min-w-0 space-y-3">
            <p className="text-xs font-bold tracking-wide text-maya-300 uppercase">Maya</p>
            <p className="font-display text-xl md:text-2xl">{report.interpretation.summary}</p>
            <dl className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-1 text-lg">
              <dt className="text-fog-200">Strongest tonight</dt>
              <dd className="font-bold">{skillName(report.interpretation.strength)}</dd>
              <dt className="text-fog-200">To practise next</dt>
              <dd className="font-bold">{skillName(report.interpretation.challenge)}</dd>
            </dl>
            <p className="text-lg">{report.interpretation.recommendation}</p>
            <p className="text-xs text-fog-400">
              {report.feedback_source.status === 'ready'
                ? `About this feedback: Written by Maya using ${report.feedback_source.provider_label}.`
                : 'About this feedback: Written by Maya from her notebook (offline feedback).'}
            </p>
          </div>
        </div>
      </section>

      {/* 3. Next mission. */}
      {report.next_mission ? (
        <section aria-labelledby="next-heading" className={SECTION}>
          <h2 id="next-heading" className="text-xl font-bold">
            Maya has prepared your next mission
          </h2>
          <NextMissionCard mission={report.next_mission} />
        </section>
      ) : null}

      {/* 4. The Diary. */}
      <section aria-labelledby="diary-heading" className={SECTION}>
        <h2 id="diary-heading" className="text-xl font-bold">
          Diary
        </h2>
        <DiaryTimeline entries={report.diary} />
      </section>

      {/* 5. Checkpoints to revisit. */}
      <section aria-labelledby="revisit-heading" className={SECTION}>
        <h2 id="revisit-heading" className="text-xl font-bold">
          Checkpoints to revisit
        </h2>
        {report.missed.length === 0 ? (
          <p className="text-fog-200">
            Nothing to revisit tonight. You understood every checkpoint.
          </p>
        ) : (
          <ul className="space-y-4">
            {report.missed.map((item) => (
              <MissedCard key={item.item_id} item={item} />
            ))}
          </ul>
        )}
      </section>

      <div className="mt-10 flex flex-col gap-3 sm:flex-row">
        <Link to="/world" className={buttonClasses('primary', 'lg')}>
          Back to the English World
        </Link>
        <Link to="/progress" className={buttonClasses('secondary', 'lg')}>
          See your progress
        </Link>
      </div>
    </article>
  )
}

function StatTile({
  label,
  value,
  highlight = false,
}: {
  label: string
  value: string
  highlight?: boolean
}) {
  return (
    <div className="rounded-card bg-ink-800 p-3 text-center">
      <dt className="text-xs tracking-wide text-fog-200 uppercase">{label}</dt>
      <dd
        className={`font-display tabular-nums ${highlight ? 'text-4xl text-amber-400' : 'text-2xl text-fog-50 md:text-3xl'}`}
      >
        {value}
      </dd>
    </div>
  )
}

function RecordRow({ term, value }: { term: string; value: string }) {
  return (
    <>
      <dt className="text-fog-200">{term}</dt>
      <dd>{value}</dd>
    </>
  )
}

function NextMissionCard({ mission }: { mission: NextMission }) {
  return (
    <div className="space-y-2 rounded-card bg-ink-800 p-4 shadow-card">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="font-display text-xl font-semibold">{mission.title}</p>
        <div className="flex gap-2">
          {mission.skill_focus.map((skill) => (
            <Tag key={skill} text={skillName(skill)} />
          ))}
        </div>
      </div>
      <p className="text-fog-200">{mission.reason}</p>
      {mission.state === 'in_preparation' ? (
        <p className="flex items-center gap-2">
          <NotebookPen aria-hidden="true" className="size-4 shrink-0" /> Maya is preparing this
          mission.
        </p>
      ) : mission.state === 'locked' ? (
        <p className="flex items-start gap-2">
          <Lock aria-hidden="true" className="mt-1 size-4 shrink-0" /> {mission.unlock_hint}
        </p>
      ) : null}
    </div>
  )
}

function DiaryTimeline({ entries }: { entries: DiaryEntry[] }) {
  return (
    <ol className="space-y-0">
      {entries.map((entry, index) => {
        const last = index === entries.length - 1
        return (
          <li key={entry.seq} className="grid grid-cols-[3.5rem_1fr]">
            <span className="pt-0.5 font-board text-sm text-amber-400 tabular-nums">
              {entry.clock}
            </span>
            <div className="relative space-y-1 border-l-2 border-ink-600 pb-5 pl-4">
              {entry.checkpoint ? (
                <span
                  aria-hidden="true"
                  className="absolute top-1.5 -left-[6px] size-2.5 rounded-full bg-fog-200"
                />
              ) : null}
              <p className="text-xs tracking-board text-fog-200 uppercase">{entry.location}</p>
              <p className={last && entry.kind === 'ending' ? 'font-display text-xl' : 'text-base'}>
                {entry.text}
              </p>
              {entry.checkpoint ? (
                <div className="flex flex-wrap items-center gap-2">
                  <Tag
                    text={checkpointTag(
                      entry.checkpoint.type,
                      entry.checkpoint.skill,
                      entry.checkpoint.cefr,
                    )}
                  />
                  <OutcomeMarker outcome={entry.checkpoint.outcome} />
                </div>
              ) : null}
              {entry.maya_decision === 'hint' ? (
                <p className="flex items-center gap-1.5 text-sm text-maya-300">
                  <Lightbulb aria-hidden="true" className="size-4" /> Maya&apos;s hint
                </p>
              ) : null}
              {entry.maya_decision === 'rescue' ? (
                <p className="flex items-center gap-1.5 text-sm text-maya-300">
                  <Footprints aria-hidden="true" className="size-4" /> Maya&apos;s shortcut
                </p>
              ) : null}
            </div>
          </li>
        )
      })}
    </ol>
  )
}

function MissedCard({ item }: { item: MissedCheckpoint }) {
  const stimulus = item.stimulus
  return (
    <li className="surface-paper space-y-3 rounded-card bg-paper-50 p-4 text-paper-ink">
      <Tag text={checkpointTag(item.type, item.skill, item.cefr)} onPaper />
      <p className="font-bold">{item.prompt}</p>
      {stimulus ? (
        stimulus.kind === 'audio' ? (
          <div>
            <p className="text-sm text-paper-muted">
              Transcript{stimulus.speaker ? ` · ${stimulus.speaker}` : ''}
            </p>
            <p className="italic">“{stimulus.audio_script}”</p>
          </div>
        ) : (
          <div className="rounded-board border border-paper-300 p-3">
            {stimulus.speaker ? (
              <p className="text-sm text-paper-muted">{stimulus.speaker}</p>
            ) : null}
            <p className="whitespace-pre-line">{stimulus.text}</p>
          </div>
        )
      ) : null}
      <dl className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-1">
        <dt className="text-paper-muted">Your answer</dt>
        <dd className="font-bold">{item.your_answer}</dd>
        <dt className="text-paper-muted">Correct answer</dt>
        <dd className="font-bold">{item.correct_answer}</dd>
      </dl>
      <p>
        <span className="font-bold">Why:</span> {item.explanation}
      </p>
      <p>
        <span className="font-bold">Maya&apos;s tip:</span> {item.maya_tip}
      </p>
    </li>
  )
}

function ReportSkeleton() {
  return (
    <div className="space-y-6" aria-busy="true">
      <Skeleton className="h-4 w-1/2" />
      <Skeleton className="h-10 w-3/4" />
      <div className="grid grid-cols-3 gap-3">
        <Skeleton className="h-24" />
        <Skeleton className="h-24" />
        <Skeleton className="h-24" />
      </div>
      {[0, 1, 2, 3].map((i) => (
        <Skeleton key={i} className="h-8" />
      ))}
      <div className="flex gap-4">
        <Skeleton className="size-16" />
        <Skeleton className="h-16 flex-1" />
      </div>
      <Skeleton className="h-40" />
      <Skeleton className="h-32" />
    </div>
  )
}
