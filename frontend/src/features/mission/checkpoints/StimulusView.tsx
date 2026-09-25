import type { Stimulus } from '../../../api/types'
import { speakerLabel } from '../speakers'
import { Announcement } from './Announcement'

type Props = { stimulus: Stimulus; clockTime: string; large?: boolean }

/** One renderer per stimulus.kind (F-09), so every item type × stimulus combination is covered. */
export function StimulusView({ stimulus, clockTime, large = false }: Props) {
  switch (stimulus.kind) {
    case 'audio':
      return (
        <Announcement
          speaker={stimulus.speaker}
          audioScript={stimulus.audio_script}
          rate={stimulus.rate}
        />
      )
    case 'message':
      return <PhoneMessage speaker={stimulus.speaker} text={stimulus.text} clockTime={clockTime} />
    case 'notice':
      return <NoticePaper speaker={stimulus.speaker} text={stimulus.text} />
    case 'timetable':
      return <TimetableBoard text={stimulus.text} />
    case 'sign':
      return <SignPlate speaker={stimulus.speaker} text={stimulus.text} large={large} />
    case 'dialogue':
      return <SpeechBubble speaker={stimulus.speaker} text={stimulus.text} />
  }
}

export function SpeechBubble({ speaker, text }: { speaker: string | null; text: string }) {
  const { label, tone } = speakerLabel(speaker ?? 'narrator')
  return (
    <div className="rounded-card bg-ink-800/95 p-4 shadow-raised">
      {label ? (
        <p className={`text-xs font-bold tracking-wide uppercase ${tone}`}>{label}</p>
      ) : null}
      <p className="text-base whitespace-pre-line md:text-lg">{text}</p>
    </div>
  )
}

function PhoneMessage({
  speaker,
  text,
  clockTime,
}: {
  speaker: string | null
  text: string
  clockTime: string
}) {
  return (
    <div className="mx-auto w-full max-w-[22rem] rounded-sheet border border-ink-600 bg-ink-950 p-3">
      <div className="mb-2 flex items-center justify-between gap-2">
        <p className="text-sm font-bold text-fog-200">{speaker ?? 'Message'}</p>
        <span aria-hidden="true" className="font-board text-xs text-fog-400">
          {clockTime}
        </span>
      </div>
      <p className="rounded-card rounded-tl-board bg-phone-700 p-3 text-base whitespace-pre-line">
        {text}
      </p>
    </div>
  )
}

function NoticePaper({ speaker, text }: { speaker: string | null; text: string }) {
  return (
    <div className="surface-paper rounded-card border-t-4 border-paper-300 bg-paper-50 p-4 text-paper-ink shadow-raised md:rotate-[-0.6deg]">
      {speaker ? <p className="text-sm font-bold tracking-wide uppercase">{speaker}</p> : null}
      <p className="mt-1 text-base whitespace-pre-line">{text}</p>
    </div>
  )
}

function TimetableBoard({ text }: { text: string }) {
  const [header, ...rows] = text.split('\n')
  return (
    <div
      tabIndex={0}
      aria-label="Timetable"
      className="overflow-x-auto rounded-board bg-ink-950 p-3 font-board text-sm text-amber-400 shadow-board md:text-base"
    >
      <p className="whitespace-pre text-fog-200">{header}</p>
      {rows.map((row, index) => (
        <p key={index} className="whitespace-pre">
          {row}
        </p>
      ))}
    </div>
  )
}

function SignPlate({
  speaker,
  text,
  large,
}: {
  speaker: string | null
  text: string
  large: boolean
}) {
  return (
    <figure className="space-y-1">
      <div
        className={`rounded-board border-2 border-fog-50/80 bg-sign-700 px-4 py-3 text-center font-bold tracking-wide whitespace-pre-line text-fog-50 ${
          large ? 'text-2xl' : 'text-xl'
        }`}
      >
        {text}
      </div>
      {speaker ? (
        <figcaption className="text-center text-xs text-fog-400">{speaker}</figcaption>
      ) : null}
    </figure>
  )
}
