import { useQueryClient } from '@tanstack/react-query'
import type { ReactNode } from 'react'
import { useEffect, useState } from 'react'
import { Navigate } from 'react-router'

import { setUnauthenticatedListener } from '../../api/http'
import type { UserView } from '../../api/types'
import { Button } from '../../components/Button'
import { InlineNotice } from '../../components/InlineNotice'
import { ME_KEY } from '../../api/queryKeys'
import { hasSessionEnded, homeFor, markSessionEnded, useMe, type CheckInState } from './session'

/** "One moment…" after 300 ms, so fast checks never flash text (UI_SPEC §9.10). */
export function GuardLoading() {
  const [visible, setVisible] = useState(false)
  useEffect(() => {
    const timer = setTimeout(() => setVisible(true), 300)
    return () => clearTimeout(timer)
  }, [])
  return (
    <div className="grid min-h-dvh place-items-center bg-ink-900" role="status" aria-busy="true">
      <p className="text-fog-200">{visible ? 'One moment…' : ''}</p>
    </div>
  )
}

type Props = { roles: UserView['role'][]; children: ReactNode }

/** Route guard backed by GET /api/auth/me. Wrong role → that role's home (never a 403 page). */
export function RequireRole({ roles, children }: Props) {
  const me = useMe()
  if (me.isPending) return <GuardLoading />
  if (me.isError) {
    return (
      <main className="mx-auto max-w-reading px-4 py-16">
        <InlineNotice
          tone="problem"
          message="We couldn't reach Global AI. Check your connection and try again."
          action={
            <Button variant="secondary" onClick={() => me.refetch()}>
              Try again
            </Button>
          }
        />
      </main>
    )
  }
  if (!me.data) {
    const state: CheckInState | undefined = hasSessionEnded() ? { sessionEnded: true } : undefined
    return <Navigate to="/check-in" replace state={state} />
  }
  if (!roles.includes(me.data.role)) {
    const state: CheckInState | undefined =
      me.data.role === 'student' ? { notice: 'That page is for teachers.' } : undefined
    return <Navigate to={homeFor(me.data)} replace state={state} />
  }
  return <>{children}</>
}

/** Any 401 UNAUTHENTICATED outside the auth probes → Check-in with the session-ended notice. */
export function SessionWatcher() {
  const queryClient = useQueryClient()
  useEffect(() => {
    setUnauthenticatedListener(() => {
      // The guard of the current page then redirects to Check-in with the notice.
      markSessionEnded()
      queryClient.setQueryData(ME_KEY, null)
    })
    return () => setUnauthenticatedListener(null)
  }, [queryClient])
  return null
}
