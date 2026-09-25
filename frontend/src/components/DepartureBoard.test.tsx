import { render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type { Clock } from '../api/types'
import { DepartureBoard } from './DepartureBoard'

const motion = vi.hoisted(() => ({ reduced: false }))
vi.mock('framer-motion', async (importOriginal) => ({
  ...(await importOriginal<typeof import('framer-motion')>()),
  useReducedMotion: () => motion.reduced,
}))

const clock = (time: string, minutes: number): Clock => ({
  time,
  minutes_left: minutes,
  label: `${time} · ${minutes} min to departure`,
  train_departed: false,
})

const slots = () => Array.from(document.querySelectorAll('[data-flip-slot] > span'))

describe('DepartureBoard clock flip', () => {
  beforeEach(() => {
    motion.reduced = false
  })

  it('is read once as the plain label, with the characters hidden from screen readers', () => {
    render(<DepartureBoard clock={clock('21:53', 12)} />)
    const board = screen.getByRole('img', { name: '21:53 · 12 min to departure' })
    for (const child of Array.from(board.children))
      expect(child).toHaveAttribute('aria-hidden', 'true')
    expect(slots().map((s) => s.textContent)).toEqual(['2', '1', ':', '5', '3'])
  })

  it('keeps the unchanged characters and flips only the ones that change', async () => {
    const { rerender } = render(<DepartureBoard clock={clock('21:53', 12)} />)
    const before = slots()
    rerender(<DepartureBoard clock={clock('21:55', 10)} />)
    // The "3" flips out, then the "5" flips in (mode="wait").
    await waitFor(() => expect(slots()[4]).toHaveTextContent('5'))
    const after = slots()
    expect(after).toHaveLength(5)
    // Slots 0–3 are the very same DOM nodes: unchanged characters never flip.
    before.slice(0, 4).forEach((node, index) => expect(after[index]).toBe(node))
    expect(after[4]).not.toBe(before[4])
    expect(screen.getByRole('img')).toHaveAccessibleName('21:55 · 10 min to departure')
  })

  it('swaps the text instantly under reduced motion', () => {
    motion.reduced = true
    render(<DepartureBoard clock={clock('21:53', 12)} />)
    expect(slots()).toHaveLength(0)
    expect(screen.getByRole('img')).toHaveTextContent('21:53')
  })
})
