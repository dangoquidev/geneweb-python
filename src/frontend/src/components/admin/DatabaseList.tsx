import { useState, useEffect } from 'react'
import { Database, Trash2, Info, RefreshCw, AlertCircle } from 'lucide-react'
import { AccessibleButton } from '../shared/AccessibleButton'
import { useLiveRegion } from '../shared/LiveRegion'
import { listDatabases, getDatabaseInfo, deleteDatabase, ApiError } from '../../services/api'
import type { DatabaseInfoResponse } from '../../services/api'

interface DeleteConfirmModalProps {
  databaseName: string
  onConfirm: () => void
  onCancel: () => void
  isDeleting: boolean
}

const DeleteConfirmModal = ({ databaseName, onConfirm, onCancel, isDeleting }: DeleteConfirmModalProps) => (
  <div
    className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50"
    role="dialog"
    aria-modal="true"
    aria-labelledby="delete-dialog-title"
  >
    <div className="bg-card border border-border rounded-lg max-w-md w-full p-6 shadow-lg">
      <h2 id="delete-dialog-title" className="text-xl font-semibold mb-4 text-foreground">
        Confirmer la suppression
      </h2>
      <p className="text-muted-foreground mb-6">
        Êtes-vous sûr de vouloir supprimer la base de données <strong className="text-foreground">"{databaseName}"</strong> ?
        Cette action est irréversible.
      </p>
      <div className="flex gap-3 justify-end">
        <AccessibleButton
          onClick={onCancel}
          disabled={isDeleting}
          variant="outline"
        >
          Annuler
        </AccessibleButton>
        <AccessibleButton
          onClick={onConfirm}
          disabled={isDeleting}
          className="bg-destructive hover:bg-destructive/90 text-destructive-foreground"
        >
          {isDeleting ? 'Suppression...' : 'Supprimer'}
        </AccessibleButton>
      </div>
    </div>
  </div>
)

interface DatabaseDetailsModalProps {
  database: DatabaseInfoResponse
  onClose: () => void
}

const DatabaseDetailsModal = ({ database, onClose }: DatabaseDetailsModalProps) => {
  const formatDate = (dateString: string) => {
    try {
      return new Date(dateString).toLocaleString('fr-FR', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      })
    } catch {
      return dateString
    }
  }

  return (
    <div
      className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50"
      role="dialog"
      aria-modal="true"
      aria-labelledby="details-dialog-title"
      onClick={onClose}
    >
      <div
        className="bg-card border border-border rounded-lg max-w-2xl w-full p-6 shadow-lg"
        onClick={(e) => e.stopPropagation()}
      >
        <h2 id="details-dialog-title" className="text-2xl font-semibold mb-6 text-foreground flex items-center gap-2">
          <Database className="h-6 w-6" aria-hidden="true" />
          {database.base_name}
        </h2>

        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <dt className="text-sm font-medium text-muted-foreground">Chemin</dt>
              <dd className="text-sm text-foreground mt-1 font-mono break-all">{database.path}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-muted-foreground">Version</dt>
              <dd className="text-sm text-foreground mt-1">{database.version}</dd>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <dt className="text-sm font-medium text-muted-foreground">Créée le</dt>
              <dd className="text-sm text-foreground mt-1">{formatDate(database.created_date)}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-muted-foreground">Modifiée le</dt>
              <dd className="text-sm text-foreground mt-1">{formatDate(database.modified_date)}</dd>
            </div>
          </div>

          <div className="border-t border-border pt-4">
            <h3 className="text-sm font-medium text-muted-foreground mb-3">Contenu</h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <dt className="text-sm font-medium text-muted-foreground">Personnes</dt>
                <dd className="text-2xl font-bold text-foreground mt-1">{database.persons}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-muted-foreground">Familles</dt>
                <dd className="text-2xl font-bold text-foreground mt-1">{database.families}</dd>
              </div>
            </div>
          </div>
        </div>

        <div className="mt-6 flex justify-end">
          <AccessibleButton onClick={onClose}>
            Fermer
          </AccessibleButton>
        </div>
      </div>
    </div>
  )
}

export default function DatabaseList() {
  const [databases, setDatabases] = useState<string[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null)
  const [isDeleting, setIsDeleting] = useState(false)
  const [detailsDatabase, setDetailsDatabase] = useState<DatabaseInfoResponse | null>(null)
  const [isLoadingDetails, setIsLoadingDetails] = useState(false)

  const { announce } = useLiveRegion()

  const loadDatabases = async () => {
    setIsLoading(true)
    setError(null)

    try {
      const result = await listDatabases()
      setDatabases(result.databases)
      announce(`${result.databases.length} base(s) de données trouvée(s)`)
    } catch (err) {
      let errorMsg = 'Erreur lors du chargement des bases de données'

      if (err instanceof ApiError) {
        errorMsg = err.details?.detail || err.details?.message || err.statusText
      } else if (err instanceof Error) {
        errorMsg = err.message
      }

      setError(errorMsg)
      announce(`Erreur: ${errorMsg}`)
    } finally {
      setIsLoading(false)
    }
  }

  const handleShowDetails = async (dbName: string) => {
    setIsLoadingDetails(true)
    try {
      const info = await getDatabaseInfo(dbName)
      setDetailsDatabase(info)
      announce(`Détails de la base ${dbName} chargés`)
    } catch (err) {
      let errorMsg = 'Erreur lors du chargement des détails'

      if (err instanceof ApiError) {
        errorMsg = err.details?.detail || err.details?.message || err.statusText
      } else if (err instanceof Error) {
        errorMsg = err.message
      }

      announce(`Erreur: ${errorMsg}`)
    } finally {
      setIsLoadingDetails(false)
    }
  }

  const handleDelete = async (dbName: string) => {
    setIsDeleting(true)

    try {
      await deleteDatabase(dbName)
      announce(`Base ${dbName} supprimée avec succès`)
      setDeleteConfirm(null)
      // Reload the list
      await loadDatabases()
    } catch (err) {
      let errorMsg = 'Erreur lors de la suppression'

      if (err instanceof ApiError) {
        errorMsg = err.details?.detail || err.details?.message || err.statusText
      } else if (err instanceof Error) {
        errorMsg = err.message
      }

      announce(`Erreur: ${errorMsg}`)
      setDeleteConfirm(null)
    } finally {
      setIsDeleting(false)
    }
  }

  useEffect(() => {
    loadDatabases()
  }, [])

  return (
    <div className="space-y-4">
      {/* En-tête avec bouton refresh */}
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-foreground">
          Bases de données existantes
        </h2>
        <AccessibleButton
          onClick={loadDatabases}
          disabled={isLoading}
          variant="outline"
          className="flex items-center gap-2"
        >
          <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} aria-hidden="true" />
          Actualiser
        </AccessibleButton>
      </div>

      {/* États de chargement et d'erreur */}
      {isLoading && !databases.length && (
        <div className="text-center py-8">
          <RefreshCw className="h-8 w-8 animate-spin text-muted-foreground mx-auto mb-2" aria-hidden="true" />
          <p className="text-muted-foreground">Chargement des bases de données...</p>
        </div>
      )}

      {error && (
        <div className="bg-destructive/10 border border-destructive/20 rounded-lg p-4">
          <div className="flex items-center gap-2 text-destructive">
            <AlertCircle className="h-5 w-5 flex-shrink-0" aria-hidden="true" />
            <span>{error}</span>
          </div>
        </div>
      )}

      {/* Liste des bases */}
      {!isLoading && !error && databases.length === 0 && (
        <div className="text-center py-12 bg-muted/30 border border-border rounded-lg">
          <Database className="h-12 w-12 text-muted-foreground mx-auto mb-4" aria-hidden="true" />
          <p className="text-muted-foreground text-lg">Aucune base de données trouvée</p>
          <p className="text-sm text-muted-foreground mt-2">
            Créez votre première base de données ci-dessus
          </p>
        </div>
      )}

      {!isLoading && databases.length > 0 && (
        <div className="grid gap-4">
          {databases.map((dbName) => (
            <div
              key={dbName}
              className="bg-card border border-border rounded-lg p-4 hover:border-primary/50 transition-colors"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <Database className="h-5 w-5 text-primary" aria-hidden="true" />
                    <h3 className="text-lg font-semibold text-foreground">{dbName}</h3>
                  </div>
                  <div className="text-sm text-muted-foreground">
                    <p>Cliquez sur "Détails" pour voir les informations complètes</p>
                  </div>
                </div>

                <div className="flex gap-2">
                  <AccessibleButton
                    onClick={() => handleShowDetails(dbName)}
                    disabled={isLoadingDetails}
                    variant="outline"
                    className="flex items-center gap-2"
                    aria-label={`Voir les détails de ${dbName}`}
                  >
                    <Info className="h-4 w-4" aria-hidden="true" />
                    Détails
                  </AccessibleButton>
                  <AccessibleButton
                    onClick={() => setDeleteConfirm(dbName)}
                    variant="outline"
                    className="flex items-center gap-2 border-destructive/20 text-destructive hover:bg-destructive/10"
                    aria-label={`Supprimer ${dbName}`}
                  >
                    <Trash2 className="h-4 w-4" aria-hidden="true" />
                    Supprimer
                  </AccessibleButton>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Modales */}
      {deleteConfirm && (
        <DeleteConfirmModal
          databaseName={deleteConfirm}
          onConfirm={() => handleDelete(deleteConfirm)}
          onCancel={() => setDeleteConfirm(null)}
          isDeleting={isDeleting}
        />
      )}

      {detailsDatabase && (
        <DatabaseDetailsModal
          database={detailsDatabase}
          onClose={() => setDetailsDatabase(null)}
        />
      )}
    </div>
  )
}
