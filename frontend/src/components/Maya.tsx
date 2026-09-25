import { Footprints } from 'lucide-react'
import { motion } from 'framer-motion'

import type { Mood } from '../api/types'
import curious from '../assets/maya/curious.svg'
import encouraging from '../assets/maya/encouraging.svg'
import proud from '../assets/maya/proud.svg'
import worried from '../assets/maya/worried.svg'
import { EASE, MOTION } from '../lib/motion'

const PORTRAITS: Record<Mood, string> = { curious, encouraging, proud, worried }

type PortraitProps = {
  mood: Mood
  size: 20 | 40 | 56 | 72 | 96 | 128
  decorative?: boolean
  className?: string
}

export function MayaPortrait({ mood, size, decorative = false, className = '' }: PortraitProps) {
  return (
    <img
      src={PORTRAITS[mood]}
      width={size}
      height={size}
      alt={decorative ? '' : `Maya, looking ${mood}`}
      className={`shrink-0 rounded-full shadow-lamp ${className}`}
      style={{ width: size, height: size }}
    />
  )
}

export type BubbleKind = 'line' | 'hint' | 'rescue' | 'reaction' | 'waiting'

type BubbleProps = { lines: string[]; kind: BubbleKind; className?: string }

/** Maya speaking. A hint looks exactly like any other line (no "Hint" label, PRODUCT §10). */
export function MayaBubble({ lines, kind, className = '' }: BubbleProps) {
  const text = kind === 'waiting' ? ['One moment…'] : lines.filter(Boolean)
  if (text.length === 0) return null
  return (
    <motion.div
      initial={{ opacity: 0, y: 4 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: MOTION.quick, ease: EASE.enter }}
      className={`rounded-card border-l-4 border-maya-300 bg-ink-800/95 px-4 py-3 ${kind === 'rescue' ? 'shadow-lamp' : ''} ${className}`}
    >
      {kind === 'rescue' ? (
        <p className="mb-1 flex items-center gap-1.5 text-xs font-bold tracking-wide text-maya-300 uppercase">
          <Footprints aria-hidden="true" className="size-4" /> Maya&apos;s shortcut
        </p>
      ) : null}
      <p className="text-xs font-bold tracking-wide text-maya-300 uppercase">Maya</p>
      <div className="space-y-2 text-base md:text-lg">
        {text.map((line, index) => (
          <p key={index} className={kind === 'waiting' ? 'italic' : ''}>
            {line}
          </p>
        ))}
      </div>
    </motion.div>
  )
}
