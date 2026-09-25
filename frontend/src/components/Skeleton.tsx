export function Skeleton({ className = '' }: { className?: string }) {
  return (
    <div aria-hidden="true" className={`animate-skeleton rounded-card bg-ink-700 ${className}`} />
  )
}
