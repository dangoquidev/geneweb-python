import type { PropsWithChildren, ReactNode } from "react";
import { useEffect } from "react";
import { useLiveRegion } from "@/components/shared/LiveRegion";

type BaseLayoutProps = PropsWithChildren<{
  title?: string
  showNavbar?: boolean
  navbarItems?: ReactNode
  containerClassName?: string
  skipLinkTarget?: string
}>

/**
 * App shell with optional navbar and footer - Conforme WCAG 2.2 AA
 * Inclut landmarks, skip links, et gestion du focus
 */
export default function BaseLayout({
  title = "GenEWeb Server",
  showNavbar = true,
  navbarItems,
  containerClassName,
  skipLinkTarget = "#main-content",
  children,
}: BaseLayoutProps) {
  const { announce } = useLiveRegion();
  // Gestion du focus sur changement de route
  useEffect(() => {
    // Mettre le focus sur le contenu principal lors du changement de page
    const mainContent = document.querySelector(skipLinkTarget) as HTMLElement
    if (mainContent) {
      mainContent.focus()
    }
  }, [skipLinkTarget, title])

  // Mise à jour du titre de page et métadonnées
  useEffect(() => {
    document.title = title

    // Mise à jour de la description si nécessaire
    const descriptionMeta = document.querySelector('meta[name="description"]')
    if (descriptionMeta) {
      descriptionMeta.setAttribute('content', 'GenEWeb - Serveur de généalogie moderne et accessible')
    }
    // Annonce du changement de page
    announce(title)
  }, [title])

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col">

      {/* Skip link - Premier élément focusable */}
      <a
        href={skipLinkTarget}
        className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 bg-primary text-primary-foreground px-4 py-2 rounded-md z-50 focus:ring-2 focus:ring-ring focus:ring-offset-2"
      >
        Aller au contenu principal
      </a>

      {showNavbar && (
        <header role="banner">
          <nav
            className="sticky top-0 z-10 border-b border-border bg-background/90 backdrop-blur"
            aria-label="Navigation principale"
          >
            <div className="container mx-auto px-4 py-3 flex items-center justify-between">
              <a
                className="font-semibold focus:ring-2 focus:ring-ring focus:ring-offset-2 rounded-md px-2 py-1"
                href="/"
                aria-label="GenEWeb - Retour à l'accueil"
              >
                GenEWeb
              </a>
              <div className="flex items-center gap-4" role="navigation" aria-label="Menu utilisateur">
                {navbarItems ?? (
                  <a
                    className="text-sm opacity-90 hover:opacity-100 focus:ring-2 focus:ring-ring focus:ring-offset-2 rounded-md px-2 py-1"
                    href="/"
                  >
                    Accueil
                  </a>
                )}
              </div>
            </div>
          </nav>
        </header>
      )}

      <main
        id="main-content"
        className={containerClassName ?? "container mx-auto flex-1 w-full px-4 py-4"}
        tabIndex={-1}
        role="main"
      >
        {children}
      </main>

      <footer
        className="mt-6 border-t border-border"
        role="contentinfo"
      >
        <div className="container mx-auto px-4 py-6 text-center text-sm">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <strong>GenEWeb</strong> - Serveur de généalogie
              <br />
              Copyright © 1998-2007 INRIA
            </div>
            <div>
              Version Python modernisée
              <br />
              Compatible avec GenEWeb original
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}
