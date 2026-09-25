/** Report only. Same color for both: the shape and the word carry the meaning (UI_SPEC §5). */
export function OutcomeMarker({ outcome }: { outcome: 'understood' | 'missed' }) {
  return (
    <span className="inline-flex items-center gap-1.5 text-sm text-fog-200">
      <span
        aria-hidden="true"
        className={`inline-block size-2.5 rounded-full border-2 border-fog-200 ${outcome === 'understood' ? 'bg-fog-200' : ''}`}
      />
      {outcome === 'understood' ? 'Understood' : 'Missed'}
    </span>
  )
}
