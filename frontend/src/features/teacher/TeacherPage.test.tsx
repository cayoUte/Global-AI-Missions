import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { api } from '../../api/client'
import { ApiError } from '../../api/http'
import type { ClassProgressResponse, ClassesResponse } from '../../api/types'
import { TeacherPage } from './TeacherPage'

vi.mock('../../api/client', () => ({
  api: { me: vi.fn(), logout: vi.fn(), teacherClasses: vi.fn(), classProgress: vi.fn() },
}))
const mocked = vi.mocked(api)

const CLASSES: ClassesResponse = {
  classes: [{ class_id: 'c1', name: 'Evening B1', teacher_name: 'Ms. Clarke', student_count: 2 }],
}
const PROGRESS: ClassProgressResponse = {
  class_id: 'c1',
  name: 'Evening B1',
  students: [
    {
      display_name: 'Ana',
      missions_played: 0,
      latest_label: null,
      profile: null,
      last_activity_at: null,
    },
    {
      display_name: 'Leo',
      missions_played: 4,
      latest_label: 'A2 · The Last Train — 70%',
      profile: {
        based_on_attempts: 3,
        skills: [
          { skill: 'grammar', pct: 75 },
          { skill: 'listening', pct: 33 },
          { skill: 'reading', pct: 67 },
          { skill: 'vocabulary', pct: 50 },
        ],
      },
      last_activity_at: '2026-09-24T21:58:00Z',
    },
  ],
}

function renderPage() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={['/teacher']}>
        <TeacherPage />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

/** Resolves only when `release` is called, so the loading state can be observed. */
function deferred<T>(value: T) {
  let release = () => {}
  const promise = new Promise<T>((resolve) => {
    release = () => resolve(value)
  })
  return { promise, release }
}

describe('TeacherPage', () => {
  beforeEach(() => {
    vi.resetAllMocks()
    mocked.me.mockResolvedValue({
      id: 't1',
      email: 'teacher@globalai.test',
      display_name: 'Ms. Clarke',
      role: 'teacher',
    })
    mocked.teacherClasses.mockResolvedValue(CLASSES)
  })

  it('shows skeleton rows while loading, then the class table as the server returns it', async () => {
    const progress = deferred(PROGRESS)
    mocked.classProgress.mockReturnValue(progress.promise)
    const { container } = renderPage()
    expect(await screen.findByRole('heading', { name: 'Hello, Ms. Clarke.' })).toBeVisible()
    await screen.findByRole('heading', { level: 2, name: 'Evening B1' })
    expect(container.querySelector('[aria-busy="true"]')).not.toBeNull()
    expect(screen.queryByRole('table')).toBeNull()

    progress.release()
    const table = await screen.findByRole('table', { name: 'Students in Evening B1' })
    expect(mocked.classProgress).toHaveBeenCalledWith('c1')
    const [, anaRow, leoRow] = within(table).getAllByRole('row')
    expect(within(anaRow).getByRole('rowheader')).toHaveTextContent('Ana')
    expect(anaRow).toHaveTextContent('—') // no report and no profile yet: nothing invented
    expect(within(leoRow).getByRole('rowheader')).toHaveTextContent('Leo')
    expect(leoRow).toHaveTextContent('A2 · The Last Train — 70%') // verbatim (md+ column)
    for (const pct of ['75%', '33%', '67%', '50%']) expect(leoRow).toHaveTextContent(pct)
    expect(leoRow).toHaveTextContent('4')
    // Read-only: no buttons or links inside the table.
    expect(within(table).queryAllByRole('button')).toHaveLength(0)
    expect(within(table).queryAllByRole('link')).toHaveLength(0)
    expect(within(table).getByText('Gr')).toHaveAttribute('title', 'Grammar')
  })

  it('shows the empty state for a class without students', async () => {
    mocked.classProgress.mockResolvedValue({ ...PROGRESS, students: [] })
    renderPage()
    expect(await screen.findByText('No students in this class yet.')).toBeVisible()
    expect(screen.queryByRole('table')).toBeNull()
  })

  it('shows the error state with Try again, and recovers', async () => {
    mocked.classProgress.mockRejectedValueOnce(new ApiError(404, 'NOT_FOUND', 'nope', null))
    mocked.classProgress.mockResolvedValueOnce(PROGRESS)
    renderPage()
    const alert = await screen.findByRole('alert')
    expect(alert).toHaveTextContent("We couldn't load your class.")
    await userEvent.click(within(alert).getByRole('button', { name: 'Try again' }))
    expect(await screen.findByRole('table', { name: 'Students in Evening B1' })).toBeVisible()
  })

  it('shows the same error when the class list fails', async () => {
    mocked.teacherClasses.mockRejectedValue(new ApiError(0, 'NETWORK_ERROR', 'offline', null))
    renderPage()
    expect(await screen.findByRole('alert')).toHaveTextContent("We couldn't load your class.")
    expect(mocked.classProgress).not.toHaveBeenCalled()
  })

  it('offers a class picker when there are two or more classes', async () => {
    mocked.teacherClasses.mockResolvedValue({
      classes: [
        ...CLASSES.classes,
        { class_id: 'c2', name: 'Morning A2', teacher_name: 'Mr. Reed', student_count: 0 },
      ],
    })
    mocked.classProgress.mockImplementation(async (id) =>
      id === 'c1' ? PROGRESS : { class_id: 'c2', name: 'Morning A2', students: [] },
    )
    renderPage()
    await screen.findByRole('table', { name: 'Students in Evening B1' })
    await userEvent.selectOptions(screen.getByLabelText('Class'), 'Morning A2')
    await waitFor(() => expect(mocked.classProgress).toHaveBeenCalledWith('c2'))
    expect(await screen.findByText('No students in this class yet.')).toBeVisible()
  })
})
