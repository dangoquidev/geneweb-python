import type { PropsWithChildren, ReactNode } from "react";

type BaseLayoutProps = PropsWithChildren<{
  title?: string
  showNavbar?: boolean
  navbarItems?: ReactNode
  containerClassName?: string
}>

export default function BaseLayout({
  title = "GenEWeb Server",
  showNavbar = true,
  navbarItems,
  containerClassName,
  children,
}: BaseLayoutProps) {
  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col">
      <head>
        <title>{title}</title>
        <meta charSet="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no" />
        <link rel="icon" href="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAAC7klEQVR4Ae2XA7BjQRCF..." />
      </head>

      {showNavbar && (
        <nav className="sticky top-0 z-10 border-b border-border bg-background/90 backdrop-blur">
          <div className="container mx-auto px-4 py-3 flex items-center justify-between">
            <a className="font-semibold" href="/">
              GenEWeb
            </a>
            <div className="flex items-center gap-4">
              {navbarItems ?? (
                <a className="text-sm opacity-90 hover:opacity-100" href="/">
                  Accueil
                </a>
              )}
            </div>
          </div>
        </nav>
      )}

      <div className={containerClassName ?? "container mx-auto flex-1 w-full px-4 py-4"}>{children}</div>

      <footer className="mt-6 border-t border-border">
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


