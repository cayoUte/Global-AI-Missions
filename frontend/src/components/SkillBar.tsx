import type { Skill } from '../api/types'
import { skillName } from '../lib/format'

type Props = { skill: Skill; pct: number; correct?: number; total?: number; size?: 'md' | 'sm' }

/** The % is always written, so the bar's color is never the only signal (UI_SPEC §5). */
export function SkillBar({ skill, pct, correct, total, size = 'md' }: Props) {
  const hasCount = correct !== undefined && total !== undefined
  const label = `${skillName(skill)} ${pct}%${hasCount ? `, ${correct} of ${total}` : ''}`
  return (
    <div role="img" aria-label={label} className="space-y-1">
      <div aria-hidden="true" className="flex items-baseline gap-2 text-sm">
        <span className="font-bold">{skillName(skill)}</span>
        {hasCount ? (
          <span className="text-fog-400">
            {correct} of {total}
          </span>
        ) : null}
        <span className="ml-auto tabular-nums">{pct}%</span>
      </div>
      <div
        aria-hidden="true"
        className={`${size === 'md' ? 'h-2' : 'h-1.5'} overflow-hidden rounded-full bg-ink-700`}
      >
        <div
          className="h-full rounded-full bg-amber-400"
          style={{ width: `${Math.max(0, Math.min(100, pct))}%` }}
        />
      </div>
    </div>
  )
}
