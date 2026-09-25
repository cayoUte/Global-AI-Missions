// Listening stimuli are played with the Web Speech API (speechSynthesis). PD-013: unlimited
// replays. PD-014: when speech is unavailable the UI falls back to the written announcement.
// "Unavailable" means: no speechSynthesis, no English voice after voiceschanged (or a short
// timeout), or an utterance error other than interrupted/canceled. After the first failure the
// fallback stays on for the rest of the session.

let failedThisSession = false

export function markSpeechFailed(): void {
  failedThisSession = true
}

/** Test helper: forget a previous failure. */
export function resetSpeechState(): void {
  failedThisSession = false
}

export function hasSpeechSynthesis(): boolean {
  return (
    typeof window !== 'undefined' &&
    'speechSynthesis' in window &&
    typeof window.SpeechSynthesisUtterance === 'function'
  )
}

/** First en-GB voice, else the first English voice, else null. */
export function pickVoice(voices: SpeechSynthesisVoice[]): SpeechSynthesisVoice | null {
  const lang = (v: SpeechSynthesisVoice) => v.lang.replace('_', '-').toLowerCase()
  return (
    voices.find((v) => lang(v) === 'en-gb') ?? voices.find((v) => lang(v).startsWith('en')) ?? null
  )
}

/** Resolves to an English voice, or null when speech is unavailable on this device. */
export function resolveVoice(timeoutMs = 1500): Promise<SpeechSynthesisVoice | null> {
  if (failedThisSession || !hasSpeechSynthesis()) return Promise.resolve(null)
  const synth = window.speechSynthesis
  const now = pickVoice(synth.getVoices())
  if (now) return Promise.resolve(now)

  return new Promise((resolve) => {
    const finish = () => {
      clearTimeout(timer)
      synth.removeEventListener?.('voiceschanged', onChange)
      resolve(pickVoice(synth.getVoices()))
    }
    const onChange = () => {
      if (pickVoice(synth.getVoices())) finish()
    }
    const timer = setTimeout(finish, timeoutMs)
    synth.addEventListener?.('voiceschanged', onChange)
  })
}

type SpeakHandlers = { onStart: () => void; onEnd: () => void; onError: () => void }

/** Speak the script; pressing again cancels and restarts. */
export function speak(
  script: string,
  rate: number,
  voice: SpeechSynthesisVoice | null,
  handlers: SpeakHandlers,
): void {
  if (failedThisSession || !hasSpeechSynthesis()) {
    handlers.onError()
    return
  }
  const synth = window.speechSynthesis
  synth.cancel()
  const utterance = new SpeechSynthesisUtterance(script)
  utterance.rate = rate
  utterance.lang = voice?.lang ?? 'en-GB'
  if (voice) utterance.voice = voice
  utterance.onstart = handlers.onStart
  utterance.onend = handlers.onEnd
  utterance.onerror = (event: SpeechSynthesisErrorEvent) => {
    if (event.error === 'interrupted' || event.error === 'canceled') {
      handlers.onEnd()
      return
    }
    markSpeechFailed()
    handlers.onError()
  }
  synth.speak(utterance)
}

export function stopSpeaking(): void {
  if (hasSpeechSynthesis()) window.speechSynthesis.cancel()
}
