import { useQuery } from '@tanstack/react-query'

import { api } from '../../api/client'
import { isApiError } from '../../api/http'
import { CONFIG_KEY, ME_KEY } from '../../api/queryKeys'
import type { UserView } from '../../api/types'

/**
 * The current user, or null when not checked in. The server answers 200 null when no session
 * cookie was sent (CR-008) and 401 when the cookie is bad or expired; both mean "no session".
 * Other failures surface as errors.
 */
export function useMe() {
  return useQuery<UserView | null>({
    queryKey: ME_KEY,
    queryFn: async () => {
      try {
        return (await api.me()) ?? null
      } catch (error) {
        if (isApiError(error) && error.status === 401) return null
        throw error
      }
    },
    staleTime: 60_000,
    retry: false,
  })
}

export function useConfig() {
  return useQuery({
    queryKey: CONFIG_KEY,
    queryFn: () => api.config(),
    staleTime: Infinity,
    retry: 1,
  })
}

export const homeFor = (user: UserView) => (user.role === 'student' ? '/world' : '/teacher')

// Set when an authenticated call returns 401 UNAUTHENTICATED; cleared by the next check-in. The
// route guard reads it so its redirect carries the "Your session ended…" notice.
let sessionEnded = false
export const markSessionEnded = () => {
  sessionEnded = true
}
export const clearSessionEnded = () => {
  sessionEnded = false
}
export const hasSessionEnded = () => sessionEnded

/** Router state used to show "Your session ended…" on Check-in. */
export type CheckInState = { sessionEnded?: boolean; notice?: string }
