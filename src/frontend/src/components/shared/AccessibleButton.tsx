import { forwardRef } from 'react'
import type { ButtonHTMLAttributes } from 'react'
import { Loader2 } from 'lucide-react'

type ButtonVariant = 'primary' | 'secondary' | 'destructive' | 'outline' | 'ghost'
type ButtonSize = 'sm' | 'md' | 'lg'

interface AccessibleButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant
  size?: ButtonSize
  loading?: boolean
  loadingText?: string
  icon?: React.ComponentType<{ className?: string }>
  iconPosition?: 'left' | 'right'
  fullWidth?: boolean
  children: React.ReactNode
}

/**
 * Bouton accessible conforme WCAG 2.2 AA
 * - Focus ring visible
 * - États loading, disabled gérés
 * - Taille de clic minimum 44x44px
 * - Labels accessibles
 */
export const AccessibleButton = forwardRef<HTMLButtonElement, AccessibleButtonProps>(
  ({
    variant = 'primary',
    size = 'md',
    loading = false,
    loadingText,
    icon: Icon,
    iconPosition = 'left',
    fullWidth = false,
    className = '',
    disabled,
    children,
    ...props
  }, ref) => {
    
    const baseClasses = 'inline-flex items-center justify-center font-medium rounded-md transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed'
    
    const variantClasses = {
      primary: 'bg-primary text-primary-foreground hover:bg-primary/90',
      secondary: 'bg-secondary text-secondary-foreground hover:bg-secondary/80',
      destructive: 'bg-destructive text-destructive-foreground hover:bg-destructive/90',
      outline: 'border border-input bg-background hover:bg-accent hover:text-accent-foreground',
      ghost: 'hover:bg-accent hover:text-accent-foreground'
    }
    
    const sizeClasses = {
      sm: 'h-9 px-3 text-sm',
      md: 'h-11 px-4 py-2', // Min 44px height pour l'accessibilité
      lg: 'h-12 px-6 text-lg'
    }
    
    const classes = [
      baseClasses,
      variantClasses[variant],
      sizeClasses[size],
      fullWidth ? 'w-full' : '',
      className
    ].filter(Boolean).join(' ')

    const isDisabled = disabled || loading

    // Texte accessible pour le loading
    const accessibleLoadingText = loadingText || `${children} en cours...`

    return (
      <button
        ref={ref}
        className={classes}
        disabled={isDisabled}
        aria-disabled={isDisabled}
        aria-label={loading ? accessibleLoadingText : undefined}
        {...props}
      >
        {loading && (
          <>
            <Loader2 className="mr-2 h-4 w-4 animate-spin" aria-hidden="true" />
            <span className="sr-only">{accessibleLoadingText}</span>
          </>
        )}
        
        {!loading && Icon && iconPosition === 'left' && (
          <Icon className="mr-2 h-4 w-4" aria-hidden="true" />
        )}
        
        <span>{children}</span>
        
        {!loading && Icon && iconPosition === 'right' && (
          <Icon className="ml-2 h-4 w-4" aria-hidden="true" />
        )}
      </button>
    )
  }
)

AccessibleButton.displayName = 'AccessibleButton'

/**
 * Bouton avec icône uniquement - Nécessite un label accessible
 */
type IconButtonProps = Omit<AccessibleButtonProps, 'children'> & {
  icon: React.ComponentType<{ className?: string }>
  'aria-label': string
  tooltip?: string
}

export const IconButton = forwardRef<HTMLButtonElement, IconButtonProps>(
  ({ icon: Icon, 'aria-label': ariaLabel, tooltip, size = 'md', ...props }, ref) => {
    const sizeClasses = {
      sm: 'h-8 w-8',
      md: 'h-11 w-11', // Min 44px pour l'accessibilité
      lg: 'h-12 w-12'
    }

    return (
      <AccessibleButton
        ref={ref}
        className={`${sizeClasses[size]} ${props.className || ''}`}
        aria-label={ariaLabel}
        title={tooltip || ariaLabel}
        {...props}
      >
        <Icon className="h-4 w-4" aria-hidden="true" />
      </AccessibleButton>
    )
  }
)

IconButton.displayName = 'IconButton'

/**
 * Bouton toggle accessible (pressed/unpressed)
 */
type ToggleButtonProps = AccessibleButtonProps & {
  pressed: boolean
  onToggle: (pressed: boolean) => void
  pressedLabel?: string
  unpressedLabel?: string
}

export const ToggleButton = forwardRef<HTMLButtonElement, ToggleButtonProps>(
  ({ 
    pressed, 
    onToggle, 
    pressedLabel, 
    unpressedLabel, 
    children, 
    onClick,
    ...props 
  }, ref) => {
    
    const handleClick = (e: React.MouseEvent<HTMLButtonElement>) => {
      onToggle(!pressed)
      onClick?.(e)
    }

    const accessibleLabel = pressed 
      ? pressedLabel || `${children} activé`
      : unpressedLabel || `${children} désactivé`

    return (
      <AccessibleButton
        ref={ref}
        variant={pressed ? 'primary' : 'outline'}
        aria-pressed={pressed}
        aria-label={accessibleLabel}
        onClick={handleClick}
        {...props}
      >
        {children}
      </AccessibleButton>
    )
  }
)

ToggleButton.displayName = 'ToggleButton'