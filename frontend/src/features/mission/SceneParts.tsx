import { forwardRef } from 'react'

import type { SceneLine } from '../../api/types'
import { speakerLabel } from './speakers'

export const SceneKicker = forwardRef<HTMLParagraphElement, { location: string }>(
  function SceneKicker({ location }, ref) {
    return (
      <p
        ref={ref}
        className="inline-block scroll-mt-20 rounded-full bg-ink-950/70 px-3 py-1 text-xs font-bold tracking-board text-fog-200 uppercase"
      >
        {location}
      </p>
    )
  },
)

type DialogueProps = {
  lines: SceneLine[]
  /** Typewriter: characters revealed so far across the lines; omitted → the full text. */
  shown?: number
  /** Click or tap while typing → complete the text (UI_SPEC §7). */
  onSkip?: () => void
}

/**
 * Scene lines; a speaker label shows only when the speaker changes (UI_SPEC §5 DialogueBox).
 * While the typewriter runs, the hidden rest of each line stays in the layout (`invisible`), so
 * the box never grows or jumps, and screen readers get the full line from a visually hidden copy.
 */
export function DialogueBox({ lines, shown, onSkip }: DialogueProps) {
  if (lines.length === 0) return null
  const typing = shown !== undefined && shown < lines.reduce((n, l) => n + l.text.length, 0)
  const reveal = shown ?? Number.POSITIVE_INFINITY
  // Where each line starts in the typewriter's character count (lines type one after another).
  const starts = lines.map((_, i) => lines.slice(0, i).reduce((n, l) => n + l.text.length, 0))
  return (
    <div
      onClick={typing ? onSkip : undefined}
      data-typewriter={typing ? 'typing' : 'done'}
      className={`space-y-2 rounded-card bg-ink-800/95 p-4 text-base shadow-raised md:p-5 md:text-lg ${typing ? 'cursor-pointer' : ''}`}
    >
      {lines.map((line, index) => {
        const changed = index === 0 || lines[index - 1].speaker !== line.speaker
        const { label, tone } = speakerLabel(line.speaker)
        const visible = Math.max(0, Math.min(line.text.length, reveal - starts[index]))
        return (
          <div key={index}>
            {changed && label ? (
              <p className={`text-xs font-bold tracking-wide uppercase ${tone}`}>{label}</p>
            ) : null}
            <p className="whitespace-pre-line">
              {visible < line.text.length ? (
                <>
                  <span className="sr-only">{line.text}</span>
                  <span aria-hidden="true">
                    {line.text.slice(0, visible)}
                    <span className="invisible">{line.text.slice(visible)}</span>
                  </span>
                </>
              ) : (
                line.text
              )}
            </p>
          </div>
        )
      })}
    </div>
  )
}
