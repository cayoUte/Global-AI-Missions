import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { resetSpeechState } from '../../../lib/speech'
import { Announcement } from './Announcement'

const SCRIPT = 'The last train to Oxford will leave from platform seven.'

type FakeUtterance = {
  text: string
  rate: number
  onerror?: (e: { error: string }) => void
  onend?: () => void
  onstart?: () => void
}

function installSpeech(voices: { lang: string; name: string }[], behaviour: 'ok' | 'error' = 'ok') {
  const spoken: FakeUtterance[] = []
  class Utterance {
    text: string
    rate = 1
    lang = ''
    voice: unknown = null
    onerror?: (e: { error: string }) => void
    onend?: () => void
    onstart?: () => void
    constructor(text: string) {
      this.text = text
    }
  }
  vi.stubGlobal('SpeechSynthesisUtterance', Utterance)
  vi.stubGlobal('speechSynthesis', {
    getVoices: () => voices,
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    cancel: vi.fn(),
    speak: (u: FakeUtterance) => {
      spoken.push(u)
      if (behaviour === 'error') u.onerror?.({ error: 'synthesis-failed' })
      else u.onstart?.()
    },
  })
  return spoken
}

describe('Announcement (listening)', () => {
  beforeEach(() => resetSpeechState())
  afterEach(() => vi.unstubAllGlobals())

  it('plays the script with the stimulus rate and never shows the transcript', async () => {
    const spoken = installSpeech([
      { lang: 'en-US', name: 'US' },
      { lang: 'en-GB', name: 'GB' },
    ])
    const user = userEvent.setup()
    render(<Announcement speaker="Station announcer" audioScript={SCRIPT} rate={0.85} />)
    await user.click(await screen.findByRole('button', { name: /^Listen/ }))
    expect(spoken).toHaveLength(1)
    expect(spoken[0]).toMatchObject({ text: SCRIPT, rate: 0.85 })
    expect(screen.queryByText(SCRIPT)).not.toBeInTheDocument()
  })

  it('falls back to the written announcement when speechSynthesis is missing (PD-014)', async () => {
    // jsdom has no speechSynthesis: the default environment is the "missing" case.
    render(<Announcement speaker="Station announcer" audioScript={SCRIPT} rate={0.85} />)
    expect(await screen.findByText("Audio isn't available on this device")).toBeInTheDocument()
    expect(screen.getByText(SCRIPT)).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /^Listen/ })).not.toBeInTheDocument()
  })

  it('falls back when no English voice appears', async () => {
    installSpeech([{ lang: 'es-ES', name: 'ES' }])
    render(<Announcement speaker="Station announcer" audioScript={SCRIPT} rate={1} />)
    expect(
      await screen.findByText("Audio isn't available on this device", {}, { timeout: 3000 }),
    ).toBeInTheDocument()
    expect(screen.getByText(SCRIPT)).toBeInTheDocument()
  })

  it('falls back when the utterance fails', async () => {
    installSpeech([{ lang: 'en-GB', name: 'GB' }], 'error')
    const user = userEvent.setup()
    render(<Announcement speaker="Station announcer" audioScript={SCRIPT} rate={1} />)
    await user.click(await screen.findByRole('button', { name: /^Listen/ }))
    expect(await screen.findByText("Audio isn't available on this device")).toBeInTheDocument()
    expect(screen.getByText(SCRIPT)).toBeInTheDocument()
  })
})
