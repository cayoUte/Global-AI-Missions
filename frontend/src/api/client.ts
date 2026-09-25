// The one client interface every screen uses. The real implementation talks to FastAPI through
// the Vite proxy (dev) or the same origin (prod). A mock implementation with fixtures exists for
// UI work without a backend (`npm run dev:mock`); it is loaded only in dev mode, so production
// builds never contain it (import.meta.env.DEV is statically false there).
import { request } from './http'
import type {
  AdvanceRequest,
  AnswerRequest,
  AnswerResponse,
  ClassProgressResponse,
  ClassesResponse,
  ConfigResponse,
  LoginRequest,
  ProgressResponse,
  Report,
  StateView,
  UserView,
  WorldResponse,
} from './types'

export interface ApiClient {
  config(): Promise<ConfigResponse>
  login(body: LoginRequest): Promise<UserView>
  logout(): Promise<void>
  me(): Promise<UserView>
  world(): Promise<WorldResponse>
  progress(): Promise<ProgressResponse>
  startMission(missionId: string): Promise<StateView>
  attempt(attemptId: string): Promise<StateView>
  advance(attemptId: string, body: AdvanceRequest): Promise<StateView>
  answer(attemptId: string, body: AnswerRequest): Promise<AnswerResponse>
  submit(attemptId: string): Promise<Report>
  report(attemptId: string): Promise<Report>
  teacherClasses(): Promise<ClassesResponse>
  classProgress(classId: string): Promise<ClassProgressResponse>
}

const id = (value: string) => encodeURIComponent(value)

export const realClient: ApiClient = {
  config: () => request('/api/config'),
  login: (body) => request('/api/auth/login', { method: 'POST', body }),
  logout: () => request('/api/auth/logout', { method: 'POST' }),
  me: () => request('/api/auth/me'),
  world: () => request('/api/world'),
  progress: () => request('/api/me/progress'),
  startMission: (missionId) =>
    request(`/api/missions/${id(missionId)}/attempts`, { method: 'POST' }),
  attempt: (attemptId) => request(`/api/attempts/${id(attemptId)}`),
  advance: (attemptId, body) =>
    request(`/api/attempts/${id(attemptId)}/advance`, { method: 'POST', body }),
  answer: (attemptId, body) =>
    request(`/api/attempts/${id(attemptId)}/answer`, { method: 'POST', body }),
  // Submit may wait for Maya's feedback (8 s server budget), so it gets a longer timeout.
  submit: (attemptId) =>
    request(`/api/attempts/${id(attemptId)}/submit`, { method: 'POST', timeoutMs: 30_000 }),
  report: (attemptId) => request(`/api/attempts/${id(attemptId)}/report`),
  teacherClasses: () => request('/api/teacher/classes'),
  classProgress: (classId) => request(`/api/teacher/classes/${id(classId)}/progress`),
}

const useMock = import.meta.env.DEV && import.meta.env.VITE_API_MOCK === 'true'

let resolved: Promise<ApiClient> | null = null
function client(): Promise<ApiClient> {
  if (!resolved) {
    resolved = useMock
      ? import('./mock/mockClient').then((m) => m.mockClient)
      : Promise.resolve(realClient)
  }
  return resolved
}

/** The client used by the app: real by default, the mock only in dev with VITE_API_MOCK=true. */
export const api: ApiClient = {
  config: async () => (await client()).config(),
  login: async (body) => (await client()).login(body),
  logout: async () => (await client()).logout(),
  me: async () => (await client()).me(),
  world: async () => (await client()).world(),
  progress: async () => (await client()).progress(),
  startMission: async (missionId) => (await client()).startMission(missionId),
  attempt: async (attemptId) => (await client()).attempt(attemptId),
  advance: async (attemptId, body) => (await client()).advance(attemptId, body),
  answer: async (attemptId, body) => (await client()).answer(attemptId, body),
  submit: async (attemptId) => (await client()).submit(attemptId),
  report: async (attemptId) => (await client()).report(attemptId),
  teacherClasses: async () => (await client()).teacherClasses(),
  classProgress: async (classId) => (await client()).classProgress(classId),
}
