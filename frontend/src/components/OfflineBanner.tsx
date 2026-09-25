import { WifiOff } from 'lucide-react'

import { useOnline } from '../lib/useOnline'

export const OFFLINE_DEFAULT = "You're offline. We'll reconnect when the signal comes back."

export function OfflineBanner({ message = OFFLINE_DEFAULT }: { message?: string }) {
  const online = useOnline()
  if (online) return null
  return (
    <div
      role="status"
      className="fixed inset-x-0 top-0 z-40 flex items-center justify-center gap-2 bg-ink-950 px-4 py-2 text-sm text-fog-50"
    >
      <WifiOff aria-hidden="true" className="size-5" />
      {message}
    </div>
  )
}
