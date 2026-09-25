import { useEffect, useRef } from 'react'

/** True when the key event comes from a place that owns typing (inputs, textareas, selects). */
export function isTypingTarget(target: EventTarget | null): boolean {
  if (!(target instanceof HTMLElement)) return false
  const tag = target.tagName
  return tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT' || target.isContentEditable
}

/** True when Enter on this target already has a native meaning (buttons, links, inputs). */
export function ownsEnter(target: EventTarget | null): boolean {
  if (!(target instanceof HTMLElement)) return false
  return isTypingTarget(target) || target.closest('button, a[href], summary') !== null
}

/**
 * A window keydown listener for the Mission Player shortcuts (UI_SPEC §8). Ignores events with a
 * modifier key or while an IME is composing. The handler always sees the latest props.
 */
export function useHotkeys(handler: (event: KeyboardEvent) => void, enabled = true): void {
  const latest = useRef(handler)
  useEffect(() => {
    latest.current = handler
  })
  useEffect(() => {
    if (!enabled) return
    const onKeyDown = (event: KeyboardEvent) => {
      if (
        event.defaultPrevented ||
        event.isComposing ||
        event.ctrlKey ||
        event.metaKey ||
        event.altKey
      )
        return
      latest.current(event)
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [enabled])
}
