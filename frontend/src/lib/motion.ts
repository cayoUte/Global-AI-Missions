// Motion constants (seconds) mirroring tokens.css (UI_SPEC §7). MotionConfig reducedMotion="user"
// wraps the app, so Framer Motion drops transforms when the user prefers reduced motion.
export const MOTION = {
  quick: 0.18,
  scene: 0.4,
  consequence: 0.5,
  flip: 0.24,
  reduced: 0.12,
} as const
export const EASE = {
  scene: [0.4, 0, 0.2, 1],
  enter: [0.16, 1, 0.3, 1],
  exit: [0.7, 0, 0.84, 0],
} as const
export const TYPEWRITER_CPS = 30
