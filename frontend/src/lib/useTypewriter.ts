import { useReducedMotion } from 'framer-motion'
import { useCallback, useEffect, useRef, useState } from 'react'

import { TYPEWRITER_CPS } from './motion'

export type Typewriter = {
  /** Characters revealed so far, counted across the lines in order. */
  shown: number
  /** True while some text is still hidden. */
  typing: boolean
  /** Reveal everything now (click on the dialogue, Space, or the first Continue). */
  complete: () => void
}

/**
 * The scene typewriter (UI_SPEC §7, Should): `total` characters at TYPEWRITER_CPS, restarting
 * whenever `resetKey` (the node id) changes. Reduced motion → everything at once. Presentation
 * only: the live region and the server state never wait for it.
 */
export function useTypewriter(resetKey: string, total: number): Typewriter {
  const reduced = useReducedMotion() === true
  const [progress, setProgress] = useState({ key: resetKey, shown: 0 })
  const timer = useRef<number | undefined>(undefined)

  const shown = reduced ? total : progress.key === resetKey ? Math.min(progress.shown, total) : 0

  useEffect(() => {
    if (reduced || total === 0) return
    const start = performance.now()
    const id = window.setInterval(() => {
      const next = Math.min(
        total,
        Math.floor(((performance.now() - start) / 1000) * TYPEWRITER_CPS),
      )
      setProgress((p) =>
        p.key === resetKey && p.shown >= next ? p : { key: resetKey, shown: next },
      )
      if (next >= total) window.clearInterval(id)
    }, 1000 / TYPEWRITER_CPS)
    timer.current = id
    return () => window.clearInterval(id)
  }, [resetKey, total, reduced])

  const complete = useCallback(() => {
    window.clearInterval(timer.current)
    setProgress({ key: resetKey, shown: total })
  }, [resetKey, total])

  return { shown, typing: shown < total, complete }
}
