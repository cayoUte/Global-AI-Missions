import type { ButtonHTMLAttributes, ReactNode } from 'react'
import { forwardRef } from 'react'

import { buttonClasses, type ButtonVariant } from './buttonClasses'

type Props = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: ButtonVariant
  size?: 'md' | 'lg'
  loading?: boolean
  loadingLabel?: string
  icon?: ReactNode
}

/** UI_SPEC §5 Button. Loading replaces the label with text (never a spinner alone). */
export const Button = forwardRef<HTMLButtonElement, Props>(function Button(
  {
    variant = 'primary',
    size = 'md',
    loading = false,
    loadingLabel,
    icon,
    disabled,
    className = '',
    children,
    type = 'button',
    ...rest
  },
  ref,
) {
  const inactive = disabled || loading
  return (
    <button
      ref={ref}
      type={type}
      disabled={inactive}
      aria-disabled={inactive || undefined}
      className={`${buttonClasses(variant, size, className)} disabled:cursor-not-allowed disabled:opacity-60`}
      {...rest}
    >
      {icon && !loading ? <span aria-hidden="true">{icon}</span> : null}
      {loading && loadingLabel ? loadingLabel : children}
    </button>
  )
})
