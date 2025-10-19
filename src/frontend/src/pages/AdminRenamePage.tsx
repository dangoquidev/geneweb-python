import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import BaseLayout from './BaseLayout'
import { AccessibleInput, Fieldset } from '../components/shared/AccessibleForm'
import { AccessibleButton } from '../components/shared/AccessibleButton'
import { useLiveRegion } from '../components/shared/LiveRegion'
import { Edit3, CheckCircle, AlertCircle, Loader2 } from 'lucide-react'

interface DatabaseInfo {
  name: string
  size?: number
  records?: number
  last_modified?: string
}

/**
 * Page de renommage des bases de données GenEWeb
 * Reproduction fidèle des fonctionnalités de renommage OCaml
 */
export default function AdminRenamePage() {
  const [databases, setDatabases] = useState<DatabaseInfo[]>([])
  const [selectedDatabase, setSelectedDatabase] = useState('')
  const [newName, setNewName] = useState('')
  const [isRenaming, setIsRenaming] = useState(false)
  const [message, setMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null)
  const [mounted, setMounted] = useState(false)

  const { announce } = useLiveRegion()

  // Charger les bases de données disponibles
  useEffect(() => {
    setMounted(true)
  }, [])

  useEffect(() => {
    if (!mounted) return

    const fetchDatabases = async () => {
      try {
        const response = await fetch('http://127.0.0.1:8000/api/databases')
        if (response.ok) {
          const data = await response.json()
          console.log('Bases de données chargées:', data.databases)

          // Adapter les données : transformer le tableau de strings en tableau d'objets DatabaseInfo
          const databaseList: DatabaseInfo[] = (data.databases || []).map((dbName: string) => ({
            name: dbName,
            size: undefined,
            records: undefined,
            last_modified: undefined
          }))

          setDatabases(databaseList)
        }
      } catch (error) {
        console.error('Erreur lors du chargement des bases:', error)
      }
    }

    fetchDatabases()
  }, [mounted])

  const handleRename = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!selectedDatabase) {
      setMessage({ type: 'error', text: 'Veuillez sélectionner une base de données' })
      announce('Erreur: Veuillez sélectionner une base de données')
      return
    }

    if (!newName.trim()) {
      setMessage({ type: 'error', text: 'Veuillez saisir un nouveau nom' })
      announce('Erreur: Veuillez saisir un nouveau nom')
      return
    }

    if (newName.trim() === selectedDatabase) {
      setMessage({ type: 'error', text: 'Le nouveau nom doit être différent du nom actuel' })
      announce('Erreur: Le nouveau nom doit être différent du nom actuel')
      return
    }

    // Vérifier si le nouveau nom existe déjà
    if (databases.some(db => db.name === newName.trim())) {
      setMessage({ type: 'error', text: 'Une base de données avec ce nom existe déjà' })
      announce('Erreur: Une base de données avec ce nom existe déjà')
      return
    }

    setIsRenaming(true)
    setMessage(null)

    try {
      const renameData = {
        old_name: selectedDatabase,
        new_name: newName.trim()
      }

      const response = await fetch('/api/admin/rename', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(renameData)
      })

      if (response.ok) {
        setMessage({
          type: 'success',
          text: `Base de données "${selectedDatabase}" renommée en "${newName.trim()}" avec succès !`
        })
        announce(`Base de données renommée avec succès de ${selectedDatabase} vers ${newName.trim()}`)

        // Recharger la liste des bases
        const updatedDatabases = databases.map(db =>
          db.name === selectedDatabase
            ? { ...db, name: newName.trim() }
            : db
        )
        setDatabases(updatedDatabases)

        // Réinitialiser le formulaire
        setSelectedDatabase('')
        setNewName('')

      } else {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.message || errorData.detail || 'Erreur lors du renommage')
      }

    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : 'Erreur de renommage'
      setMessage({ type: 'error', text: errorMsg })
      announce(`Erreur: ${errorMsg}`)
    } finally {
      setIsRenaming(false)
    }
  }

  const validateNewName = (name: string): string | null => {
    if (!name.trim()) {
      return 'Le nom ne peut pas être vide'
    }
    if (name.length > 50) {
      return 'Le nom ne peut pas dépasser 50 caractères'
    }
    if (!/^[a-zA-Z0-9_-]+$/.test(name)) {
      return 'Le nom ne peut contenir que des lettres, chiffres, tirets et underscores'
    }
    if (databases.some(db => db.name === name.trim())) {
      return 'Une base de données avec ce nom existe déjà'
    }
    return null
  }

  const newNameError = newName ? validateNewName(newName) : null

  return (
    <BaseLayout title="Renommer une base de données - GenEWeb">
      <div className="space-y-8">
        {/* En-tête */}
        <div className="text-center">
          <h1 className="text-3xl font-bold mb-2">Renommer une base de données</h1>
          <p className="text-muted-foreground">
            Modifier le nom d'une base de données existante
          </p>
        </div>

        <div className="bg-card border border-border rounded-lg overflow-hidden max-w-2xl mx-auto">
          {/* Messages */}
          {message && (
            <div className={`p-4 border-b border-border ${
              message.type === 'success'
                ? 'bg-green-50 dark:bg-green-950/50'
                : 'bg-destructive/10'
            }`}>
              <div className={`flex items-center gap-2 ${
                message.type === 'success'
                  ? 'text-green-700 dark:text-green-300'
                  : 'text-destructive'
              }`}>
                {message.type === 'success' ? (
                  <CheckCircle className="h-5 w-5 flex-shrink-0" aria-hidden="true" />
                ) : (
                  <AlertCircle className="h-5 w-5 flex-shrink-0" aria-hidden="true" />
                )}
                <span>{message.text}</span>
              </div>
            </div>
          )}

          {/* Formulaire de renommage */}
          <div className="p-8">
            <form onSubmit={handleRename} className="space-y-6">

              <Fieldset legend="Sélection de la base de données à renommer">
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-foreground mb-2">
                      Base de données à renommer :
                    </label>
                    <select
                      value={selectedDatabase}
                      onChange={(e: React.ChangeEvent<HTMLSelectElement>) => {
                        setSelectedDatabase(e.target.value)
                        setMessage(null)
                      }}
                      className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
                      required
                    >
                      <option key="empty" value="">Sélectionnez une base de données</option>
                      {databases.map((db) => (
                        <option key={db.name} value={db.name}>
                          {db.name} {db.records && `(${db.records} enregistrements)`}
                        </option>
                      ))}
                    </select>
                    {databases.length === 0 && (
                      <p className="text-xs text-muted-foreground mt-1">
                        Aucune base de données disponible
                      </p>
                    )}
                  </div>

                  {selectedDatabase && (
                    <div className="bg-blue-50 dark:bg-blue-950/50 rounded-lg p-4">
                      <p className="text-sm text-blue-700 dark:text-blue-300">
                        <strong>Base sélectionnée :</strong> {selectedDatabase}
                      </p>
                    </div>
                  )}
                </div>
              </Fieldset>

              <Fieldset legend="Nouveau nom">
                <div className="space-y-4">
                  <AccessibleInput
                    id="new-name"
                    label="Nouveau nom de la base de données :"
                    type="text"
                    value={newName}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => setNewName(e.target.value)}
                    placeholder="nouveau_nom"
                    className="w-full"
                    help="Le nom ne peut contenir que des lettres, chiffres, tirets et underscores"
                    error={newNameError || undefined}
                    disabled={!selectedDatabase}
                    required
                  />

                  <div className="bg-muted/50 rounded-lg p-4 text-sm">
                    <p className="font-medium mb-2">Règles de nommage :</p>
                    <ul className="space-y-1 text-muted-foreground">
                      <li>• Seuls les lettres, chiffres, tirets (-) et underscores (_) sont autorisés</li>
                      <li>• Maximum 50 caractères</li>
                      <li>• Le nom doit être unique (pas de doublons)</li>
                      <li>• Évitez les espaces et caractères spéciaux</li>
                    </ul>
                  </div>
                </div>
              </Fieldset>

              <div className="flex justify-end gap-4">
                <AccessibleButton
                  type="button"
                  onClick={() => {
                    setSelectedDatabase('')
                    setNewName('')
                    setMessage(null)
                  }}
                  className="bg-muted hover:bg-muted/80 text-muted-foreground px-6 py-2"
                  disabled={isRenaming}
                >
                  Annuler
                </AccessibleButton>

                <AccessibleButton
                  type="submit"
                  disabled={isRenaming || !selectedDatabase || !newName.trim() || !!newNameError}
                  className="bg-primary hover:bg-primary/90 text-primary-foreground px-6 py-2"
                  icon={isRenaming ? Loader2 : Edit3}
                >
                  {isRenaming ? 'Renommage en cours...' : 'Renommer la base'}
                </AccessibleButton>
              </div>
            </form>
          </div>

          {/* Navigation retour */}
          <div className="px-8 py-6 bg-muted/30 border-t border-border">
            <div className="text-center">
              <Link
                to="/admin"
                className="text-primary hover:text-primary/80 hover:underline transition-colors focus:ring-2 focus:ring-primary focus:ring-offset-2 rounded px-2 py-1"
              >
                ← Retour au menu principal
              </Link>
            </div>
          </div>
        </div>
      </div>
    </BaseLayout>
  )
}
