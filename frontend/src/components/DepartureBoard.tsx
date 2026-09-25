import { Bus } from 'lucide-react'

import type { Clock } from '../api/types'
import { splitClockLabel } from '../lib/format'

type Props = { clock: Clock | null; className?: string }

/**
 * The story clock (UI_SPEC §9.3.2). Renders the server's label verbatim; the split on the first
 * " · " is layout only. Never a countdown, never ticks by itself.
 */
export function DepartureBoard({ clock, className = '' }: Props) {
  if (!clock) {
    return (
      <div
        aria-hidden="true"
        className={`min-w-[8.5rem] rounded-board bg-ink-950 px-3 py-2 font-board text-2xl text-amber-400 shadow-board ${className}`}
      >
        — · —
      </div>
    )
  }
  const [time, rest] = splitClockLabel(clock.label)
  const departed = clock.train_departed
  return (
    <div
      role="img"
      aria-label={clock.label}
      className={`min-w-[8.5rem] rounded-board bg-ink-950 px-3 py-2 font-board tracking-board uppercase lg:min-w-[13rem] ${
        departed
          ? 'text-fog-200 shadow-[0_0_0_1px_var(--color-ink-600)_inset]'
          : 'text-amber-400 shadow-board'
      } ${className}`}
    >
      <span
        aria-hidden="true"
        className={rest ? 'block text-2xl tabular-nums lg:text-4xl' : 'block text-xs lg:text-sm'}
      >
        {time}
      </span>
      {rest ? (
        <span
          aria-hidden="true"
          className="flex max-w-[11rem] items-center gap-1 text-xs lg:max-w-none lg:text-sm"
        >
          {departed ? <Bus className="size-4 shrink-0" /> : null}
          {rest}
        </span>
      ) : null}
    </div>
  )
}
