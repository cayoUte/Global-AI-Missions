import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { api } from '../../api/client'
import { ApiError } from '../../api/http'
import { CheckInPage } from './CheckInPage'

vi.mock('../../api/client', () => ({
  api: { me: vi.fn(), config: vi.fn(), login: vi.fn() },
}))

const mocked = vi.mocked(api)

function renderPage() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={['/check-in']}>
        <Routes>
          <Route path="/check-in" element={<CheckInPage />} />
          <Route path="/world" element={<p>World page</p>} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

async function fillAndSubmit(user: ReturnType<typeof userEvent.setup>) {
  await user.type(await screen.findByLabelText('Email'), 'new@globalai.test')
  await user.type(screen.getByLabelText('Password'), 'secret')
  await user.click(screen.getByRole('button', { name: 'Check in' }))
}

describe('CheckInPage', () => {
  beforeEach(() => {
    vi.resetAllMocks()
    mocked.me.mockResolvedValue(null) // anonymous visitor: 200 null (CR-008)
    mocked.config.mockResolvedValue({ demo_mode: false, demo_accounts: null, demo_password: null })
  })

  it('validates presence and email shape on the client', async () => {
    const user = userEvent.setup()
    renderPage()
    await user.click(await screen.findByRole('button', { name: 'Check in' }))
    expect(screen.getByText('Enter your email.')).toBeInTheDocument()
    expect(screen.getByText('Enter your password.')).toBeInTheDocument()
    expect(mocked.login).not.toHaveBeenCalled()
  })

  it('shows one generic message on wrong credentials and keeps the email', async () => {
    mocked.login.mockRejectedValue(new ApiError(401, 'INVALID_CREDENTIALS', 'x', null))
    const user = userEvent.setup()
    renderPage()
    await fillAndSubmit(user)
    expect(await screen.findByText("That email and password don't match.")).toBeInTheDocument()
    expect(screen.getByLabelText('Email')).toHaveValue('new@globalai.test')
    expect(screen.getByLabelText('Password')).toHaveValue('')
  })

  it('shows the rate-limit copy on 429', async () => {
    mocked.login.mockRejectedValue(
      new ApiError(429, 'RATE_LIMITED', 'x', { retry_after_seconds: 42 }),
    )
    const user = userEvent.setup()
    renderPage()
    await fillAndSubmit(user)
    expect(
      await screen.findByText('Too many tries. Wait a minute and check in again.'),
    ).toBeInTheDocument()
  })

  it('hides the demo panel unless the server says demo mode is on', async () => {
    renderPage()
    await screen.findByRole('button', { name: 'Check in' })
    expect(screen.queryByText('Demo accounts')).not.toBeInTheDocument()
  })

  it('routes a student to the English World after check-in', async () => {
    mocked.login.mockResolvedValue({
      id: 'u1',
      email: 'new@globalai.test',
      display_name: 'Ana',
      role: 'student',
    })
    const user = userEvent.setup()
    renderPage()
    await fillAndSubmit(user)
    expect(await screen.findByText('World page')).toBeInTheDocument()
  })
})
