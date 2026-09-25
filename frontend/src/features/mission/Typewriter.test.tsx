import { act, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import type { SceneLine } from '../../api/types'
import { useTypewriter } from '../../lib/useTypewriter'
import { ContinueAction } from './MissionPlayerPage'
import { DialogueBox } from './SceneParts'

// framer-motion's useReducedMotion, switchable per test.
const motion = vi.hoisted(() => ({ reduced: false }))
vi.mock('framer-motion', async (importOriginal) => ({
  ...(await importOriginal<typeof import('framer-motion')>()),
  useReducedMotion: () => motion.reduced,
}))

const LINES: SceneLine[] = [
  { speaker: 'narrator', text: 'The board flickers above the concourse.' }, // 39 chars
  { speaker: 'Guard', text: 'Last train in twelve minutes.' },
]

function Scene({ onContinue }: { onContinue: () => void }) {
  const total = LINES.reduce((n, l) => n + l.text.length, 0)
  const typewriter = useTypewriter('n1', total)
  return (
    <>
      <DialogueBox lines={LINES} shown={typewriter.shown} onSkip={typewriter.complete} />
      <ContinueAction
        disabled={false}
        slow={false}
        typing={typewriter.typing}
        onComplete={typewriter.complete}
        onContinue={onContinue}
      />
    </>
  )
}

const box = () => document.querySelector('[data-typewriter]') as HTMLElement
/** The visible (typed) part of each line still being typed, joined with "|". */
const shownText = () =>
  Array.from(box().querySelectorAll('[aria-hidden="true"]'), (el) => {
    const copy = el.cloneNode(true) as HTMLElement
    copy.querySelector('.invisible')?.remove()
    return copy.textContent
  }).join('|')

describe('typewriter', () => {
  beforeEach(() => {
    motion.reduced = false
    vi.useFakeTimers()
  })
  afterEach(() => vi.useRealTimers())

  it('types at 30 characters per second, line by line, with the full text for screen readers', () => {
    render(<Scene onContinue={vi.fn()} />)
    expect(box()).toHaveAttribute('data-typewriter', 'typing')
    // The full lines are there from the start (visually hidden), so nothing is streamed to AT.
    const copies = box().querySelectorAll('.sr-only')
    expect(Array.from(copies, (el) => el.textContent)).toEqual(LINES.map((l) => l.text))
    act(() => vi.advanceTimersByTime(1050)) // about 30 characters, all on the first line
    expect(shownText()).toMatch(/^The board flickers above the co?n?\|$/)
    act(() => vi.advanceTimersByTime(500)) // the first line is done; the second has begun
    expect(box()).toHaveAttribute('data-typewriter', 'typing')
    expect(screen.getByText('The board flickers above the concourse.')).not.toHaveClass('sr-only')
    expect(shownText()).toMatch(/^Last t/)
    act(() => vi.advanceTimersByTime(2000))
    expect(box()).toHaveAttribute('data-typewriter', 'done')
    expect(box()).toHaveTextContent(
      'The board flickers above the concourse.GuardLast train in twelve minutes.',
    )
  })

  it('first Continue completes the text, the second advances', () => {
    const onContinue = vi.fn()
    render(<Scene onContinue={onContinue} />)
    const next = screen.getByRole('button', { name: 'Continue' })
    fireEvent.click(next)
    expect(box()).toHaveAttribute('data-typewriter', 'done')
    expect(onContinue).not.toHaveBeenCalled()
    fireEvent.click(next)
    expect(onContinue).toHaveBeenCalledTimes(1)
  })

  it('a click on the dialogue completes the text', () => {
    render(<Scene onContinue={vi.fn()} />)
    fireEvent.click(box())
    expect(box()).toHaveAttribute('data-typewriter', 'done')
  })

  it('reduced motion shows the full text at once and Continue advances on the first press', () => {
    motion.reduced = true
    const onContinue = vi.fn()
    render(<Scene onContinue={onContinue} />)
    expect(box()).toHaveAttribute('data-typewriter', 'done')
    expect(screen.getByText('Last train in twelve minutes.')).not.toHaveClass('sr-only')
    fireEvent.click(screen.getByRole('button', { name: 'Continue' }))
    expect(onContinue).toHaveBeenCalledTimes(1)
  })
})
