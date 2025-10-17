import type { PropsWithChildren } from "react"
import BaseLayout from "../../pages/BaseLayout"
import AdminNav from "../navigation/AdminNav"
import { Shield } from "lucide-react"

type AdminLayoutProps = PropsWithChildren<{
  title?: string
  currentPath?: string
  showSidebar?: boolean
}>

/**
 * Layout spécialisé pour les pages d'administration
 * Inclut la navigation admin et les styles appropriés
 */
export default function AdminLayout({ 
  title = "Administration GenEWeb", 
  currentPath,
  showSidebar = true,
  children 
}: AdminLayoutProps) {
  const navbarItems = (
    <div className="flex items-center gap-4">
      <a className="text-sm opacity-90 hover:opacity-100 flex items-center gap-2" href="/admin">
        <Shield className="h-4 w-4" />
        Administration
      </a>
      <a className="text-sm opacity-90 hover:opacity-100" href="/">
        Retour à l'accueil
      </a>
    </div>
  )

  if (!showSidebar) {
    return (
      <BaseLayout 
        title={title} 
        navbarItems={navbarItems}
        containerClassName="container mx-auto flex-1 w-full px-4 py-4"
      >
        {children}
      </BaseLayout>
    )
  }

  return (
    <BaseLayout 
      title={title} 
      navbarItems={navbarItems}
      containerClassName="container mx-auto flex-1 w-full px-4 py-4"
    >
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Sidebar navigation */}
        <div className="lg:col-span-1">
          <div className="sticky top-6">
            <AdminNav currentPath={currentPath} />
          </div>
        </div>
        
        {/* Main content */}
        <div className="lg:col-span-3">
          {children}
        </div>
      </div>
    </BaseLayout>
  )
}