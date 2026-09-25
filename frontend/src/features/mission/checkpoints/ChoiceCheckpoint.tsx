import { useEffect, useRef, useState, type KeyboardEvent, type Ref } from 'react'

import type { OptionView } from '../../../api/types'
import { isTypingTarget, ownsEnter, useHotkeys } from '../../../lib/hotkeys'
import { ActionBar } from '../ActionBar'
import { StimulusView } from './StimulusView'
import { promptId, useConfirmOnce, type CheckpointProps } from './types'

/** multiple_choice, comprehension and vocabulary: stimulus → prompt → decision cards → Confirm. */
export function ChoiceCheckpoint({
  checkpoint,
  clockTime,
  locked,
  slow,
  onConfirm,
}: CheckpointProps) {
  const options = checkpoint.options ?? []
  const [selected, setSelected] = useState<string | null>(null)
  const confirm = useConfirmOnce(locked, onConfirm)
  const groupRef = useRef<HTMLDivElement>(null)

  // New node → focus the choice group (UI_SPEC §8 focus management).
  useEffect(() => {
    groupRef.current?.focus({ preventScroll: true })
  }, [])

  const tryConfirm = () => {
    if (selected) confirm({ option_id: selected })
  }

  useHotkeys((event) => {
    if (locked) return
    const digit = Number(event.key)
    if (
      Number.isInteger(digit) &&
      digit >= 1 &&
      digit <= options.length &&
      !isTypingTarget(event.target)
    ) {
      event.preventDefault()
      setSelected(options[digit - 1].id)
    } else if (event.key === 'Enter' && !ownsEnter(event.target)) {
      event.preventDefault()
      tryConfirm()
    }
  })

  const isVocabulary = checkpoint.type === 'vocabulary'
  const layout = isVocabulary
    ? options.every((o) => o.text.length <= 18)
      ? 'grid grid-cols-2 gap-3'
      : 'grid gap-3'
    : options.every((o) => o.text.length <= 28)
      ? 'grid gap-3 md:grid-cols-2'
      : 'grid gap-3'
  const sideBySide = checkpoint.type === 'comprehension' && checkpoint.stimulus !== null

  return (
    <div className="space-y-4">
      <div
        className={
          sideBySide ? 'space-y-4 lg:grid lg:grid-cols-2 lg:gap-6 lg:space-y-0' : 'space-y-4'
        }
      >
        {checkpoint.stimulus ? (
          <StimulusView stimulus={checkpoint.stimulus} clockTime={clockTime} large={isVocabulary} />
        ) : null}
        <div className="space-y-3">
          <p id={promptId(checkpoint.item_id)} className="text-lg font-bold">
            {checkpoint.prompt}
          </p>
          <ChoiceGroup
            ref={groupRef}
            labelledBy={promptId(checkpoint.item_id)}
            options={options}
            value={selected}
            onChange={setSelected}
            locked={locked}
            className={layout}
            centred={isVocabulary}
          />
        </div>
      </div>
      <ActionBar
        label="Confirm"
        onClick={tryConfirm}
        disabled={!selected || locked}
        loading={locked && slow}
        loadingLabel="One moment…"
      />
    </div>
  )
}

type GroupProps = {
  options: OptionView[]
  value: string | null
  onChange: (id: string) => void
  locked: boolean
  labelledBy: string
  className: string
  centred: boolean
  ref: Ref<HTMLDivElement>
}

/** role="radiogroup" with roving tabindex; arrows move and select; locked keeps the selection only. */
function ChoiceGroup({
  options,
  value,
  onChange,
  locked,
  labelledBy,
  className,
  centred,
  ref,
}: GroupProps) {
  const radios = useRef<(HTMLDivElement | null)[]>([])
  const focusIndex = Math.max(
    0,
    options.findIndex((o) => o.id === value),
  )

  const onKeyDown = (event: KeyboardEvent<HTMLDivElement>, index: number) => {
    if (locked) return
    const move = { ArrowDown: 1, ArrowRight: 1, ArrowUp: -1, ArrowLeft: -1 }[event.key]
    if (move) {
      event.preventDefault()
      const next = (index + move + options.length) % options.length
      onChange(options[next].id)
      radios.current[next]?.focus()
    } else if (event.key === ' ') {
      event.preventDefault()
      onChange(options[index].id)
    }
  }

  return (
    <div
      ref={ref}
      role="radiogroup"
      tabIndex={-1}
      aria-labelledby={labelledBy}
      aria-disabled={locked || undefined}
      className={`outline-none ${className}`}
    >
      {options.map((option, index) => {
        const checked = option.id === value
        return (
          <div
            key={option.id}
            ref={(el) => {
              radios.current[index] = el
            }}
            role="radio"
            aria-checked={checked}
            aria-disabled={locked || undefined}
            tabIndex={index === focusIndex ? 0 : -1}
            onClick={() => !locked && onChange(option.id)}
            onKeyDown={(event) => onKeyDown(event, index)}
            className={`flex min-h-14 w-full items-center gap-3 rounded-card border px-4 py-3 text-left text-base transition-[background-color,box-shadow,border-color] duration-(--motion-quick) md:text-lg ${
              centred ? 'justify-center text-center' : ''
            } ${checked ? 'border-amber-400 bg-amber-400/12 shadow-selected' : 'border-line-strong bg-ink-800/95'} ${
              locked ? 'cursor-default' : 'cursor-pointer'
            } ${!locked && !checked ? 'hover:bg-ink-700' : ''}`}
          >
            <span
              aria-hidden="true"
              className={`grid size-7 shrink-0 place-items-center rounded-full border font-board text-sm ${
                checked ? 'border-amber-400 bg-amber-400 text-ink-950' : 'border-line-strong'
              }`}
            >
              {index + 1}
            </span>
            <span className="min-w-0 break-words">{option.text}</span>
          </div>
        )
      })}
    </div>
  )
}
