import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { act, render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { api } from '../../api/client'
import { mockWorld } from '../../api/mock/fixtures'
import { WorldPage } from './WorldPage'

vi.mock('../../api/client', () => ({
  api: { me: vi.fn(), config: vi.fn(), logout: vi.fn(), world: vi.fn() },
}))
const mocked = vi.mocked(api)

function renderWorld() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  render(
    <QueryClientProvider client={client}>
      <MemoryRouter>
        <WorldPage />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('WorldPage replay link', () => {
  beforeEach(() => {
    vi.resetAllMocks()
    mocked.world.mockResolvedValue(mockWorld(null, null))
  })

  it('links to the simulated run only in demo mode', async () => {
    mocked.config.mockResolvedValue({ demo_mode: true, demo_accounts: [], demo_password: 'x' })
    renderWorld()
    const link = await screen.findByRole('link', { name: 'Watch a simulated run' })
    expect(link.getAttribute('href')).toMatch(/^\/replay\?mission=/)
  })

  it('hides the link when demo mode is off', async () => {
    mocked.config.mockResolvedValue({ demo_mode: false, demo_accounts: null, demo_password: null })
    renderWorld()
    await screen.findByRole('heading', { name: 'Missions' })
    expect(mocked.config).toHaveBeenCalled()
    await act(() => new Promise((resolve) => setTimeout(resolve, 20))) // let the config settle
    expect(screen.queryByRole('link', { name: 'Watch a simulated run' })).toBeNull()
  })
})
