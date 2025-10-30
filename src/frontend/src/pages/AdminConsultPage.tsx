import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import BaseLayout from './BaseLayout'
import { Database, AlertCircle, Activity } from 'lucide-react'
import { useLiveRegion } from '../components/shared/LiveRegion'
import { listDatabases, ApiError } from '../services/api'
import { useTranslation } from 'react-i18next'

type DatabaseInfo = {
  name: string
  url: string
}

/**
 * Page de consultation des bases de données GenEWeb
 * Reproduction fidèle du template list.htm original
 */
export default function AdminConsultPage() {
  const { t } = useTranslation('common')
  const [databases, setDatabases] = useState<DatabaseInfo[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [mounted, setMounted] = useState(false)
  const { announce } = useLiveRegion()

  // Gérer l'hydratation côté client
  useEffect(() => {
    setMounted(true)
  }, [])

  useEffect(() => {
    // Ne faire l'appel API qu'après le montage côté client
    if (!mounted) return

    const fetchDatabases = async () => {
      try {
        setLoading(true)
        setError(null)
        announce(t('database.loading'))

        const result = await listDatabases()

        // Transform database names to DatabaseInfo objects
        const dbList: DatabaseInfo[] = result.databases.map(name => ({
          name,
          url: `/admin/databases/${encodeURIComponent(name)}` // Route vers la page de consultation
        }))

        setDatabases(dbList)

        if (dbList.length === 0) {
          announce(t('admin.none_found'))
        } else {
          announce(`${dbList.length} ${t('admin.databases')}`)
        }

      } catch (err) {
        let errorMsg = 'Erreur inconnue'

        if (err instanceof ApiError) {
          errorMsg = err.details?.detail || err.details?.message || err.statusText
        } else if (err instanceof Error) {
          errorMsg = err.message
        } else if (typeof err === 'string') {
          errorMsg = err
        }

        // Gestion des erreurs réseau
        if (errorMsg.includes('Failed to fetch') || errorMsg.includes('NetworkError')) {
          errorMsg = 'Unable to connect to server - Check your connection'
        }

        setError(errorMsg)
        announce(`${t('app.error')}: ${errorMsg}`)
        console.error('Error while loading databases:', err)
      } finally {
        setLoading(false)
      }
    }

    fetchDatabases()
  }, [mounted]) // Déclencher après le montage côté client

  return (
    <BaseLayout title={`${t('admin.databases')} - GenEWeb`}>
      <div className="space-y-8">
        {/* En-tête */}
        <div className="text-center">
          <h1 className="text-3xl font-bold mb-2">{t('admin.databases')}</h1>
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
                  <span>{t('database.loading')}</span>
              </div>
            </div>
          )}

          {/* Gestion d'erreur */}
          {error && (
              <div className="mb-6 p-4 bg-destructive/10 border border-destructive/20 rounded-lg">
              <div className="flex items-center gap-2 text-destructive">
                <AlertCircle className="h-5 w-5 flex-shrink-0" aria-hidden="true" />
                  <span className="font-medium">{t('app.error')}:</span>
                <span>{error}</span>
              </div>
            </div>
          )}

            {/* Liste des bases de données */}
            {!loading && !error && (
            <>
              <h2 className="text-xl font-semibold mb-6">
                {t('admin.available_databases')}
              </h2>

              {databases.length === 0 ? (
                <div className="text-center py-12">
                  <Database className="h-16 w-16 mx-auto mb-4 text-muted-foreground" aria-hidden="true" />
                  <p className="text-lg mb-2">
                    {t('admin.none_found')}
                  </p>
                  <p className="text-muted-foreground text-sm mb-6">
                    {t('admin.create_first')}
                  </p>
                  <Link
                    to="/admin/create-import"
                    className="inline-flex items-center gap-2 bg-primary hover:bg-primary/90 text-primary-foreground px-6 py-3 rounded-md font-medium transition-colors focus:ring-2 focus:ring-primary focus:ring-offset-2"
                  >
                    <Database className="h-4 w-4" aria-hidden="true" />
                    {t('admin.create_database')}
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
                          </div>
                        </div>
                        <Link
                          to={db.url}
                          className="inline-flex items-center gap-2 text-primary hover:text-primary/80 font-medium hover:underline transition-colors focus:ring-2 focus:ring-primary focus:ring-offset-2 rounded px-2 py-1"
                        >
                          {t('admin.consult')}
                          <span className="sr-only">{db.name}</span>
                        </Link>
                      </li>
                    ))}
                  </ul>

                  {/* Statistiques */}
                  <div className="mt-8 pt-6 border-t border-border">
                    <p className="text-sm text-muted-foreground text-center">
                      {databases.length} {t('admin.databases')}
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
              ← {t('admin.back_to_menu')}
            </Link>
          </div>
        </div>
      </div>
    </BaseLayout>
  )
}
