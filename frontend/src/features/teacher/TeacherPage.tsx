import { useQuery } from '@tanstack/react-query'
import { useSearchParams } from 'react-router'

import { api } from '../../api/client'
import { TEACHER_CLASSES_KEY, classProgressKey } from '../../api/queryKeys'
import type { ClassProgressResponse, ClassSummary } from '../../api/types'
import { AppShell, PageHeading, type NavItem } from '../../components/AppShell'
import { Button } from '../../components/Button'
import { InlineNotice } from '../../components/InlineNotice'
import { Skeleton } from '../../components/Skeleton'
import { SkillCell } from '../../components/SkillCell'
import {
  labelLevel,
  plural,
  shortDate,
  skillAbbr,
  skillName,
  SCORED_SKILLS,
} from '../../lib/format'
import { useMe } from '../auth/session'

const TEACHER_NAV: NavItem[] = [{ to: '/teacher', label: 'Classes' }]
const LOAD_ERROR = "We couldn't load your class."

/**
 * Teacher view (PRODUCT §5.7, UI_SPEC §9.8): read-only. The teacher's classes (an admin sees
 * all), and per class each student's latest report label, per-skill profile, missions played and
 * last activity, exactly as the server returns them. No drill-in, no actions (PD-030).
 */
export function TeacherPage() {
  const me = useMe()
  const classes = useQuery({ queryKey: TEACHER_CLASSES_KEY, queryFn: () => api.teacherClasses() })
  const [params, setParams] = useSearchParams()

  const list = classes.data?.classes ?? []
  const selected = list.find((c) => c.class_id === params.get('class')) ?? list[0]

  return (
    <AppShell navItems={TEACHER_NAV}>
      <div className="space-y-6 md:space-y-8">
        <PageHeading className="font-display text-2xl font-semibold">
          Hello, {me.data?.display_name}.
        </PageHeading>
        {classes.isPending ? (
          <TableSkeleton />
        ) : classes.isError ? (
          <LoadError retrying={classes.isFetching} onRetry={() => classes.refetch()} />
        ) : !selected ? (
          <p className="text-fog-200">No classes yet.</p>
        ) : (
          <>
            {list.length > 1 ? (
              <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
                <label htmlFor="class-picker" className="text-sm font-bold">
                  Class
                </label>
                <select
                  id="class-picker"
                  value={selected.class_id}
                  onChange={(event) => setParams({ class: event.target.value }, { replace: true })}
                  className="min-h-11 rounded-control border border-line-strong bg-ink-900 px-3 text-fog-50 hover:bg-ink-700"
                >
                  {list.map((c) => (
                    <option key={c.class_id} value={c.class_id}>
                      {c.name}
                    </option>
                  ))}
                </select>
              </div>
            ) : null}
            <ClassSection key={selected.class_id} summary={selected} />
          </>
        )}
      </div>
    </AppShell>
  )
}

function ClassSection({ summary }: { summary: ClassSummary }) {
  const progress = useQuery({
    queryKey: classProgressKey(summary.class_id),
    queryFn: () => api.classProgress(summary.class_id),
  })
  const headingId = `class-${summary.class_id}`
  return (
    <section aria-labelledby={headingId} className="space-y-3">
      <div>
        <h2 id={headingId} className="text-xl font-bold">
          {summary.name}
        </h2>
        <p className="text-sm text-fog-400">
          {summary.teacher_name} · {summary.student_count}{' '}
          {plural(summary.student_count, 'student', 'students')}
        </p>
      </div>
      {progress.isPending ? (
        <TableSkeleton />
      ) : progress.isError ? (
        <LoadError retrying={progress.isFetching} onRetry={() => progress.refetch()} />
      ) : progress.data.students.length === 0 ? (
        <p className="rounded-card bg-ink-800 p-4 text-fog-200">No students in this class yet.</p>
      ) : (
        <StudentsTable data={progress.data} />
      )}
    </section>
  )
}

/** Same pattern as Attempt history: a real table that scrolls inside its card below 768 px. */
function StudentsTable({ data }: { data: ClassProgressResponse }) {
  const head = 'px-2 py-2 text-left text-xs font-bold tracking-wide text-fog-200 uppercase'
  const wide = 'hidden md:table-cell'
  return (
    <div className="overflow-x-auto rounded-card bg-ink-800">
      <table className="w-full border-collapse">
        <caption className="sr-only">Students in {data.name}</caption>
        <thead>
          <tr className="border-b border-ink-600">
            <th scope="col" className={head}>
              Student
            </th>
            <th scope="col" className={`${head} ${wide}`}>
              Missions played
            </th>
            <th scope="col" className={head}>
              <span className="md:hidden">Level</span>
              <span className="hidden md:inline">Latest report</span>
            </th>
            {SCORED_SKILLS.map((skill) => (
              <th key={skill} scope="col" className={head}>
                <abbr title={skillName(skill)} className="no-underline md:hidden">
                  {skillAbbr(skill)}
                </abbr>
                <span className="hidden md:inline">{skillName(skill)}</span>
              </th>
            ))}
            <th scope="col" className={`${head} ${wide}`}>
              Last activity
            </th>
          </tr>
        </thead>
        <tbody>
          {data.students.map((student, index) => (
            <tr key={index} className="border-b border-ink-600 last:border-b-0">
              <th scope="row" className="px-2 py-2 text-left font-bold">
                {student.display_name}
              </th>
              <td className={`px-2 py-2 text-sm tabular-nums ${wide}`}>
                {student.missions_played}
              </td>
              <td className="px-2 py-2 text-sm">
                {student.latest_label ? (
                  <>
                    <span className="inline-block rounded-board bg-ink-950 px-1.5 font-display whitespace-nowrap text-amber-400 md:hidden">
                      {labelLevel(student.latest_label)}
                    </span>
                    <span className="hidden md:inline">{student.latest_label}</span>
                  </>
                ) : (
                  <span className="text-fog-400">—</span>
                )}
              </td>
              {SCORED_SKILLS.map((skill) => (
                <SkillCell
                  key={skill}
                  pct={student.profile?.skills.find((s) => s.skill === skill)?.pct}
                />
              ))}
              <td className={`px-2 py-2 text-sm ${wide}`}>
                {student.last_activity_at ? (
                  shortDate(student.last_activity_at)
                ) : (
                  <span className="text-fog-400">—</span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function LoadError({ retrying, onRetry }: { retrying: boolean; onRetry: () => void }) {
  return (
    <InlineNotice
      tone="problem"
      message={LOAD_ERROR}
      action={
        <Button variant="secondary" loading={retrying} loadingLabel="One moment…" onClick={onRetry}>
          Try again
        </Button>
      }
    />
  )
}

function TableSkeleton() {
  return (
    <div className="space-y-3" aria-busy="true">
      {[0, 1, 2].map((i) => (
        <Skeleton key={i} className="h-12" />
      ))}
    </div>
  )
}
