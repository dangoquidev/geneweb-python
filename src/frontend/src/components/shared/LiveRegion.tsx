import { createContext, useContext, useState, useEffect } from 'react'

type LiveRegionType = 'polite' | 'assertive' | 'off'

type Announcement = {
  id: string
  message: string
  type: LiveRegionType
  timestamp: number
}

type LiveRegionContextType = {
  announce: (message: string, type?: LiveRegionType) => void
  announceError: (message: string) => void
  announceSuccess: (message: string) => void
  clearAnnouncements: () => void
}

const LiveRegionContext = createContext<LiveRegionContextType | null>(null)

/**
 * Provider pour les live regions ARIA - Conforme WCAG 2.2
 * Permet d'annoncer les changements d'état aux lecteurs d'écran
 */
export function LiveRegionProvider({ children }: { children: React.ReactNode }) {
  const [announcements, setAnnouncements] = useState<Announcement[]>([])

  const announce = (message: string, type: LiveRegionType = 'polite') => {
    const id = `announcement-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
    const announcement: Announcement = {
      id,
      message,
      type,
      timestamp: Date.now()
    }

    setAnnouncements(prev => [...prev, announcement])

    // Auto-nettoyage après 5 secondes
    setTimeout(() => {
      setAnnouncements(prev => prev.filter(a => a.id !== id))
    }, 5000)
  }

  const announceError = (message: string) => {
    announce(`Erreur: ${message}`, 'assertive')
  }

  const announceSuccess = (message: string) => {
    announce(`Succès: ${message}`, 'polite')
  }

  const clearAnnouncements = () => {
    setAnnouncements([])
  }

  const contextValue: LiveRegionContextType = {
    announce,
    announceError,
    announceSuccess,
    clearAnnouncements
  }

  return (
    <LiveRegionContext.Provider value={contextValue}>
      {children}
      
      {/* Live regions pour les annonces */}
      <div className="sr-only" aria-live="polite" aria-atomic="true">
        {announcements
          .filter(a => a.type === 'polite')
          .map(announcement => (
            <div key={announcement.id}>
              {announcement.message}
            </div>
          ))
        }
      </div>
      
      <div className="sr-only" role="alert" aria-live="assertive" aria-atomic="true">
        {announcements
          .filter(a => a.type === 'assertive')
          .map(announcement => (
            <div key={announcement.id}>
              {announcement.message}
            </div>
          ))
        }
      </div>
    </LiveRegionContext.Provider>
  )
}

/**
 * Hook pour utiliser les live regions
 */
export function useLiveRegion() {
  const context = useContext(LiveRegionContext)
  if (!context) {
    throw new Error('useLiveRegion must be used within a LiveRegionProvider')
  }
  return context
}

/**
 * Composant de statut visuel avec annonce accessible
 */
type StatusMessageProps = {
  type: 'success' | 'error' | 'warning' | 'info'
  message: string
  visible?: boolean
  onDismiss?: () => void
  announceToSR?: boolean
}

export function StatusMessage({ 
  type, 
  message, 
  visible = true, 
  onDismiss,
  announceToSR = true 
}: StatusMessageProps) {
  const { announce, announceError } = useLiveRegion()

  useEffect(() => {
    if (visible && announceToSR) {
      if (type === 'error') {
        announceError(message)
      } else {
        announce(message, type === 'warning' ? 'assertive' : 'polite')
      }
    }
  }, [visible, message, type, announceToSR, announce, announceError])

  if (!visible) return null

  const typeClasses = {
    success: 'bg-green-500/10 border-green-500/20 text-green-700 dark:text-green-400',
    error: 'bg-red-500/10 border-red-500/20 text-red-700 dark:text-red-400',
    warning: 'bg-orange-500/10 border-orange-500/20 text-orange-700 dark:text-orange-400',
    info: 'bg-blue-500/10 border-blue-500/20 text-blue-700 dark:text-blue-400'
  }

  const icons = {
    success: '✓',
    error: '✕',
    warning: '⚠',
    info: 'ℹ'
  }

  return (
    <div 
      className={`flex items-start gap-3 p-4 rounded-lg border ${typeClasses[type]}`}
      role={type === 'error' ? 'alert' : 'status'}
      aria-live={type === 'error' ? 'assertive' : 'polite'}
    >
      <span className="flex-shrink-0 font-bold" aria-hidden="true">
        {icons[type]}
      </span>
      <div className="flex-1">
        <p className="text-sm">{message}</p>
      </div>
      {onDismiss && (
        <button
          onClick={onDismiss}
          className="flex-shrink-0 opacity-70 hover:opacity-100 focus:ring-2 focus:ring-ring focus:ring-offset-2 rounded-sm"
          aria-label="Fermer le message"
        >
          <span aria-hidden="true">×</span>
        </button>
      )}
    </div>
  )
}