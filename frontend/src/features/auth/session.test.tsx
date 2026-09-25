import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { renderHook, waitFor } from '@testing-library/react'
import type { ReactNode } from 'react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { api } from '../../api/client'
import { ApiError } from '../../api/http'
import { useMe } from './session'

vi.mock('../../api/client', () => ({ api: { me: vi.fn() } }))

const mocked = vi.mocked(api)

function renderUseMe() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  const wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={client}>{children}</QueryClientProvider>
  )
  return renderHook(() => useMe(), { wrapper })
}

describe('useMe', () => {
  beforeEach(() => vi.resetAllMocks())

  it('reads 200 null (no cookie, CR-008) as "not checked in"', async () => {
    mocked.me.mockResolvedValue(null)
    const { result } = renderUseMe()
    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data).toBeNull()
  })

  it('reads 401 (bad or expired cookie) as "not checked in"', async () => {
    mocked.me.mockRejectedValue(new ApiError(401, 'UNAUTHENTICATED', 'expired', null))
    const { result } = renderUseMe()
    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data).toBeNull()
  })

  it('returns the user when checked in and surfaces other failures as errors', async () => {
    mocked.me.mockResolvedValue({ id: 'u1', email: 'a@b.c', display_name: 'Ana', role: 'student' })
    const ok = renderUseMe()
    await waitFor(() => expect(ok.result.current.data?.display_name).toBe('Ana'))

    mocked.me.mockRejectedValue(new ApiError(0, 'NETWORK_ERROR', 'offline', null))
    const down = renderUseMe()
    await waitFor(() => expect(down.result.current.isError).toBe(true))
  })
})
