// In-memory mock of the API (dev only: `npm run dev:mock`). It mirrors the contract's shapes and
// status rules closely enough to build screens, but it never judges answers: every answer moves
// the story forward. Excluded from production builds (see ../client.ts).
import { ApiError } from '../http'
import type { ApiClient } from '../client'
import type { StateView, UserView } from '../types'
import {
  MOCK_CLASS_PROGRESS,
  MOCK_CLASSES,
  MOCK_EMPTY_PROGRESS,
  MOCK_MISSION,
  MOCK_NODES,
  mockReport,
  mockWorld,
} from './fixtures'

type MockAttempt = {
  id: string
  nodeId: string
  minutesLeft: number
  status: StateView['status']
  answered: Set<string>
}

const delay = (ms = 250) => new Promise((resolve) => setTimeout(resolve, ms))
let user: UserView | null = null
let current: MockAttempt | null = null
let lastSubmitted: string | null = null

function clockFor(minutesLeft: number) {
  const total = 21 * 60 + 47 + (18 - minutesLeft)
  const time = `${String(Math.floor(total / 60)).padStart(2, '0')}:${String(total % 60).padStart(2, '0')}`
  const label =
    minutesLeft > 0
      ? `${time} · ${minutesLeft} min to departure`
      : minutesLeft === 0
        ? `${time} · Departing now`
        : `${time} · Train departed — Plan B`
  return { time, minutes_left: minutesLeft, train_departed: minutesLeft < 0, label }
}

function view(attempt: MockAttempt): StateView {
  const entry = MOCK_NODES[attempt.nodeId]
  return {
    attempt_id: attempt.id,
    mission_id: MOCK_MISSION.id,
    mission_title: MOCK_MISSION.title,
    status: attempt.status,
    clock: clockFor(attempt.minutesLeft),
    node: entry.node,
    maya: { mood: 'curious', decision: 'quiet', line: entry.mayaLine },
  }
}

function requireUser() {
  if (!user) throw new ApiError(401, 'UNAUTHENTICATED', 'mock: not checked in', null)
}

function requireAttempt(attemptId: string): MockAttempt {
  requireUser()
  if (!current || current.id !== attemptId)
    throw new ApiError(404, 'NOT_FOUND', 'mock: unknown attempt', null)
  return current
}

function conflict(
  code: 'NODE_OUT_OF_SEQUENCE' | 'CHECKPOINT_LOCKED' | 'ATTEMPT_NOT_IN_PROGRESS',
  attempt: MockAttempt,
): never {
  throw new ApiError(409, code, 'mock conflict', { state: view(attempt) })
}

function moveOn(attempt: MockAttempt) {
  const entry = MOCK_NODES[attempt.nodeId]
  if (!entry.next) return
  attempt.minutesLeft -= entry.minutes
  attempt.nodeId = entry.next
  if (MOCK_NODES[attempt.nodeId].node.kind === 'ending') attempt.status = 'completed'
}

export const mockClient: ApiClient = {
  async config() {
    await delay()
    return { demo_mode: false, demo_accounts: null, demo_password: null }
  },
  async login(body) {
    await delay()
    const role = body.email.startsWith('teacher') ? 'teacher' : 'student'
    user = { id: 'mock-user', email: body.email, display_name: 'Mock', role }
    return user
  },
  async logout() {
    user = null
  },
  async me() {
    await delay(50)
    return user // null when not checked in, like the server (CR-008)
  },
  async world() {
    await delay()
    requireUser()
    return mockWorld(current && current.status !== 'submitted' ? current.id : null, lastSubmitted)
  },
  async progress() {
    await delay()
    requireUser()
    return MOCK_EMPTY_PROGRESS
  },
  async startMission() {
    await delay()
    requireUser()
    if (!current || current.status === 'submitted') {
      current = {
        id: crypto.randomUUID(),
        nodeId: 'intro',
        minutesLeft: 18,
        status: 'in_progress',
        answered: new Set(),
      }
    }
    return view(current)
  },
  async attempt(attemptId) {
    await delay()
    return view(requireAttempt(attemptId))
  },
  async advance(attemptId, body) {
    await delay()
    const attempt = requireAttempt(attemptId)
    if (attempt.status !== 'in_progress') conflict('ATTEMPT_NOT_IN_PROGRESS', attempt)
    const kind = MOCK_NODES[attempt.nodeId].node.kind
    if (body.node_id !== attempt.nodeId || kind === 'checkpoint' || kind === 'ending')
      conflict('NODE_OUT_OF_SEQUENCE', attempt)
    moveOn(attempt)
    return view(attempt)
  },
  async answer(attemptId, body) {
    await delay(600)
    const attempt = requireAttempt(attemptId)
    if (attempt.answered.has(body.node_id)) conflict('CHECKPOINT_LOCKED', attempt)
    if (attempt.status !== 'in_progress') conflict('ATTEMPT_NOT_IN_PROGRESS', attempt)
    if (body.node_id !== attempt.nodeId) conflict('NODE_OUT_OF_SEQUENCE', attempt)
    attempt.answered.add(body.node_id)
    moveOn(attempt)
    return { maya_line: 'Mock reaction from Maya.', state: view(attempt) }
  },
  async submit(attemptId) {
    await delay(1500)
    const attempt = requireAttempt(attemptId)
    if (attempt.status === 'in_progress')
      throw new ApiError(409, 'MISSION_NOT_FINISHED', 'mock', { state: view(attempt) })
    attempt.status = 'submitted'
    lastSubmitted = attempt.id
    return mockReport(attempt.id)
  },
  async report(attemptId) {
    await delay()
    const attempt = requireAttempt(attemptId)
    if (attempt.status !== 'submitted')
      throw new ApiError(409, 'MISSION_NOT_FINISHED', 'mock', { state: view(attempt) })
    return mockReport(attemptId)
  },
  async teacherClasses() {
    await delay()
    requireUser()
    return MOCK_CLASSES
  },
  async classProgress(classId) {
    await delay()
    requireUser()
    if (classId !== MOCK_CLASS_PROGRESS.class_id)
      throw new ApiError(404, 'NOT_FOUND', 'mock: unknown class', null)
    return MOCK_CLASS_PROGRESS
  },
}
