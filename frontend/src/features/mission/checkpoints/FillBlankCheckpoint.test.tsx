import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import type { CheckpointView } from '../../../api/types'
import { FillBlankCheckpoint } from './FillBlankCheckpoint'

const checkpoint: CheckpointView = {
  item_id: 'q05',
  type: 'fill_blank',
  prompt: 'Could I ___ a single ticket, please?',
  stimulus: { kind: 'dialogue', speaker: 'Clerk', text: 'Next, please.' },
  options: null,
}

function setup(locked = false) {
  const onConfirm = vi.fn()
  render(
    <FillBlankCheckpoint
      checkpoint={checkpoint}
      clockTime="21:50"
      locked={locked}
      slow={false}
      onConfirm={onConfirm}
    />,
  )
  return {
    onConfirm,
    input: screen.getByLabelText('Your words for the gap'),
    confirm: screen.getByRole('button', { name: 'Confirm' }),
  }
}

describe('FillBlankCheckpoint', () => {
  it('puts the input inside the sentence and keeps Confirm disabled while empty', () => {
    const { input, confirm } = setup()
    expect(input.closest('p')).toHaveTextContent('Could I a single ticket, please?')
    expect(confirm).toBeDisabled()
  })

  it('keeps Confirm disabled for whitespace-only input, and Enter sends nothing', async () => {
    const user = userEvent.setup()
    const { input, confirm, onConfirm } = setup()
    await user.type(input, '    ')
    expect(confirm).toBeDisabled()
    await user.keyboard('{Enter}')
    expect(onConfirm).not.toHaveBeenCalled()
  })

  it('sends the trimmed text exactly once, even on a double click', async () => {
    const user = userEvent.setup()
    const { input, confirm, onConfirm } = setup()
    await user.type(input, '  have  ')
    expect(confirm).toBeEnabled()
    await user.dblClick(confirm)
    await user.keyboard('{Enter}')
    expect(onConfirm).toHaveBeenCalledTimes(1)
    expect(onConfirm).toHaveBeenCalledWith({ text: 'have' })
  })

  it('Enter in the gap confirms when the text is not empty', async () => {
    const user = userEvent.setup()
    const { input, onConfirm } = setup()
    await user.type(input, 'buy{Enter}')
    expect(onConfirm).toHaveBeenCalledWith({ text: 'buy' })
  })

  it('once locked, the input is read-only and Confirm stays disabled', () => {
    const { input, confirm } = setup(true)
    expect(input).toHaveAttribute('readonly')
    expect(confirm).toBeDisabled()
  })
})
