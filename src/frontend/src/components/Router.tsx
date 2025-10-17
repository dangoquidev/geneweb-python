import { useEffect, useState } from 'react'

export type Route = {
  path: string
  component: React.ComponentType<any>
  props?: any
}

type RouterProps = {
  routes: Route[]
  defaultPath?: string
}

/**
 * Router simple basé sur window.location.pathname
 * Utilisé pour la navigation entre les pages admin
 */
export function Router({ routes, defaultPath = '/' }: RouterProps) {
  const [currentPath, setCurrentPath] = useState(() => {
    // Initialisation sécurisée pour éviter les erreurs d'hydratation
    if (typeof window !== 'undefined') {
      return window.location.pathname
    }
    return defaultPath
  })

  useEffect(() => {
    // Synchroniser avec le pathname réel après le montage côté client
    if (typeof window !== 'undefined' && window.location.pathname !== currentPath) {
      setCurrentPath(window.location.pathname)
    }
    
    const handlePopState = () => {
      setCurrentPath(window.location.pathname)
    }

    window.addEventListener('popstate', handlePopState)
    return () => window.removeEventListener('popstate', handlePopState)
  }, [])

  // Navigation programmable
  const navigate = (path: string) => {
    window.history.pushState({}, '', path)
    setCurrentPath(path)
  }

  // Recherche de la route correspondante
  const currentRoute = routes.find(route => {
    if (route.path === currentPath) return true
    // Support des routes avec paramètres (ex: /admin/consult?base=test)
    if (route.path.includes('?')) {
      return currentPath.startsWith(route.path.split('?')[0])
    }
    return false
  })

  // Route par défaut si aucune correspondance
  const routeToRender = currentRoute || routes.find(r => r.path === defaultPath)

  if (!routeToRender) {
    return <div>Page non trouvée</div>
  }

  const Component = routeToRender.component
  return <Component navigate={navigate} {...(routeToRender.props || {})} />
}

/**
 * Hook pour la navigation
 */
export function useNavigate() {
  return (path: string) => {
    window.history.pushState({}, '', path)
    window.dispatchEvent(new PopStateEvent('popstate'))
  }
}

/**
 * Composant Link pour la navigation
 */
type LinkProps = {
  to: string
  children: React.ReactNode
  className?: string
  onClick?: () => void
}

export function Link({ to, children, className, onClick }: LinkProps) {
  const navigate = useNavigate()

  const handleClick = (e: React.MouseEvent) => {
    e.preventDefault()
    onClick?.()
    navigate(to)
  }

  return (
    <a href={to} onClick={handleClick} className={className}>
      {children}
    </a>
  )
}