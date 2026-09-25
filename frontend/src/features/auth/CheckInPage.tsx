import { useMutation, useQueryClient } from '@tanstack/react-query'
import { CircleAlert, Eye, EyeOff } from 'lucide-react'
import { useEffect, useRef, useState, type FormEvent } from 'react'
import { Navigate, useLocation, useNavigate } from 'react-router'

import { api } from '../../api/client'
import { isApiError } from '../../api/http'
import { ME_KEY } from '../../api/queryKeys'
import type { ConfigResponse, UserView } from '../../api/types'
import { Backdrop } from '../../components/Backdrop'
import { Button } from '../../components/Button'
import { InlineNotice } from '../../components/InlineNotice'
import { OfflineBanner } from '../../components/OfflineBanner'
import { GuardLoading } from './guards'
import { clearSessionEnded, homeFor, useConfig, useMe, type CheckInState } from './session'

const EMAIL_SHAPE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

const COPY = {
  INVALID_CREDENTIALS: "That email and password don't match.",
  RATE_LIMITED: 'Too many tries. Wait a minute and check in again.',
  NETWORK: "We couldn't reach Global AI. Check your connection and try again.",
  SESSION_ENDED: 'Your session ended. Check in again — your mission is saved.',
}

function loginErrorCopy(error: unknown): string {
  if (isApiError(error)) {
    if (error.code === 'INVALID_CREDENTIALS') return COPY.INVALID_CREDENTIALS
    if (error.code === 'RATE_LIMITED') return COPY.RATE_LIMITED
  }
  return COPY.NETWORK
}

type FieldErrors = { email?: string; password?: string }

function validate(email: string, password: string): FieldErrors {
  const errors: FieldErrors = {}
  if (!email.trim()) errors.email = 'Enter your email.'
  else if (!EMAIL_SHAPE.test(email.trim())) errors.email = 'Enter an email like name@example.com.'
  if (!password) errors.password = 'Enter your password.'
  return errors
}

export function CheckInPage() {
  const me = useMe()
  const config = useConfig()
  const location = useLocation()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const arrival = (location.state as CheckInState | null) ?? {}

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({})
  const emailRef = useRef<HTMLInputElement>(null)
  const submitRef = useRef<HTMLButtonElement>(null)

  const login = useMutation({
    mutationFn: (body: { email: string; password: string }) => api.login(body),
    onSuccess: (user: UserView) => {
      clearSessionEnded()
      queryClient.clear()
      queryClient.setQueryData(ME_KEY, user)
      navigate(homeFor(user), { replace: true })
    },
    onError: (error) => {
      if (isApiError(error) && error.code === 'INVALID_CREDENTIALS') setPassword('')
    },
  })

  // Desktop only: focus the email field (no autofocus on mobile, the keyboard would cover the pass).
  useEffect(() => {
    if (window.matchMedia?.('(min-width: 1024px)').matches) emailRef.current?.focus()
  }, [])

  if (me.isPending) return <GuardLoading />
  if (me.data) return <Navigate to={homeFor(me.data)} replace />

  const onSubmit = (event: FormEvent) => {
    event.preventDefault()
    if (login.isPending) return
    const errors = validate(email, password)
    setFieldErrors(errors)
    if (errors.email || errors.password) return
    login.mutate({ email: email.trim(), password })
  }

  const useAccount = (accountEmail: string, demoPassword: string) => {
    setEmail(accountEmail)
    setPassword(demoPassword)
    setFieldErrors({})
    submitRef.current?.focus()
  }

  const demo: ConfigResponse | undefined = config.data?.demo_mode ? config.data : undefined

  return (
    <div className="relative min-h-dvh overflow-hidden">
      <OfflineBanner />
      <div className="fixed inset-0">
        <Backdrop backdropKey="street_night" />
      </div>
      <main className="relative z-10 mx-auto max-w-[26rem] px-4 py-8 lg:max-w-[40rem]">
        <section className="surface-paper rounded-sheet bg-paper-50 text-paper-ink shadow-raised lg:grid lg:grid-cols-[1fr_auto_16rem]">
          <div className="p-6">
            <p className="font-board text-xs tracking-board text-paper-muted">BOARDING PASS</p>
            <h1 className="mt-1 font-display text-2xl font-semibold">Global AI Missions</h1>
            <p className="mt-1">Tonight, your English gets you home.</p>

            <dl
              aria-hidden="true"
              className="mt-4 grid grid-cols-2 gap-2 font-board text-xs text-paper-muted sm:grid-cols-4"
            >
              <div>
                <dt>FROM</dt>
                <dd className="text-paper-ink">London</dd>
              </div>
              <div>
                <dt>TO</dt>
                <dd className="text-paper-ink">Home</dd>
              </div>
              <div>
                <dt>DEPARTS</dt>
                <dd className="text-paper-ink">22:05</dd>
              </div>
              <div>
                <dt>PLATFORM</dt>
                <dd className="text-paper-ink">—</dd>
              </div>
            </dl>

            {arrival.sessionEnded ? (
              <InlineNotice tone="info" onPaper message={COPY.SESSION_ENDED} className="mt-4" />
            ) : null}

            <form
              noValidate
              onSubmit={onSubmit}
              className="mt-5 space-y-4"
              aria-busy={login.isPending}
            >
              <div className="space-y-1">
                <label htmlFor="email" className="block font-bold">
                  Email
                </label>
                <input
                  ref={emailRef}
                  id="email"
                  type="email"
                  autoComplete="username"
                  inputMode="email"
                  value={email}
                  readOnly={login.isPending}
                  onChange={(e) => setEmail(e.target.value)}
                  aria-invalid={fieldErrors.email ? true : undefined}
                  aria-describedby={fieldErrors.email ? 'email-error' : undefined}
                  className="min-h-11 w-full rounded-control border border-paper-muted bg-paper-50 px-3 text-base"
                />
                {fieldErrors.email ? (
                  <FieldError id="email-error" text={fieldErrors.email} />
                ) : null}
              </div>
              <div className="space-y-1">
                <label htmlFor="password" className="block font-bold">
                  Password
                </label>
                <div className="flex gap-2">
                  <input
                    id="password"
                    type={showPassword ? 'text' : 'password'}
                    autoComplete="current-password"
                    value={password}
                    readOnly={login.isPending}
                    onChange={(e) => setPassword(e.target.value)}
                    aria-invalid={fieldErrors.password ? true : undefined}
                    aria-describedby={fieldErrors.password ? 'password-error' : undefined}
                    className="min-h-11 w-full min-w-0 rounded-control border border-paper-muted bg-paper-50 px-3 text-base"
                  />
                  <button
                    type="button"
                    aria-pressed={showPassword}
                    aria-label={showPassword ? 'Hide password' : 'Show password'}
                    onClick={() => setShowPassword((v) => !v)}
                    className="grid size-11 shrink-0 place-items-center rounded-control border border-paper-muted"
                  >
                    {showPassword ? (
                      <EyeOff aria-hidden="true" className="size-5" />
                    ) : (
                      <Eye aria-hidden="true" className="size-5" />
                    )}
                  </button>
                </div>
                {fieldErrors.password ? (
                  <FieldError id="password-error" text={fieldErrors.password} />
                ) : null}
              </div>

              {login.isError ? (
                <InlineNotice tone="problem" onPaper message={loginErrorCopy(login.error)} />
              ) : null}

              <Button
                ref={submitRef}
                type="submit"
                variant="paper"
                size="lg"
                className="w-full"
                loading={login.isPending}
                loadingLabel="Checking in…"
              >
                Check in
              </Button>
            </form>
          </div>

          {demo ? (
            <>
              <Perforation />
              <DemoAccounts config={demo} onUse={useAccount} />
            </>
          ) : null}
        </section>
      </main>
    </div>
  )
}

function FieldError({ id, text }: { id: string; text: string }) {
  return (
    <p id={id} className="flex items-center gap-1.5 text-sm">
      <CircleAlert aria-hidden="true" className="size-4" />
      {text}
    </p>
  )
}

function Perforation() {
  return (
    <div
      aria-hidden="true"
      className="relative mx-6 border-t-2 border-dashed border-paper-300 lg:mx-0 lg:my-6 lg:border-t-0 lg:border-l-2"
    />
  )
}

function DemoAccounts({
  config,
  onUse,
}: {
  config: ConfigResponse
  onUse: (email: string, password: string) => void
}) {
  const password = config.demo_password ?? ''
  return (
    <aside aria-labelledby="demo-heading" className="space-y-3 p-6">
      <h2 id="demo-heading" className="font-bold">
        Demo accounts
      </h2>
      <ul className="space-y-3">
        {(config.demo_accounts ?? []).map((account) => (
          <li key={account.email} className="space-y-1">
            <p className="font-bold">
              {account.display_name} · {account.role}
            </p>
            <p className="font-board text-sm break-all">{account.email}</p>
            <p className="text-sm text-paper-muted">{account.purpose}</p>
            <Button variant="paper-secondary" onClick={() => onUse(account.email, password)}>
              Use this account
            </Button>
          </li>
        ))}
      </ul>
      <p className="text-sm">
        Password for all demo accounts: <span className="font-board">{password}</span>
      </p>
    </aside>
  )
}
