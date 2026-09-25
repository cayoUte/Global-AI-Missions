import { LogOut } from 'lucide-react'
import type { ReactNode } from 'react'
import { useEffect, useRef } from 'react'
import { NavLink } from 'react-router'

import { useCheckOut } from '../features/auth/useCheckOut'
import { Button } from './Button'
import { OfflineBanner } from './OfflineBanner'

export type NavItem = { to: string; label: string }

const STUDENT_NAV: NavItem[] = [
  { to: '/world', label: 'English World' },
  { to: '/progress', label: 'Progress' },
]

function NavItems({ items, className }: { items: NavItem[]; className: string }) {
  return (
    <>
      {items.map((item) => (
        <NavLink
          key={item.to}
          to={item.to}
          className={({ isActive }) =>
            `${className} flex min-h-11 items-center justify-center px-3 text-fog-200 hover:text-fog-50 ${
              isActive
                ? 'border-b-2 border-amber-400 font-bold text-fog-50'
                : 'border-b-2 border-transparent'
            }`
          }
        >
          {item.label}
        </NavLink>
      ))}
    </>
  )
}

type Props = {
  children: ReactNode
  nav?: boolean
  /** The nav links; the student's English World and Progress by default. */
  navItems?: NavItem[]
  width?: 'world' | 'player'
}

/** Shell for English World, Progress, Mission Report and the teacher page (UI_SPEC §4). */
export function AppShell({ children, nav = true, navItems = STUDENT_NAV, width = 'world' }: Props) {
  const checkOut = useCheckOut()
  return (
    <div className="min-h-dvh bg-ink-900">
      <OfflineBanner />
      <header className="sticky top-0 z-20 border-b border-ink-600 bg-ink-950/80 backdrop-blur">
        <div className="mx-auto flex h-14 max-w-world items-center gap-4 px-4 md:px-6 lg:px-8">
          <span className="font-display text-lg font-semibold">Global AI Missions</span>
          {nav ? (
            <nav aria-label="Main" className="ml-4 hidden gap-2 md:flex">
              <NavItems items={navItems} className="" />
            </nav>
          ) : null}
          <Button
            variant="ghost"
            className="ml-auto"
            icon={<LogOut className="size-5" />}
            loading={checkOut.isPending}
            loadingLabel="Check out"
            onClick={() => checkOut.mutate()}
          >
            Check out
          </Button>
        </div>
        {nav ? (
          <nav
            aria-label="Main"
            className={`grid h-11 border-t border-ink-600 md:hidden ${navItems.length === 1 ? 'grid-cols-1' : 'grid-cols-2'}`}
          >
            <NavItems items={navItems} className="w-full" />
          </nav>
        ) : null}
      </header>
      <main
        className={`mx-auto px-4 py-6 md:px-6 md:py-10 lg:px-8 ${width === 'world' ? 'max-w-world' : 'max-w-player'}`}
      >
        {children}
      </main>
    </div>
  )
}

/** One h1 per screen; focus it on route change (UI_SPEC §8). */
export function PageHeading({
  children,
  className = '',
  srOnly = false,
}: {
  children: ReactNode
  className?: string
  srOnly?: boolean
}) {
  const ref = useRef<HTMLHeadingElement>(null)
  useEffect(() => {
    ref.current?.focus({ preventScroll: true })
  }, [])
  return (
    <h1 ref={ref} tabIndex={-1} className={`outline-none ${srOnly ? 'sr-only' : ''} ${className}`}>
      {children}
    </h1>
  )
}
