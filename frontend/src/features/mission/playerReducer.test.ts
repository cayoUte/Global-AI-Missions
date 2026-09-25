import { describe, expect, it } from 'vitest'

import type { StateView } from '../../api/types'
import {
  initialPlayerState,
  isCheckpointLocked,
  phaseFor,
  playerReducer,
  type PlayerState,
} from './playerReducer'

function view(
  kind: StateView['node']['kind'],
  overrides: Partial<StateView> = {},
  id: string = kind,
): StateView {
  return {
    attempt_id: 'a1',
    mission_id: 'the-last-train',
    mission_title: 'The Last Train',
    status: kind === 'ending' ? 'completed' : 'in_progress',
    clock: {
      time: '21:47',
      minutes_left: 18,
      train_departed: false,
      label: '21:47 · 18 min to departure',
    },
    node: {
      id,
      kind,
      scene: { location: 'Concourse', backdrop: 'concourse_night', lines: [] },
      checkpoint:
        kind === 'checkpoint'
          ? {
              item_id: 'q1',
              type: 'multiple_choice',
              prompt: 'Which?',
              stimulus: null,
              options: [{ id: 'a', text: 'A' }],
            }
          : null,
      ending: kind === 'ending' ? { key: 'made_it', title: 'Made It' } : null,
    },
    maya: { mood: 'curious', decision: 'quiet', line: null },
    ...overrides,
  }
}

const answer = { kind: 'answer' as const, body: { node_id: 'checkpoint', option_id: 'a' } }

describe('phaseFor', () => {
  it('maps the server state to a phase without judging anything', () => {
    expect(phaseFor(view('narrative'))).toBe('scene')
    expect(phaseFor(view('checkpoint'))).toBe('checkpoint')
    expect(phaseFor(view('consequence'))).toBe('consequence')
    expect(phaseFor(view('consequence'), 'Nice.')).toBe('reaction')
    expect(phaseFor(view('ending'))).toBe('ending')
    expect(phaseFor(view('ending', { status: 'submitted' }))).toBe('report')
  })
})

describe('playerReducer', () => {
  it('starts loading without a cached state and renders one when it has it', () => {
    expect(initialPlayerState(null)).toMatchObject({ phase: 'loading', pending: { kind: 'load' } })
    expect(initialPlayerState(view('checkpoint')).phase).toBe('checkpoint')
  })

  it('locks the checkpoint on Confirm and ignores a second Confirm while sending', () => {
    const start = initialPlayerState(view('checkpoint'))
    const sending = playerReducer(start, { type: 'request', request: answer })
    expect(sending.phase).toBe('sending')
    expect(isCheckpointLocked(sending)).toBe(true)
    const again = playerReducer(sending, { type: 'request', request: { ...answer } })
    expect(again).toBe(sending) // same object: the page never runs a second request
  })

  it("shows Maya's reaction with the consequence scene after an answer", () => {
    const sending = playerReducer(initialPlayerState(view('checkpoint')), {
      type: 'request',
      request: answer,
    })
    const next = playerReducer(sending, {
      type: 'answered',
      response: { maya_line: 'Good ear.', state: view('consequence') },
    })
    expect(next).toMatchObject({
      phase: 'reaction',
      reaction: 'Good ear.',
      pending: null,
      problem: null,
    })
    expect(next.view?.node.kind).toBe('consequence')
  })

  it('keeps the failed request for Try again and stays on the same node (locked)', () => {
    const sending = playerReducer(initialPlayerState(view('checkpoint')), {
      type: 'request',
      request: answer,
    })
    const failed = playerReducer(sending, { type: 'failed', problem: 'network' })
    expect(failed).toMatchObject({ phase: 'checkpoint', problem: 'network', pending: answer })
    expect(isCheckpointLocked(failed)).toBe(true)
    const retry = playerReducer(failed, { type: 'request', request: { ...answer } })
    expect(retry).toMatchObject({ phase: 'sending', problem: null })
  })

  it('unlocks the checkpoint on a 422 (a rejected answer never locks)', () => {
    const sending = playerReducer(initialPlayerState(view('checkpoint')), {
      type: 'request',
      request: answer,
    })
    const rejected = playerReducer(sending, { type: 'failed', problem: 'invalid_answer' })
    expect(rejected.phase).toBe('checkpoint')
    expect(isCheckpointLocked(rejected)).toBe(false)
  })

  it("renders the server's truth on a 409 resync, silently", () => {
    const sending = playerReducer(initialPlayerState(view('checkpoint')), {
      type: 'request',
      request: answer,
    })
    const synced = playerReducer(sending, {
      type: 'resync',
      view: view('consequence', {}, 'c1_ok'),
    })
    expect(synced).toMatchObject({
      phase: 'consequence',
      problem: null,
      pending: null,
      reaction: null,
    })
    expect(synced.view?.node.id).toBe('c1_ok')
  })

  it('goes ending → submitting → report, and a failed submit returns to the Ending', () => {
    const ending: PlayerState = initialPlayerState(view('ending'))
    expect(ending.phase).toBe('ending')
    const submitting = playerReducer(ending, { type: 'request', request: { kind: 'submit' } })
    expect(submitting.phase).toBe('submitting')
    expect(playerReducer(submitting, { type: 'request', request: { kind: 'submit' } })).toBe(
      submitting,
    )
    expect(playerReducer(submitting, { type: 'failed', problem: 'submit' })).toMatchObject({
      phase: 'ending',
      problem: 'submit',
    })
    expect(playerReducer(submitting, { type: 'submitted' }).phase).toBe('report')
  })

  it('shows the not-found state for a missing or foreign attempt', () => {
    const loading = initialPlayerState(null)
    expect(playerReducer(loading, { type: 'not_found' }).phase).toBe('not_found')
  })
})
