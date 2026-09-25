import { AnimatePresence, motion, useReducedMotion } from 'framer-motion'
import { Bus } from 'lucide-react'

import type { Clock } from '../api/types'
import { splitClockLabel } from '../lib/format'
import { EASE, MOTION } from '../lib/motion'

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
        {rest ? <FlipText text={time} /> : time}
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

const HALF_FLIP = MOTION.flip / 2 // 120 ms out, then 120 ms in

/**
 * Clock flip (UI_SPEC §7, Should): each character sits in its own slot, keyed by the character,
 * so only the characters that change flip (old 0→-90°, then new 90→0°). Nothing animates on the
 * first render; reduced motion swaps the text instantly. The board's aria-label carries the time,
 * so this is all aria-hidden.
 */
export function FlipText({ text }: { text: string }) {
  const reduced = useReducedMotion() === true
  if (reduced) return <>{text}</>
  return (
    <>
      {Array.from(text).map((char, index) => (
        <span
          key={index}
          data-flip-slot=""
          className="inline-block whitespace-pre [perspective:400px]"
        >
          <AnimatePresence mode="wait" initial={false}>
            <motion.span
              key={char}
              className="inline-block"
              initial={{ rotateX: 90 }}
              animate={{ rotateX: 0, transition: { duration: HALF_FLIP, ease: EASE.enter } }}
              exit={{ rotateX: -90, transition: { duration: HALF_FLIP, ease: EASE.exit } }}
            >
              {char}
            </motion.span>
          </AnimatePresence>
        </span>
      ))}
    </>
  )
}
