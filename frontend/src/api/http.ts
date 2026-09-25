// A small typed fetch wrapper. The session lives in the httpOnly cookie (credentials: 'include');
// no token is ever read or stored by the client. Every non-2xx body is the contract's error
// envelope, turned into an ApiError whose `code` drives the user copy (never `message`).

export type ErrorCode =
  | 'INVALID_CREDENTIALS'
  | 'UNAUTHENTICATED'
  | 'FORBIDDEN_ROLE'
  | 'NOT_FOUND'
  | 'ATTEMPT_NOT_IN_PROGRESS'
  | 'NODE_OUT_OF_SEQUENCE'
  | 'CHECKPOINT_LOCKED'
  | 'MISSION_NOT_FINISHED'
  | 'VALIDATION_ERROR'
  | 'RATE_LIMITED'
  | 'INTERNAL_ERROR'
  // Client-side codes: the request never produced a contract response.
  | 'NETWORK_ERROR'
  | 'TIMEOUT'

export class ApiError extends Error {
  readonly status: number
  readonly code: ErrorCode
  readonly details: Record<string, unknown> | null

  constructor(
    status: number,
    code: ErrorCode,
    message: string,
    details: Record<string, unknown> | null,
  ) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
    this.details = details
  }

  /** True for every 409 on an attempt endpoint: details.state holds the server's truth. */
  get isConflict(): boolean {
    return this.status === 409
  }
}

export function isApiError(error: unknown): error is ApiError {
  return error instanceof ApiError
}

// Paths whose 401 means "not checked in" rather than "the session ended".
const AUTH_PROBES = ['/api/auth/me', '/api/auth/login']

type UnauthenticatedListener = () => void
let onUnauthenticated: UnauthenticatedListener | null = null

/** The app registers one listener that routes to Check-in with the session-ended notice. */
export function setUnauthenticatedListener(listener: UnauthenticatedListener | null): void {
  onUnauthenticated = listener
}

const DEFAULT_TIMEOUT_MS = 15_000

type RequestOptions = {
  method?: 'GET' | 'POST'
  body?: unknown
  timeoutMs?: number
}

export async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = 'GET', body, timeoutMs = DEFAULT_TIMEOUT_MS } = options
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), timeoutMs)

  let response: Response
  try {
    response = await fetch(path, {
      method,
      credentials: 'include',
      headers:
        body === undefined
          ? { Accept: 'application/json' }
          : { Accept: 'application/json', 'Content-Type': 'application/json' },
      body: body === undefined ? undefined : JSON.stringify(body),
      signal: controller.signal,
    })
  } catch {
    const timedOut = controller.signal.aborted
    throw new ApiError(
      0,
      timedOut ? 'TIMEOUT' : 'NETWORK_ERROR',
      timedOut ? 'Request timed out' : 'Network error',
      null,
    )
  } finally {
    clearTimeout(timer)
  }

  if (response.status === 204) return undefined as T

  const payload: unknown = await response.json().catch(() => null)

  if (!response.ok) {
    const envelope = (
      payload as { error?: { code?: string; message?: string; details?: unknown } } | null
    )?.error
    const code =
      (envelope?.code as ErrorCode | undefined) ??
      (response.status >= 500 ? 'INTERNAL_ERROR' : 'NETWORK_ERROR')
    const error = new ApiError(
      response.status,
      code,
      envelope?.message ?? `HTTP ${response.status}`,
      (envelope?.details as Record<string, unknown> | null | undefined) ?? null,
    )
    if (code === 'UNAUTHENTICATED' && !AUTH_PROBES.includes(path)) onUnauthenticated?.()
    throw error
  }

  return payload as T
}
