import { AppShell, PageHeading } from '../../components/AppShell'
import { useMe } from '../auth/session'

/** PD-019: the teacher view stretch is not built; RBAC is demonstrated through the API. */
export function TeacherLanding() {
  const me = useMe()
  return (
    <AppShell nav={false}>
      <div className="max-w-reading space-y-4">
        <PageHeading className="font-display text-2xl font-semibold">
          Hello, {me.data?.display_name}.
        </PageHeading>
        <p className="text-lg">
          The teacher view isn&apos;t part of this build. Your roles are shown through the API.
        </p>
      </div>
    </AppShell>
  )
}
