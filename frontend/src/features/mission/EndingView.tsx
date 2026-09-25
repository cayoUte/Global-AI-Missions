import { useEffect, useRef } from 'react'

import type { StateView } from '../../api/types'
import { Button } from '../../components/Button'
import { DepartureBoard } from '../../components/DepartureBoard'
import { InlineNotice } from '../../components/InlineNotice'
import { MayaBubble, MayaPortrait } from '../../components/Maya'
import { PlayerFrame } from './PlayerFrame'
import { DialogueBox } from './SceneParts'

type Props = {
  view: StateView
  submitting: boolean
  failed: boolean
  onSubmit: () => void
}

/**
 * The Ending (UI_SPEC §9.4): title, final clock, closing scene, Maya's closing line and
 * Submit mission. No score, level or count. Also shown after a reload or from "Waiting to submit".
 */
export function EndingView({ view, submitting, failed, onSubmit }: Props) {
  const title = view.node.ending?.title ?? view.node.scene.location
  const headingRef = useRef<HTMLHeadingElement>(null)
  useEffect(() => {
    headingRef.current?.focus({ preventScroll: true })
  }, [])

  return (
    <PlayerFrame backdrop={view.node.scene.backdrop} title={view.mission_title}>
      <div className="mx-auto max-w-reading space-y-5 pt-[6vh]">
        <div className="space-y-2">
          <p className="inline-block rounded-full bg-ink-950/70 px-3 py-1 text-xs font-bold tracking-board text-fog-200 uppercase">
            The end of the night
          </p>
          <h1
            ref={headingRef}
            tabIndex={-1}
            className="font-display text-3xl font-semibold outline-none"
          >
            <span className="rounded-card bg-ink-950/70 px-2 box-decoration-clone">{title}</span>
          </h1>
        </div>
        <DepartureBoard clock={view.clock} className="inline-block" />
        <DialogueBox lines={view.node.scene.lines} />
        <div className="flex items-start gap-3">
          <MayaPortrait
            mood={submitting ? 'curious' : view.maya.mood}
            size={96}
            className={submitting ? 'animate-maya-idle' : ''}
          />
          <MayaBubble lines={[view.maya.line ?? '']} kind="line" className="min-w-0 flex-1" />
        </div>

        {failed && !submitting ? (
          <InlineNotice
            tone="problem"
            message="Your Diary is safe, but we couldn't finish the report. Try again."
            action={
              <Button variant="secondary" onClick={onSubmit}>
                Try again
              </Button>
            }
          />
        ) : null}

        <div className="space-y-2" aria-busy={submitting || undefined}>
          <Button
            size="lg"
            className="w-full sm:w-auto"
            loading={submitting}
            loadingLabel="Maya is reading your Diary…"
            onClick={onSubmit}
          >
            Submit mission
          </Button>
          <p className="text-sm text-fog-200">
            Maya will read your Diary and prepare your Mission Report.
          </p>
          <p role="status" className="sr-only">
            {submitting ? 'Maya is reading your Diary…' : ''}
          </p>
        </div>
      </div>
    </PlayerFrame>
  )
}
