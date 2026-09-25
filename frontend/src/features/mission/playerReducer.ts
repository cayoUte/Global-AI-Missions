// The Mission Player state machine. It only renders the server's StateView: it never knows the
// next node, the clock or correctness. Every request goes through `request`, which the reducer
// refuses while another one is in flight (double-submit guard); the page runs the request in an
// effect keyed on `pending`, so one accepted `request` = exactly one network call.
//
//   loading → scene | checkpoint | ending
//   scene/consequence/reaction --Continue--> sending → scene | checkpoint | consequence | ending
//   checkpoint --Confirm--> sending → reaction (Maya's reaction + the consequence scene)
//   ending --Submit mission--> submitting → report
//   any 409 → the server's state (resync) · network failure → same phase + problem + Try again
import type { AdvanceRequest, AnswerRequest, AnswerResponse, StateView } from '../../api/types'

export type Phase =
  | 'loading'
  | 'scene'
  | 'checkpoint'
  | 'sending'
  | 'reaction'
  | 'consequence'
  | 'ending'
  | 'submitting'
  | 'report'
  | 'not_found'

export type PendingRequest =
  | { kind: 'load' }
  | { kind: 'advance'; body: AdvanceRequest }
  | { kind: 'answer'; body: AnswerRequest }
  | { kind: 'submit' }

/** network: Try again resends the same request · invalid_answer: 422, the checkpoint unlocks. */
export type Problem = 'network' | 'invalid_answer' | 'submit' | null

export type PlayerState = {
  phase: Phase
  view: StateView | null
  /** Maya's reaction from the answer response (lost on reload: accepted, PD-032). */
  reaction: string | null
  /** The request in flight, or the failed one kept for Try again. */
  pending: PendingRequest | null
  problem: Problem
}

export type PlayerAction =
  | { type: 'request'; request: PendingRequest }
  | { type: 'loaded'; view: StateView }
  | { type: 'advanced'; view: StateView }
  | { type: 'answered'; response: AnswerResponse }
  | { type: 'resync'; view: StateView }
  | { type: 'submitted' }
  | { type: 'failed'; problem: Exclude<Problem, null> }
  | { type: 'not_found' }

/** The phase that renders a StateView (the server decides everything; this only maps it). */
export function phaseFor(view: StateView, reaction: string | null = null): Phase {
  if (view.status === 'submitted') return 'report'
  if (view.status === 'completed' || view.node.kind === 'ending') return 'ending'
  if (view.node.kind === 'checkpoint') return 'checkpoint'
  if (reaction) return 'reaction'
  return view.node.kind === 'consequence' ? 'consequence' : 'scene'
}

export function initialPlayerState(view: StateView | null): PlayerState {
  if (view) return { phase: phaseFor(view), view, reaction: null, pending: null, problem: null }
  return { phase: 'loading', view: null, reaction: null, pending: { kind: 'load' }, problem: null }
}

const BUSY: Phase[] = ['sending', 'submitting']

export function playerReducer(state: PlayerState, action: PlayerAction): PlayerState {
  switch (action.type) {
    case 'request': {
      if (BUSY.includes(state.phase)) return state // a second Confirm/Continue/Submit is ignored
      if (state.phase === 'loading' && state.pending && !state.problem) return state
      const phase: Phase =
        action.request.kind === 'load'
          ? 'loading'
          : action.request.kind === 'submit'
            ? 'submitting'
            : 'sending'
      return { ...state, phase, pending: action.request, problem: null }
    }
    case 'loaded':
    case 'advanced':
    case 'resync':
      return {
        phase: phaseFor(action.view),
        view: action.view,
        reaction: null,
        pending: null,
        problem: null,
      }
    case 'answered': {
      const reaction = action.response.maya_line
      return {
        phase: phaseFor(action.response.state, reaction),
        view: action.response.state,
        reaction,
        pending: null,
        problem: null,
      }
    }
    case 'submitted':
      return { ...state, phase: 'report', pending: null, problem: null }
    case 'failed': {
      const back: Phase = state.view ? phaseFor(state.view, state.reaction) : 'loading'
      // A 422 on an answer never locks the checkpoint: drop the request so the student can edit.
      const pending = action.problem === 'invalid_answer' ? null : state.pending
      return { ...state, phase: back, pending, problem: action.problem }
    }
    case 'not_found':
      return { ...state, phase: 'not_found', pending: null, problem: null }
  }
}

/** The checkpoint stays locked from Confirm until the server answers (also while Try again is offered). */
export function isCheckpointLocked(state: PlayerState): boolean {
  return state.pending?.kind === 'answer'
}
