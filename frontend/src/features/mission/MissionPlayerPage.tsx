import { useQueryClient } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import { useCallback, useEffect, useMemo, useReducer, useRef, useState } from 'react'
import { Link, useNavigate, useParams, useSearchParams } from 'react-router'

import { api } from '../../api/client'
import { isApiError } from '../../api/http'
import { PROGRESS_KEY, WORLD_KEY, attemptKey, reportKey } from '../../api/queryKeys'
import type { StateView } from '../../api/types'
import { Button } from '../../components/Button'
import { buttonClasses } from '../../components/buttonClasses'
import { InlineNotice } from '../../components/InlineNotice'
import { MayaBubble, MayaPortrait, type BubbleKind } from '../../components/Maya'
import { ownsEnter, useHotkeys } from '../../lib/hotkeys'
import { EASE } from '../../lib/motion'
import { useOnline } from '../../lib/useOnline'
import { ActionBar } from './ActionBar'
import { ChoiceCheckpoint } from './checkpoints/ChoiceCheckpoint'
import { FillBlankCheckpoint } from './checkpoints/FillBlankCheckpoint'
import type { CheckpointAnswer } from './checkpoints/types'
import { EndingView } from './EndingView'
import { playerPath, reportPath } from './navigation'
import {
  initialPlayerState,
  isCheckpointLocked,
  playerReducer,
  type PendingRequest,
  type PlayerState,
} from './playerReducer'
import { PlayerFrame, SIGNAL_DROPPED } from './PlayerFrame'
import { DialogueBox, SceneKicker } from './SceneParts'

/** /missions/:missionId/play?attempt=… — without an attempt id, start (or resume) first. */
export function MissionPlayerPage() {
  const { missionId = '' } = useParams()
  const [params] = useSearchParams()
  const attemptId = params.get('attempt')
  if (!attemptId) return <StartThenPlay missionId={missionId} />
  return <MissionPlayer key={attemptId} attemptId={attemptId} />
}

function StartThenPlay({ missionId }: { missionId: string }) {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [failed, setFailed] = useState(false)
  const started = useRef(false)

  const start = useCallback(() => {
    setFailed(false)
    api
      .startMission(missionId)
      .then((state) => {
        queryClient.setQueryData(attemptKey(state.attempt_id), state)
        navigate(playerPath(state.mission_id, state.attempt_id), { replace: true })
      })
      .catch(() => setFailed(true))
  }, [missionId, navigate, queryClient])

  useEffect(() => {
    if (started.current) return
    started.current = true
    start()
  }, [start])

  return (
    <PlayerFrame backdrop="concourse_night" clock={null} title="">
      <div className="space-y-4">
        {failed ? (
          <InlineNotice
            tone="problem"
            message={SIGNAL_DROPPED}
            action={
              <Button variant="secondary" onClick={start}>
                Try again
              </Button>
            }
          />
        ) : (
          <MayaBubble lines={[]} kind="waiting" />
        )}
      </div>
    </PlayerFrame>
  )
}

function MissionPlayer({ attemptId }: { attemptId: string }) {
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const online = useOnline()
  const [state, dispatch] = useReducer(playerReducer, attemptId, (id) =>
    initialPlayerState(queryClient.getQueryData<StateView>(attemptKey(id)) ?? null),
  )
  const slow = useSlow(
    state.phase === 'sending' || state.phase === 'submitting' || state.phase === 'loading',
  )

  // Run each accepted request exactly once (the reducer refuses a second one while busy).
  const ran = useRef<PendingRequest | null>(null)
  useEffect(() => {
    const request = state.pending
    const busy =
      state.phase === 'sending' || state.phase === 'submitting' || state.phase === 'loading'
    if (!request || !busy || state.problem || ran.current === request) return
    ran.current = request
    void run(request)

    async function run(req: PendingRequest) {
      try {
        if (req.kind === 'load') dispatch({ type: 'loaded', view: await api.attempt(attemptId) })
        else if (req.kind === 'advance')
          dispatch({ type: 'advanced', view: await api.advance(attemptId, req.body) })
        else if (req.kind === 'answer')
          dispatch({ type: 'answered', response: await api.answer(attemptId, req.body) })
        else {
          const report = await api.submit(attemptId)
          queryClient.setQueryData(reportKey(attemptId), report)
          void queryClient.invalidateQueries({ queryKey: WORLD_KEY })
          void queryClient.invalidateQueries({ queryKey: PROGRESS_KEY })
          dispatch({ type: 'submitted' })
        }
      } catch (error) {
        if (!isApiError(error))
          return dispatch({ type: 'failed', problem: req.kind === 'submit' ? 'submit' : 'network' })
        const serverState = error.details?.state as StateView | undefined
        if (error.status === 409 && serverState)
          return dispatch({ type: 'resync', view: serverState }) // silent (PRODUCT §5.3)
        if (error.status === 404) return dispatch({ type: 'not_found' })
        if (error.status === 401) return // the session watcher routes to Check-in
        if (error.status === 422 && req.kind === 'answer')
          return dispatch({ type: 'failed', problem: 'invalid_answer' })
        dispatch({ type: 'failed', problem: req.kind === 'submit' ? 'submit' : 'network' })
      }
    }
  }, [state.pending, state.phase, state.problem, attemptId, queryClient])

  // Keep the cached StateView current (Pause → Continue your mission renders it immediately).
  useEffect(() => {
    if (state.view) queryClient.setQueryData(attemptKey(attemptId), state.view)
  }, [state.view, attemptId, queryClient])

  // Submitted → the Mission Report.
  useEffect(() => {
    if (state.phase === 'report') navigate(reportPath(attemptId), { replace: true })
  }, [state.phase, attemptId, navigate])

  // Back online after a failure → re-read the server's truth.
  useEffect(() => {
    if (online && state.problem === 'network' && state.pending?.kind !== 'submit')
      dispatch({ type: 'request', request: { kind: 'load' } })
  }, [online]) // eslint-disable-line react-hooks/exhaustive-deps -- only on reconnection

  const retry = () => {
    if (state.pending) dispatch({ type: 'request', request: { ...state.pending } })
    else dispatch({ type: 'request', request: { kind: 'load' } })
  }

  const view = state.view

  if (state.phase === 'not_found') {
    return (
      <PlayerFrame
        backdrop={view?.node.scene.backdrop ?? 'concourse_night'}
        clock={view?.clock ?? null}
        title={view?.mission_title ?? ''}
      >
        <InlineNotice
          tone="problem"
          message="We couldn't find this mission run."
          action={
            <Link to="/world" className={buttonClasses('secondary')}>
              Back to the English World
            </Link>
          }
        />
      </PlayerFrame>
    )
  }

  if (!view) {
    return (
      <PlayerFrame backdrop="concourse_night" clock={null} title="">
        <div className="flex items-start gap-3" aria-busy="true">
          <MayaPortrait mood="curious" size={56} />
          <MayaBubble lines={[]} kind="waiting" className="flex-1" />
        </div>
        {state.problem ? <RetryNotice onRetry={retry} className="mt-4" /> : null}
      </PlayerFrame>
    )
  }

  if (state.phase === 'ending' || state.phase === 'submitting' || state.phase === 'report') {
    return (
      <EndingView
        view={view}
        submitting={state.phase === 'submitting' || state.phase === 'report'}
        failed={state.problem === 'submit' || state.problem === 'network'}
        onSubmit={() => dispatch({ type: 'request', request: { kind: 'submit' } })}
      />
    )
  }

  return <SceneScreen state={state} view={view} slow={slow} dispatch={dispatch} onRetry={retry} />
}

type SceneScreenProps = {
  state: PlayerState
  view: StateView
  slow: boolean
  dispatch: (action: { type: 'request'; request: PendingRequest }) => void
  onRetry: () => void
}

function SceneScreen({ state, view, slow, dispatch, onRetry }: SceneScreenProps) {
  const node = view.node
  const checkpoint = node.checkpoint
  const locked = isCheckpointLocked(state)
  const busy = state.phase === 'sending'
  const kickerRef = useRef<HTMLParagraphElement>(null)

  const onConfirm = (answer: CheckpointAnswer) =>
    dispatch({
      type: 'request',
      request: { kind: 'answer', body: { node_id: node.id, ...answer } },
    })
  const onContinue = () =>
    dispatch({ type: 'request', request: { kind: 'advance', body: { node_id: node.id } } })

  // New node → scroll the column back to the scene's top.
  useEffect(() => {
    kickerRef.current?.scrollIntoView?.({ block: 'start' })
  }, [node.id])

  // Maya's bubble for this moment (UI_SPEC §9.3.3).
  let bubbleKind: BubbleKind =
    view.maya.decision === 'rescue' ? 'rescue' : view.maya.decision === 'hint' ? 'hint' : 'line'
  let bubbleLines = [view.maya.line ?? '']
  if (state.phase === 'reaction' && state.reaction) {
    bubbleKind = view.maya.decision === 'rescue' ? 'rescue' : 'reaction'
    bubbleLines =
      view.maya.line && view.maya.line !== state.reaction
        ? [state.reaction, view.maya.line]
        : [state.reaction]
  }
  if (busy && slow) bubbleKind = 'waiting'
  const rescue = view.maya.decision === 'rescue'

  const announcement = [
    state.phase === 'reaction' && state.reaction ? `Maya: ${state.reaction}` : '',
    `${node.scene.location}. ${view.clock.label}.`,
    ...node.scene.lines.map((l) => (l.speaker === 'narrator' ? l.text : `${l.speaker}: ${l.text}`)),
    view.maya.line && view.maya.line !== state.reaction ? `Maya: ${view.maya.line}` : '',
  ]
    .filter(Boolean)
    .join(' ')

  return (
    <PlayerFrame backdrop={node.scene.backdrop} clock={view.clock} title={view.mission_title} wide>
      <h1 className="sr-only">
        {view.mission_title} — {node.scene.location}
      </h1>
      <div role="log" aria-live="polite" aria-relevant="additions" className="sr-only">
        <p key={`${node.id}-${state.reaction ?? ''}`}>{announcement}</p>
      </div>
      {/* Keyed by node: the new scene fades in (250 ms) while the backdrop crossfades behind it.
          No exit animation on purpose: stale content (and its buttons) never lingers on screen. */}
      <motion.div
        key={node.id}
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0, transition: { duration: 0.25, ease: EASE.enter } }}
        aria-busy={busy || undefined}
        className="grid gap-4 lg:grid-cols-[15rem_1fr] lg:gap-x-8"
      >
        <div className="space-y-3 lg:col-start-2 lg:row-start-1">
          <SceneKicker ref={kickerRef} location={node.scene.location} />
          <DialogueBox lines={node.scene.lines} />
        </div>

        <div className="flex items-start gap-3 lg:sticky lg:top-20 lg:col-start-1 lg:row-span-2 lg:row-start-1 lg:flex-col lg:items-center lg:self-start">
          <MayaPortrait mood={view.maya.mood} size={rescue ? 72 : 56} className="md:hidden" />
          <MayaPortrait
            mood={view.maya.mood}
            size={rescue ? 96 : 72}
            className="hidden md:block lg:hidden"
          />
          <MayaPortrait mood={view.maya.mood} size={128} className="hidden lg:block" />
          <MayaBubble
            key={`${node.id}-${bubbleKind}`}
            lines={bubbleLines}
            kind={bubbleKind}
            className="min-w-0 flex-1 lg:w-full"
          />
        </div>

        <div className="space-y-4 lg:col-start-2 lg:row-start-2">
          {state.problem === 'network' ? <RetryNotice onRetry={onRetry} /> : null}
          {state.problem === 'invalid_answer' ? (
            <InlineNotice tone="problem" message="Type the missing words." />
          ) : null}
          {checkpoint ? (
            checkpoint.type === 'fill_blank' ? (
              <FillBlankCheckpoint
                checkpoint={checkpoint}
                clockTime={view.clock.time}
                locked={locked}
                slow={slow}
                onConfirm={onConfirm}
              />
            ) : (
              <ChoiceCheckpoint
                checkpoint={checkpoint}
                clockTime={view.clock.time}
                locked={locked}
                slow={slow}
                onConfirm={onConfirm}
              />
            )
          ) : (
            <ContinueAction
              key={node.id}
              disabled={busy || state.problem === 'network'}
              slow={busy && slow}
              onContinue={onContinue}
            />
          )}
        </div>
      </motion.div>
    </PlayerFrame>
  )
}

function ContinueAction({
  disabled,
  slow,
  onContinue,
}: {
  disabled: boolean
  slow: boolean
  onContinue: () => void
}) {
  const ref = useRef<HTMLButtonElement>(null)
  useEffect(() => {
    ref.current?.focus({ preventScroll: true })
  }, [])
  useHotkeys((event) => {
    if (event.key === 'Enter' && !ownsEnter(event.target) && !disabled) {
      event.preventDefault()
      onContinue()
    }
  })
  return (
    <ActionBar
      ref={ref}
      label="Continue"
      onClick={onContinue}
      disabled={disabled}
      loading={slow}
      loadingLabel="One moment…"
    />
  )
}

function RetryNotice({ onRetry, className = '' }: { onRetry: () => void; className?: string }) {
  return (
    <InlineNotice
      tone="problem"
      className={className}
      message={SIGNAL_DROPPED}
      action={
        <Button variant="secondary" onClick={onRetry}>
          Try again
        </Button>
      }
    />
  )
}

/** True once `active` has lasted more than one second ("One moment…" rule). */
function useSlow(active: boolean): boolean {
  // A fresh token per busy stretch; "slow" means the timer fired for the current token.
  const token = useMemo(() => (active ? {} : null), [active])
  const [slowToken, setSlowToken] = useState<object | null>(null)
  useEffect(() => {
    if (!token) return
    const timer = setTimeout(() => setSlowToken(token), 1000)
    return () => clearTimeout(timer)
  }, [token])
  return token !== null && slowToken === token
}
