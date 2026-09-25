/** A per-skill table cell: the % written out, with a micro-bar under it (UI_SPEC §9.6). */
export function SkillCell({ pct }: { pct: number | undefined }) {
  if (pct === undefined) return <td className="px-2 py-2 text-sm text-fog-400">—</td>
  return (
    <td className="px-2 py-2 text-sm tabular-nums">
      {pct}%
      <div
        aria-hidden="true"
        className="mt-1 h-1 w-full min-w-8 overflow-hidden rounded-full bg-ink-700"
      >
        <div className="h-full bg-amber-400" style={{ width: `${pct}%` }} />
      </div>
    </td>
  )
}
