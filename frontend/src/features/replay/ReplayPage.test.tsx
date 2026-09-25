import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { api } from '../../api/client'
import { ApiError } from '../../api/http'
import type { SimulationResponse, SimulationStep } from '../../api/types'
import { ReplayPage } from './ReplayPage'
import { parseSeed } from './seed'

vi.mock('../../api/client', () => ({
  api: { me: vi.fn(), config: vi.fn(), logout: vi.fn(), simulate: vi.fn() },
}))
const motion = vi.hoisted(() => ({ reduced: false }))
vi.mock('framer-motion', async (importOriginal) => ({
  ...(await importOriginal<typeof import('framer-motion')>()),
  useReducedMotion: () => motion.reduced,
}))
const mocked = vi.mocked(api)

const step = (seq: number, patch: Partial<SimulationStep>): SimulationStep => ({
  seq,
  node_id: `n${seq}`,
  kind: 'narrative',
  clock: {
    time: '21:47',
    minutes_left: 18,
    train_departed: false,
    label: '21:47 · 18 min to departure',
  },
  outcome: null,
  maya_decision: 'quiet',
  maya_mood: 'curious',
  ...patch,
})
const RESULT: SimulationResponse = {
  mission_id: 'the-last-train',
  profile: 'A2',
  seed: 7,
  steps: [
    step(1, {}),
    step(2, { node_id: 'c01', kind: 'checkpoint', outcome: 'understood' }),
    step(3, { node_id: 'c02', kind: 'checkpoint', outcome: 'missed', maya_decision: 'hint' }),
    step(4, { kind: 'consequence', maya_decision: 'rescue', maya_mood: 'worried' }),
    step(5, { kind: 'ending', maya_mood: 'proud' }),
  ],
  ending: { key: 'made_it_with_maya', title: 'Made It Together' },
  story_minutes_used: 17,
}

function renderPage(url = '/replay?mission=the-last-train') {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[url]}>
        <ReplayPage />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

function demoMode(on: boolean) {
  mocked.config.mockResolvedValue({ demo_mode: on, demo_accounts: null, demo_password: null })
}

describe('ReplayPage', () => {
  beforeEach(() => {
    vi.resetAllMocks()
    motion.reduced = false
    mocked.me.mockResolvedValue({
      id: 's',
      email: 'new@x.test',
      display_name: 'Ana',
      role: 'student',
    })
    demoMode(true)
  })

  it('runs a simulation: loading, then the ending and the path step by step', async () => {
    let release = () => {}
    mocked.simulate.mockReturnValue(
      new Promise((resolve) => {
        release = () => resolve(RESULT)
      }),
    )
    renderPage()
    expect(await screen.findByText(/A simulated student, not a real one/)).toBeVisible()
    await userEvent.click(screen.getByRole('radio', { name: 'B1' }))
    await userEvent.clear(screen.getByLabelText('Seed'))
    await userEvent.type(screen.getByLabelText('Seed'), '7')
    await userEvent.click(screen.getByRole('button', { name: 'Run simulation' }))
    expect(mocked.simulate).toHaveBeenCalledWith('the-last-train', 'B1', 7)
    expect(screen.getByRole('status')).toHaveTextContent('Running the simulation…')

    release()
    expect(
      await screen.findByRole('heading', { name: 'Ending reached: Made It Together' }),
    ).toBeVisible()
    expect(screen.getByText('Story-minutes used: 17')).toBeVisible()
    // Playing: the path appears step by step; Show all reveals the rest.
    const path = screen.getByRole('list', { name: 'Simulated path' })
    expect(within(path).queryAllByRole('listitem').length).toBeLessThan(5)
    await userEvent.click(screen.getByRole('button', { name: 'Show all' }))
    expect(within(path).getAllByRole('listitem')).toHaveLength(5)
    expect(within(path).getByText('Understood')).toBeVisible()
    expect(within(path).getByText('Missed')).toBeVisible()
    expect(within(path).getByText("Maya's hint")).toBeVisible()
    expect(within(path).getByText("Maya's shortcut")).toBeVisible()
    expect(within(path).getByAltText('Maya, looking worried')).toBeVisible()
    expect(within(path).getAllByText('18 min to departure')).toHaveLength(5)
  })

  it('shows the whole path at once under reduced motion', async () => {
    motion.reduced = true
    mocked.simulate.mockResolvedValue(RESULT)
    renderPage()
    await userEvent.click(await screen.findByRole('button', { name: 'Run simulation' }))
    const path = await screen.findByRole('list', { name: 'Simulated path' })
    expect(within(path).getAllByRole('listitem')).toHaveLength(5)
    expect(screen.getByRole('button', { name: 'Show all' })).toBeDisabled()
  })

  it('shows the error state with Try again, and recovers', async () => {
    mocked.simulate.mockRejectedValueOnce(new ApiError(0, 'NETWORK_ERROR', 'offline', null))
    mocked.simulate.mockResolvedValueOnce(RESULT)
    renderPage()
    await userEvent.click(await screen.findByRole('button', { name: 'Run simulation' }))
    const alert = await screen.findByRole('alert')
    expect(alert).toHaveTextContent("The simulation couldn't run.")
    await userEvent.click(within(alert).getByRole('button', { name: 'Try again' }))
    expect(await screen.findByRole('heading', { name: /Ending reached/ })).toBeVisible()
    expect(mocked.simulate).toHaveBeenCalledTimes(2)
  })

  it('is not available when demo mode is off, and never calls the API', async () => {
    demoMode(false)
    renderPage()
    expect(
      await screen.findByText('The simulated run is only available in demo mode.'),
    ).toBeVisible()
    expect(screen.queryByRole('button', { name: 'Run simulation' })).toBeNull()
    expect(screen.getByRole('link', { name: 'Back to the English World' })).toHaveAttribute(
      'href',
      '/world',
    )
    expect(mocked.simulate).not.toHaveBeenCalled()
  })

  it('keeps Run disabled for a seed outside 0..1000000', async () => {
    renderPage()
    const seed = await screen.findByLabelText('Seed')
    await userEvent.clear(seed)
    await userEvent.type(seed, '1000001')
    expect(screen.getByRole('button', { name: 'Run simulation' })).toBeDisabled()
    expect(parseSeed('0')).toBe(0)
    expect(parseSeed(' 42 ')).toBe(42)
    for (const bad of ['', '-1', '1.5', 'abc', '1000001']) expect(parseSeed(bad)).toBeNull()
  })
})
