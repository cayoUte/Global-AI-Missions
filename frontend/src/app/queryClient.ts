import { QueryClient } from '@tanstack/react-query'

import { isApiError } from '../api/http'

export function createQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: {
        // Retry once on network trouble; never on contract errors (401/403/404/409/422).
        retry: (count, error) =>
          count < 1 && !(isApiError(error) && error.status >= 400 && error.status < 500),
        refetchOnWindowFocus: false,
      },
    },
  })
}
