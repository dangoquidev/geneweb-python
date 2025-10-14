import { forwardRef, useState } from 'react'
import type { InputHTMLAttributes, TextareaHTMLAttributes, SelectHTMLAttributes } from 'react'
import { AlertCircle, CheckCircle, Eye, EyeOff } from 'lucide-react'

type ValidationState = 'valid' | 'invalid' | 'pending' | 'neutral'

interface BaseFieldProps {
  label: string
  id: string
  error?: string
  help?: string
  required?: boolean
  validationState?: ValidationState
}

/**
 * Input accessible conforme WCAG 2.2 AA
 */
interface AccessibleInputProps extends BaseFieldProps, Omit<InputHTMLAttributes<HTMLInputElement>, 'id'> {
  showPasswordToggle?: boolean
}

export const AccessibleInput = forwardRef<HTMLInputElement, AccessibleInputProps>(
  ({ 
    label, 
    id, 
    error, 
    help, 
    required, 
    type = 'text',
    validationState = 'neutral',
    showPasswordToggle = false,
    className = '',
    ...props 
  }, ref) => {
    const [showPassword, setShowPassword] = useState(false)
    const [focused, setFocused] = useState(false)

    const inputType = showPasswordToggle && type === 'password' 
      ? (showPassword ? 'text' : 'password')
      : type

    const helpId = help ? `${id}-help` : undefined
    const errorId = error ? `${id}-error` : undefined
    const describedBy = [helpId, errorId].filter(Boolean).join(' ')

    const inputClasses = [
      'w-full rounded-md border px-3 py-2 text-sm transition-colors',
      'focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2',
      'disabled:cursor-not-allowed disabled:opacity-50',
      validationState === 'invalid' || error 
        ? 'border-destructive bg-destructive/5 focus:border-destructive' 
        : 'border-input bg-background',
      className
    ].filter(Boolean).join(' ')

    return (
      <div className="space-y-2">
        <label 
          htmlFor={id}
          className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
        >
          {label}
          {required && (
            <span className="text-destructive ml-1" aria-label="obligatoire">*</span>
          )}
        </label>
        
        <div className="relative">
          <input
            ref={ref}
            type={inputType}
            id={id}
            className={inputClasses}
            aria-invalid={validationState === 'invalid' || Boolean(error)}
            aria-describedby={describedBy || undefined}
            aria-required={required}
            onFocus={(e) => {
              setFocused(true)
              props.onFocus?.(e)
            }}
            onBlur={(e) => {
              setFocused(false)
              props.onBlur?.(e)
            }}
            {...props}
          />
          
          {/* Indicateur visuel de validation */}
          {validationState !== 'neutral' && !focused && (
            <div className="absolute inset-y-0 right-3 flex items-center">
              {validationState === 'valid' && (
                <CheckCircle className="h-4 w-4 text-green-600" aria-hidden="true" />
              )}
              {(validationState === 'invalid' || error) && (
                <AlertCircle className="h-4 w-4 text-destructive" aria-hidden="true" />
              )}
            </div>
          )}
          
          {/* Toggle password visibility */}
          {showPasswordToggle && type === 'password' && (
            <button
              type="button"
              className="absolute inset-y-0 right-3 flex items-center text-muted-foreground hover:text-foreground focus:ring-2 focus:ring-ring focus:ring-offset-2 rounded-sm"
              onClick={() => setShowPassword(!showPassword)}
              aria-label={showPassword ? 'Masquer le mot de passe' : 'Afficher le mot de passe'}
              tabIndex={0}
            >
              {showPassword ? (
                <EyeOff className="h-4 w-4" aria-hidden="true" />
              ) : (
                <Eye className="h-4 w-4" aria-hidden="true" />
              )}
            </button>
          )}
        </div>
        
        {help && (
          <p id={helpId} className="text-xs text-muted-foreground">
            {help}
          </p>
        )}
        
        {error && (
          <p id={errorId} className="text-xs text-destructive flex items-center gap-1" role="alert">
            <AlertCircle className="h-3 w-3 flex-shrink-0" aria-hidden="true" />
            {error}
          </p>
        )}
      </div>
    )
  }
)

AccessibleInput.displayName = 'AccessibleInput'

/**
 * Textarea accessible
 */
interface AccessibleTextareaProps extends BaseFieldProps, Omit<TextareaHTMLAttributes<HTMLTextAreaElement>, 'id'> {
  maxLength?: number
  showCharCount?: boolean
}

export const AccessibleTextarea = forwardRef<HTMLTextAreaElement, AccessibleTextareaProps>(
  ({ 
    label, 
    id, 
    error, 
    help, 
    required, 
    validationState = 'neutral',
    maxLength,
    showCharCount = Boolean(maxLength),
    className = '',
    value,
    ...props 
  }, ref) => {
    const helpId = help ? `${id}-help` : undefined
    const errorId = error ? `${id}-error` : undefined
    const countId = showCharCount ? `${id}-count` : undefined
    const describedBy = [helpId, errorId, countId].filter(Boolean).join(' ')

    const currentLength = typeof value === 'string' ? value.length : 0
    
    const textareaClasses = [
      'w-full rounded-md border px-3 py-2 text-sm transition-colors min-h-[80px]',
      'focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2',
      'disabled:cursor-not-allowed disabled:opacity-50 resize-vertical',
      validationState === 'invalid' || error 
        ? 'border-destructive bg-destructive/5 focus:border-destructive' 
        : 'border-input bg-background',
      className
    ].filter(Boolean).join(' ')

    return (
      <div className="space-y-2">
        <label 
          htmlFor={id}
          className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
        >
          {label}
          {required && (
            <span className="text-destructive ml-1" aria-label="obligatoire">*</span>
          )}
        </label>
        
        <textarea
          ref={ref}
          id={id}
          className={textareaClasses}
          aria-invalid={validationState === 'invalid' || Boolean(error)}
          aria-describedby={describedBy || undefined}
          aria-required={required}
          maxLength={maxLength}
          value={value}
          {...props}
        />
        
        {showCharCount && maxLength && (
          <p 
            id={countId} 
            className="text-xs text-muted-foreground text-right"
            aria-live="polite"
          >
            {currentLength} / {maxLength} caractères
          </p>
        )}
        
        {help && (
          <p id={helpId} className="text-xs text-muted-foreground">
            {help}
          </p>
        )}
        
        {error && (
          <p id={errorId} className="text-xs text-destructive flex items-center gap-1" role="alert">
            <AlertCircle className="h-3 w-3 flex-shrink-0" aria-hidden="true" />
            {error}
          </p>
        )}
      </div>
    )
  }
)

AccessibleTextarea.displayName = 'AccessibleTextarea'

/**
 * Select accessible
 */
interface AccessibleSelectProps extends BaseFieldProps, Omit<SelectHTMLAttributes<HTMLSelectElement>, 'id'> {
  options: Array<{ value: string; label: string; disabled?: boolean }>
  placeholder?: string
}

export const AccessibleSelect = forwardRef<HTMLSelectElement, AccessibleSelectProps>(
  ({ 
    label, 
    id, 
    error, 
    help, 
    required, 
    validationState = 'neutral',
    options,
    placeholder,
    className = '',
    ...props 
  }, ref) => {
    const helpId = help ? `${id}-help` : undefined
    const errorId = error ? `${id}-error` : undefined
    const describedBy = [helpId, errorId].filter(Boolean).join(' ')

    const selectClasses = [
      'w-full rounded-md border px-3 py-2 text-sm transition-colors',
      'focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2',
      'disabled:cursor-not-allowed disabled:opacity-50',
      validationState === 'invalid' || error 
        ? 'border-destructive bg-destructive/5 focus:border-destructive' 
        : 'border-input bg-background',
      className
    ].filter(Boolean).join(' ')

    return (
      <div className="space-y-2">
        <label 
          htmlFor={id}
          className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
        >
          {label}
          {required && (
            <span className="text-destructive ml-1" aria-label="obligatoire">*</span>
          )}
        </label>
        
        <select
          ref={ref}
          id={id}
          className={selectClasses}
          aria-invalid={validationState === 'invalid' || Boolean(error)}
          aria-describedby={describedBy || undefined}
          aria-required={required}
          {...props}
        >
          {placeholder && (
            <option value="" disabled>
              {placeholder}
            </option>
          )}
          {options.map((option) => (
            <option 
              key={option.value} 
              value={option.value}
              disabled={option.disabled}
            >
              {option.label}
            </option>
          ))}
        </select>
        
        {help && (
          <p id={helpId} className="text-xs text-muted-foreground">
            {help}
          </p>
        )}
        
        {error && (
          <p id={errorId} className="text-xs text-destructive flex items-center gap-1" role="alert">
            <AlertCircle className="h-3 w-3 flex-shrink-0" aria-hidden="true" />
            {error}
          </p>
        )}
      </div>
    )
  }
)

AccessibleSelect.displayName = 'AccessibleSelect'

/**
 * Fieldset pour grouper des champs liés
 */
interface FieldsetProps {
  legend: string
  children: React.ReactNode
  className?: string
}

export function Fieldset({ legend, children, className = '' }: FieldsetProps) {
  return (
    <fieldset className={`border border-border rounded-lg p-4 ${className}`}>
      <legend className="px-2 text-sm font-medium text-foreground">
        {legend}
      </legend>
      <div className="space-y-4 mt-4">
        {children}
      </div>
    </fieldset>
  )
}