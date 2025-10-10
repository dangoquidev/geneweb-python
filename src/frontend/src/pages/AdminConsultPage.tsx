import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import BaseLayout from './BaseLayout'
import { Database, AlertCircle, Activity } from 'lucide-react'
import { useLiveRegion } from '../components/shared/LiveRegion'

type DatabaseInfo = {
  name: string
  url: string
  last_modified?: string
  size?: string
}

/**
 * Page de consultation des bases de données GenEWeb
 * Reproduction fidèle du template list.htm original
 */
export default function AdminConsultPage() {
  const [databases, setDatabases] = useState<DatabaseInfo[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const { announce } = useLiveRegion()

  useEffect(() => {
    const fetchDatabases = async () => {
      try {
        setLoading(true)
        announce('Chargement de la liste des bases de données')
        
        const response = await fetch('/api/admin/databases')
        if (!response.ok) {
          throw new Error('Erreur lors du chargement des bases de données')
        }

        const data = await response.json()
        const dbList = data.databases || []
        
        setDatabases(dbList)
        announce(`${dbList.length} base${dbList.length !== 1 ? 's' : ''} de données trouvée${dbList.length !== 1 ? 's' : ''}`)
      } catch (err) {
        const errorMsg = err instanceof Error ? err.message : 'Erreur inconnue'
        setError(errorMsg)
        announce(`Erreur: ${errorMsg}`)
      } finally {
        setLoading(false)
      }
    }

    fetchDatabases()
  }, [announce])

  return (
    <BaseLayout title="Bases de données - GenEWeb">
      <div className="space-y-8">
        {/* En-tête */}
        <div className="text-center">
          <h1 className="text-3xl font-bold mb-2">Bases de données</h1>
          <p className="text-muted-foreground">
            Consultation des arbres généalogiques disponibles
          </p>
        </div>

        <div className="bg-card border border-border rounded-lg p-8">
            
          {/* Information sur le service gwd */}
          <div className="mb-6 p-4 bg-muted/50 border border-border rounded-lg">
            <p className="text-sm">
              Pour consulter une base de données, le service gwd doit avoir été lancé.{' '}
              <Link 
                to="/admin/gwd-info"
                className="text-primary hover:text-primary/80 underline hover:no-underline font-medium"
              >
                (informations gwd)
              </Link>
            </p>
          </div>

          {/* État de chargement */}
          {loading && (
            <div className="flex items-center justify-center py-12">
              <div className="flex items-center gap-3 text-muted-foreground">
                <Activity className="h-5 w-5 animate-spin" aria-hidden="true" />
                <span>Chargement des bases de données...</span>
              </div>
            </div>
          )}

          {/* Gestion d'erreur */}
          {error && (
            <div className="mb-6 p-4 bg-destructive/10 border border-destructive/20 rounded-lg">
              <div className="flex items-center gap-2 text-destructive">
                <AlertCircle className="h-5 w-5 flex-shrink-0" aria-hidden="true" />
                <span className="font-medium">Erreur :</span>
                <span>{error}</span>
              </div>
            </div>
          )}

            {/* Liste des bases de données */}
            {!loading && !error && (
            <>
              <h2 className="text-xl font-semibold mb-6">
                Bases de données disponibles
              </h2>

              {databases.length === 0 ? (
                <div className="text-center py-12">
                  <Database className="h-16 w-16 mx-auto mb-4 text-muted-foreground" aria-hidden="true" />
                  <p className="text-lg mb-2">
                    Il n'y a pas de base de données actuellement
                  </p>
                  <p className="text-muted-foreground text-sm mb-6">
                    Créez votre première base de données pour commencer
                  </p>
                  <Link
                    to="/admin/create-import"
                    className="inline-flex items-center gap-2 bg-primary hover:bg-primary/90 text-primary-foreground px-6 py-3 rounded-md font-medium transition-colors focus:ring-2 focus:ring-primary focus:ring-offset-2"
                  >
                    <Database className="h-4 w-4" aria-hidden="true" />
                    Créer une base de données
                  </Link>
                </div>
              ) : (
                <div className="space-y-4">
                  <ul className="space-y-3" role="list">
                    {databases.map((db) => (
                      <li key={db.name} className="flex items-center justify-between p-4 bg-muted/50 rounded-lg hover:bg-muted transition-colors">
                        <div className="flex items-center gap-3">
                          <Database className="h-5 w-5 text-primary flex-shrink-0" aria-hidden="true" />
                          <div>
                            <div className="font-medium">
                              {db.name}
                            </div>
                            {(db.size || db.last_modified) && (
                              <div className="text-sm text-muted-foreground mt-1">
                                {db.size && <span>Taille: {db.size}</span>}
                                {db.size && db.last_modified && <span className="mx-2">•</span>}
                                {db.last_modified && <span>Modifié: {new Date(Number(db.last_modified) * 1000).toLocaleDateString()}</span>}
                              </div>
                            )}
                          </div>
                        </div>
                        <a
                          href={db.url}
                          className="inline-flex items-center gap-2 text-primary hover:text-primary/80 font-medium hover:underline transition-colors focus:ring-2 focus:ring-primary focus:ring-offset-2 rounded px-2 py-1"
                          target="_blank"
                          rel="noopener noreferrer"
                        >
                          Consulter
                          <span className="sr-only">la base {db.name} dans un nouvel onglet</span>
                        </a>
                      </li>
                    ))}
                  </ul>

                  {/* Statistiques */}
                  <div className="mt-8 pt-6 border-t border-border">
                    <p className="text-sm text-muted-foreground text-center">
                      {databases.length} base{databases.length !== 1 ? 's' : ''} de données disponible{databases.length !== 1 ? 's' : ''}
                    </p>
                  </div>
                </div>
              )}
            </>
            )}

          {/* Navigation retour */}
          <div className="mt-8 pt-6 border-t border-border text-center">
            <Link
              to="/admin"
              className="text-primary hover:text-primary/80 hover:underline transition-colors focus:ring-2 focus:ring-primary focus:ring-offset-2 rounded px-2 py-1"
            >
              ← Retour au menu principal
            </Link>
          </div>
        </div>
      </div>
    </BaseLayout>
  )
}