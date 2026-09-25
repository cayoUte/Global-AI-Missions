export type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'paper' | 'paper-secondary'

const VARIANTS: Record<ButtonVariant, string> = {
  primary: 'bg-amber-400 text-ink-950 font-bold hover:bg-amber-200',
  secondary: 'border border-line-strong text-fog-50 hover:bg-ink-700',
  ghost: 'text-fog-50 hover:underline underline-offset-4',
  paper: 'bg-paper-ink text-paper-50 font-bold hover:opacity-90',
  'paper-secondary': 'border border-paper-muted text-paper-ink hover:bg-paper-300',
}

/** Button styles, shared by <Button> and by router links that look like buttons. */
export function buttonClasses(
  variant: ButtonVariant = 'primary',
  size: 'md' | 'lg' = 'md',
  extra = '',
): string {
  return [
    'inline-flex items-center justify-center gap-2 rounded-control px-4 text-base transition-colors duration-(--motion-quick)',
    size === 'lg' ? 'min-h-14' : 'min-h-11',
    VARIANTS[variant],
    extra,
  ].join(' ')
}
