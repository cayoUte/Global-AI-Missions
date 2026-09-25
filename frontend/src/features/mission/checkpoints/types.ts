import { useEffect, useRef } from 'react'

import type { CheckpointView } from '../../../api/types'

export type CheckpointAnswer = { option_id: string } | { text: string }

export type CheckpointProps = {
  checkpoint: CheckpointView
  clockTime: string
  /** True from Confirm until the server answers (and while Try again is offered). */
  locked: boolean
  /** Confirm's label after 1 s of waiting ("One moment…"). */
  slow: boolean
  onConfirm: (answer: CheckpointAnswer) => void
}

/**
 * Nothing is sent before Confirm, and Confirm sends exactly once: a second click (even in the same
 * tick, before the parent re-renders) is ignored until the checkpoint is unlocked again (a 422).
 */
export function useConfirmOnce(locked: boolean, onConfirm: (answer: CheckpointAnswer) => void) {
  const sent = useRef(false)
  useEffect(() => {
    if (!locked) sent.current = false
  }, [locked])
  return (answer: CheckpointAnswer) => {
    if (locked || sent.current) return
    sent.current = true
    onConfirm(answer)
  }
}

export const promptId = (itemId: string) => `prompt-${itemId}`
