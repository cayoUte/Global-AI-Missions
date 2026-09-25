import { AnimatePresence, motion } from 'framer-motion'

import { EASE, MOTION } from '../lib/motion'

/** A static backdrop layer (UI_SPEC §6). Unknown keys fall back to concourse_night in CSS. */
export function Backdrop({
  backdropKey,
  className = '',
}: {
  backdropKey: string
  className?: string
}) {
  return <div className={`backdrop ${className}`} data-backdrop={backdropKey} aria-hidden="true" />
}

/** Fixed full-bleed backdrop that crossfades when the key changes (Must, < 600 ms). */
export function SceneBackdrop({ backdropKey }: { backdropKey: string }) {
  return (
    <div className="fixed inset-0 z-0" aria-hidden="true">
      <AnimatePresence initial={false}>
        <motion.div
          key={backdropKey}
          className="absolute inset-0"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: MOTION.scene, ease: EASE.scene }}
        >
          <Backdrop backdropKey={backdropKey} />
        </motion.div>
      </AnimatePresence>
    </div>
  )
}
