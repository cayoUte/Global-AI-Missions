export function Tag({ text, onPaper = false }: { text: string; onPaper?: boolean }) {
  const tone = onPaper ? 'border-paper-muted text-paper-muted' : 'border-line-strong text-fog-200'
  return (
    <span
      className={`inline-block rounded-board border px-2 py-0.5 text-xs font-bold tracking-wide uppercase ${tone}`}
    >
      {text}
    </span>
  )
}
