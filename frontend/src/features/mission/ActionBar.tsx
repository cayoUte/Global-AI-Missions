import { forwardRef } from 'react'

import { Button } from '../../components/Button'

type Props = {
  label: string
  onClick: () => void
  disabled?: boolean
  loading?: boolean
  loadingLabel?: string
}

/** Mobile: sticky full-width primary button. lg+: inline, right-aligned, with an Enter hint. */
export const ActionBar = forwardRef<HTMLButtonElement, Props>(function ActionBar(
  { label, onClick, disabled, loading, loadingLabel },
  ref,
) {
  return (
    <div className="sticky bottom-0 z-30 -mx-4 bg-ink-950/90 px-4 pt-3 pb-[max(1rem,env(safe-area-inset-bottom))] backdrop-blur lg:static lg:mx-0 lg:flex lg:items-center lg:justify-end lg:gap-3 lg:bg-transparent lg:p-0 lg:backdrop-blur-none">
      <kbd aria-hidden="true" className="hidden text-xs text-fog-400 lg:inline">
        Enter
      </kbd>
      <Button
        ref={ref}
        size="lg"
        className="w-full lg:w-auto lg:min-w-40"
        disabled={disabled}
        loading={loading}
        loadingLabel={loadingLabel}
        onClick={onClick}
        aria-keyshortcuts="Enter"
      >
        {label}
      </Button>
    </div>
  )
})
