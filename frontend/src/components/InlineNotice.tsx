import { CircleAlert, Info, WifiOff } from 'lucide-react'
import type { ReactNode } from 'react'

type Props = {
  tone: 'info' | 'problem' | 'offline'
  title?: string
  message: ReactNode
  action?: ReactNode
  onPaper?: boolean
  className?: string
}

/** Errors are text + icon + a line-strong edge: there is no error color (UI_SPEC §3.1). */
export function InlineNotice({
  tone,
  title,
  message,
  action,
  onPaper = false,
  className = '',
}: Props) {
  const Icon = tone === 'problem' ? CircleAlert : tone === 'offline' ? WifiOff : Info
  const surface = onPaper
    ? 'border-paper-ink text-paper-ink bg-paper-50'
    : 'border-line-strong bg-ink-800 text-fog-50'
  return (
    <div
      role={tone === 'problem' ? 'alert' : 'status'}
      className={`rounded-card border-l-4 p-4 ${surface} ${className}`}
    >
      <div className="flex items-start gap-3">
        <Icon aria-hidden="true" className="mt-0.5 size-5 shrink-0" />
        <div className="min-w-0 flex-1 space-y-3">
          <div>
            {title ? <p className="font-bold">{title}</p> : null}
            <p>{message}</p>
          </div>
          {action}
        </div>
      </div>
    </div>
  )
}
