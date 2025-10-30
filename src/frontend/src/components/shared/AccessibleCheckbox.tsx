import { forwardRef } from 'react'

interface AccessibleCheckboxProps {
  id: string
  label: string
  checked: boolean
  onChange: (event: React.ChangeEvent<HTMLInputElement>) => void
  disabled?: boolean
  className?: string
  help?: string
  'aria-describedby'?: string
}

/**
 * Composant checkbox accessible avec focus ring visible
 * Suit les standards WCAG 2.2 AA pour l'accessibilité
 */
export const AccessibleCheckbox = forwardRef<HTMLInputElement, AccessibleCheckboxProps>(
  ({ id, label, checked, onChange, disabled = false, className = '', help, 'aria-describedby': ariaDescribedBy, ...props }, ref) => {
    const helpId = help ? `${id}-help` : undefined
    const describedBy = [ariaDescribedBy, helpId].filter(Boolean).join(' ') || undefined

    return (
      <div className={`flex items-start gap-3 ${className}`}>
        <input
          ref={ref}
          type="checkbox"
          id={id}
          checked={checked}
          onChange={onChange}
          disabled={disabled}
          className="h-4 w-4 text-primary focus:ring-2 focus:ring-primary focus:ring-offset-2 border-border rounded disabled:opacity-50 disabled:cursor-not-allowed mt-0.5"
          aria-describedby={describedBy}
          {...props}
        />
        <div className="flex-1">
          <label
            htmlFor={id}
            className={`text-sm cursor-pointer ${disabled ? 'text-muted-foreground opacity-50' : 'text-foreground'}`}
          >
            {label}
          </label>
          {help && (
            <p id={helpId} className="text-xs text-muted-foreground mt-1">
              {help}
            </p>
          )}
        </div>
      </div>
    )
  }
)

AccessibleCheckbox.displayName = 'AccessibleCheckbox'

export default AccessibleCheckbox
