import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router'

import { api } from '../../api/client'
import { ME_KEY } from '../../api/queryKeys'

/** Check out: clear the cookie on the server, forget every cached query, go to Check-in. */
export function useCheckOut() {
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  return useMutation({
    mutationFn: () => api.logout(),
    onSettled: () => {
      queryClient.clear()
      queryClient.setQueryData(ME_KEY, null)
      navigate('/check-in', { replace: true })
    },
  })
}
