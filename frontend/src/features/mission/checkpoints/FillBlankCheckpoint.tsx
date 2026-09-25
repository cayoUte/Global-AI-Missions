import { useEffect, useRef, useState, type CSSProperties } from 'react'

import { ActionBar } from '../ActionBar'
import { SpeechBubble } from './StimulusView'
import { promptId, useConfirmOnce, type CheckpointProps } from './types'

const GAP = '___'
const MAX_CHARS = 80

/**
 * fill_blank: the prompt is the student's own line with one gap; a single text input sits in the
 * gap. Confirm is enabled only when the trimmed text is not empty, and sends the trimmed text.
 */
export function FillBlankCheckpoint({ checkpoint, locked, slow, onConfirm }: CheckpointProps) {
  const [text, setText] = useState('')
  const confirm = useConfirmOnce(locked, onConfirm)
  const inputRef = useRef<HTMLInputElement>(null)
  const trimmed = text.trim()
  const ready = trimmed.length > 0 && trimmed.length <= MAX_CHARS

  useEffect(() => {
    inputRef.current?.focus({ preventScroll: true })
  }, [])

  const tryConfirm = () => {
    if (ready) confirm({ text: trimmed })
  }

  const at = checkpoint.prompt.indexOf(GAP)
  const before = at === -1 ? checkpoint.prompt : checkpoint.prompt.slice(0, at)
  const after = at === -1 ? '' : checkpoint.prompt.slice(at + GAP.length)
  const describedBy = `${promptId(checkpoint.item_id)}-sr`
  const chars = Math.min(18, Math.max(6, text.length))
  const dialogue =
    checkpoint.stimulus && checkpoint.stimulus.kind !== 'audio' ? checkpoint.stimulus : null

  return (
    <div className="space-y-4">
      {dialogue ? <SpeechBubble speaker={dialogue.speaker} text={dialogue.text} /> : null}
      <div className="rounded-card bg-ink-800/95 p-4 text-lg shadow-raised">
        <p className="text-xs font-bold tracking-wide text-amber-400 uppercase">You</p>
        <p id={promptId(checkpoint.item_id)} className="leading-10">
          {before}
          <input
            ref={inputRef}
            type="text"
            value={text}
            readOnly={locked}
            maxLength={MAX_CHARS}
            autoComplete="off"
            autoCorrect="off"
            autoCapitalize="off"
            spellCheck={false}
            enterKeyHint="done"
            aria-label="Your words for the gap"
            aria-describedby={describedBy}
            onChange={(event) => setText(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === 'Enter' && !event.nativeEvent.isComposing) {
                event.preventDefault()
                tryConfirm()
              }
            }}
            style={{ '--chars': chars } as CSSProperties}
            className="mx-1 inline-block w-[calc(var(--chars)*1ch+2ch)] max-w-full min-w-[6ch] rounded-t-board border-b-2 border-amber-400 bg-ink-950 px-2 py-1 font-bold text-amber-200"
          />
          {after}
        </p>
        <p id={describedBy} className="sr-only">
          {before}
          blank
          {after}
        </p>
      </div>
      <p className="text-sm text-fog-400">Type the missing words.</p>
      <ActionBar
        label="Confirm"
        onClick={tryConfirm}
        disabled={!ready || locked}
        loading={locked && slow}
        loadingLabel="One moment…"
      />
    </div>
  )
}
