import { Link } from 'react-router-dom'
import BaseLayout from './BaseLayout'
import { Construction, ArrowLeft } from 'lucide-react'

interface AdminToolPageProps {
  title: string
  description: string
  toolName: string
}

/**
 * Page générique pour les outils d'administration non encore implémentés
 */
export default function AdminToolPage({ title, description, toolName }: AdminToolPageProps) {
  return (
    <BaseLayout title={`${title} - GenEWeb`}>
      <div className="space-y-8">
        {/* En-tête */}
        <div className="text-center">
          <h1 className="text-3xl font-bold mb-2">{title}</h1>
          <p className="text-muted-foreground">
            {description}
          </p>
        </div>

        <div className="bg-card border border-border rounded-lg overflow-hidden max-w-2xl mx-auto">
          {/* Statut en développement */}
          <div className="p-4 bg-yellow-50 dark:bg-yellow-950/50 border-b border-border">
            <div className="flex items-start gap-3">
              <Construction className="h-5 w-5 text-yellow-600 dark:text-yellow-400 flex-shrink-0 mt-0.5" />
              <div className="text-sm">
                <p className="font-medium text-yellow-800 dark:text-yellow-200 mb-1">
                  🚧 Fonctionnalité en développement
                </p>
                <p className="text-yellow-700 dark:text-yellow-300">
                  L'outil <strong>{toolName}</strong> est prévu mais n'est pas encore implémenté dans cette version moderne de GenEWeb.
                </p>
              </div>
            </div>
          </div>

          <div className="p-8 text-center">
            <div className="space-y-4">
              <Construction className="h-16 w-16 mx-auto text-muted-foreground/50" />

              <div>
                <h2 className="text-xl font-semibold mb-2">Prochainement disponible</h2>
                <p className="text-muted-foreground">
                  Cette fonctionnalité sera ajoutée dans une future version.
                  <br />
                  En attendant, vous pouvez utiliser les autres outils disponibles.
                </p>
              </div>

              <div className="pt-4">
                <Link
                  to="/admin"
                  className="inline-flex items-center gap-2 bg-primary hover:bg-primary/90 text-primary-foreground px-6 py-3 rounded-md transition-colors focus:ring-2 focus:ring-primary focus:ring-offset-2"
                >
                  <ArrowLeft className="h-4 w-4" />
                  Retour au menu principal
                </Link>
              </div>
            </div>
          </div>
        </div>
      </div>
    </BaseLayout>
  )
}
