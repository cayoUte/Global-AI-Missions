import { Volume2 } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'

import { Button } from '../../../components/Button'
import { InlineNotice } from '../../../components/InlineNotice'
import { isTypingTarget, useHotkeys } from '../../../lib/hotkeys'
import { resolveVoice, speak, stopSpeaking } from '../../../lib/speech'

type Status = 'checking' | 'idle' | 'speaking' | 'played' | 'unavailable'

type Props = { speaker: string | null; audioScript: string; rate: number }

/**
 * A platform announcement played with speechSynthesis (UI_SPEC §9.3.4). No transcript is shown
 * unless speech is unavailable on this device (PD-014), in which case the story continues on text.
 */
export function Announcement({ speaker, audioScript, rate }: Props) {
  const [status, setStatus] = useState<Status>('checking')
  const [played, setPlayed] = useState(false)
  const voice = useRef<SpeechSynthesisVoice | null>(null)

  useEffect(() => {
    let alive = true
    resolveVoice().then((found) => {
      if (!alive) return
      voice.current = found
      setStatus(found ? 'idle' : 'unavailable')
    })
    return () => {
      alive = false
      stopSpeaking()
    }
  }, [])

  const play = () => {
    if (status === 'unavailable' || status === 'checking') return
    setStatus('speaking') // before speak(): an error may be reported synchronously
    speak(audioScript, rate, voice.current, {
      onStart: () => setStatus('speaking'),
      onEnd: () => {
        setPlayed(true)
        setStatus('played')
      },
      onError: () => setStatus('unavailable'),
    })
  }

  useHotkeys((event) => {
    if ((event.key === 'l' || event.key === 'L') && !isTypingTarget(event.target)) {
      event.preventDefault()
      play()
    }
  }, status !== 'unavailable')

  const label = speaker ?? 'Announcement'

  if (status === 'unavailable') {
    return (
      <div className="space-y-3">
        <InlineNotice tone="info" message="Audio isn't available on this device" />
        <div className="rounded-board bg-ink-950 p-3 shadow-board">
          <p className="text-xs font-bold tracking-wide text-fog-200 uppercase">{label}</p>
          <p className="mt-1 text-base whitespace-pre-line text-amber-400">{audioScript}</p>
        </div>
      </div>
    )
  }

  const speaking = status === 'speaking'
  return (
    <div className="space-y-3 rounded-card border border-ink-600 bg-ink-950/90 p-4">
      <p className="flex items-center gap-2 text-xs font-bold tracking-wide text-fog-200 uppercase">
        <Volume2 aria-hidden="true" className="size-5" />
        {label}
        <Waveform active={speaking} />
      </p>
      <Button
        variant="secondary"
        size="lg"
        className="w-full sm:w-auto"
        onClick={play}
        aria-keyshortcuts="L"
      >
        {speaking ? 'Listening…' : played ? 'Listen again' : 'Listen'}
        <kbd className="ml-2 hidden text-xs text-fog-400 lg:inline">L</kbd>
      </Button>
      <p className="sr-only" role="status">
        {speaking ? 'Playing the announcement.' : ''}
      </p>
    </div>
  )
}

/** Should: five bars that move only while speaking (static under reduced motion). */
function Waveform({ active }: { active: boolean }) {
  return (
    <span aria-hidden="true" className="ml-auto flex h-4 items-center gap-0.5">
      {[0, 120, 240, 360, 480].map((delay) => (
        <span
          key={delay}
          className={`h-full w-1 origin-center rounded-full bg-amber-400 ${active ? 'animate-waveform' : 'scale-y-25'}`}
          style={{ animationDelay: `${delay}ms` }}
        />
      ))}
    </span>
  )
}
