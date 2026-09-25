import { Pause } from 'lucide-react'
import type { ReactNode } from 'react'
import { useNavigate } from 'react-router'

import type { Clock } from '../../api/types'
import { SceneBackdrop } from '../../components/Backdrop'
import { Button } from '../../components/Button'
import { DepartureBoard } from '../../components/DepartureBoard'
import { OfflineBanner } from '../../components/OfflineBanner'

export const SIGNAL_DROPPED = 'The signal dropped. Your place in the story is saved.'

type FrameProps = {
  backdrop: string
  /** null → the board skeleton; undefined → no board (the Ending shows it inline). */
  clock?: Clock | null
  title: string
  wide?: boolean
  children: ReactNode
}

/** Full-bleed scene: fixed crossfading backdrop, top bar (Pause · title · story clock), column. */
export function PlayerFrame({ backdrop, clock, title, wide = false, children }: FrameProps) {
  const navigate = useNavigate()
  return (
    <div className="relative min-h-dvh overflow-x-hidden">
      <SceneBackdrop backdropKey={backdrop} />
      <OfflineBanner message={SIGNAL_DROPPED} />
      <header className="relative z-20 flex items-start justify-between gap-3 bg-gradient-to-b from-ink-950/80 to-transparent px-4 pt-3 pb-6 md:px-6">
        <Button
          variant="ghost"
          icon={<Pause className="size-5" />}
          onClick={() => navigate('/world')}
        >
          Pause
        </Button>
        {title ? (
          <p className="hidden self-center font-display text-sm text-fog-200 md:block">{title}</p>
        ) : null}
        {clock !== undefined ? <DepartureBoard clock={clock} /> : null}
      </header>
      <div
        className={`relative z-10 mx-auto px-4 pt-[22vh] pb-8 md:px-6 ${wide ? 'max-w-player lg:max-w-[64rem]' : 'max-w-player'}`}
      >
        {children}
      </div>
    </div>
  )
}
