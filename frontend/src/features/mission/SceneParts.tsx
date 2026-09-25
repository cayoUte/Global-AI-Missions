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

/** Scene lines; a speaker label shows only when the speaker changes (UI_SPEC §5 DialogueBox). */
export function DialogueBox({ lines }: { lines: SceneLine[] }) {
  if (lines.length === 0) return null
  return (
    <div className="space-y-2 rounded-card bg-ink-800/95 p-4 text-base shadow-raised md:p-5 md:text-lg">
      {lines.map((line, index) => {
        const changed = index === 0 || lines[index - 1].speaker !== line.speaker
        const { label, tone } = speakerLabel(line.speaker)
        return (
          <div key={index}>
            {changed && label ? (
              <p className={`text-xs font-bold tracking-wide uppercase ${tone}`}>{label}</p>
            ) : null}
            <p className="whitespace-pre-line">{line.text}</p>
          </div>
        )
      })}
    </div>
  )
}
