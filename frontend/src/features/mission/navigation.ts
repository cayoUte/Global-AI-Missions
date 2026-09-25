import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router'

import { api } from '../../api/client'
import { attemptKey } from '../../api/queryKeys'
import type { StateView } from '../../api/types'

export const playerPath = (missionId: string, attemptId: string) =>
  `/missions/${encodeURIComponent(missionId)}/play?attempt=${encodeURIComponent(attemptId)}`
export const reportPath = (attemptId: string) => `/attempts/${encodeURIComponent(attemptId)}/report`

/**
 * Start mission / Play again: POST start returns the open attempt (200) or a new one (201).
 * The StateView is cached so the player renders it without a second request.
 */
export function useStartMission() {
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  return useMutation({
    mutationFn: (missionId: string) => api.startMission(missionId),
    onSuccess: (state: StateView) => {
      queryClient.setQueryData(attemptKey(state.attempt_id), state)
      navigate(playerPath(state.mission_id, state.attempt_id))
    },
  })
}
