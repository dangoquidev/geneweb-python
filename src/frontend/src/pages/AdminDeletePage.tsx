import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import BaseLayout from './BaseLayout'
import { Fieldset } from '../components/shared/AccessibleForm'
import { AccessibleButton } from '../components/shared/AccessibleButton'
import { useLiveRegion } from '../components/shared/LiveRegion'
import { Trash2, CheckCircle, AlertCircle, Loader2, AlertTriangle } from 'lucide-react'

interface DatabaseInfo {
    name: string
    size?: number
    records?: number
    last_modified?: string
}

/**
 * Page de suppression des bases de données GenEWeb
 * Reproduction fidèle des fonctionnalités de suppression OCaml
 */
export default function AdminDeletePage() {
    const [databases, setDatabases] = useState<DatabaseInfo[]>([])
    const [selectedDatabase, setSelectedDatabase] = useState('')
    const [confirmationText, setConfirmationText] = useState('')
    const [isDeleting, setIsDeleting] = useState(false)
    const [showConfirmation, setShowConfirmation] = useState(false)
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

    const handleDeleteRequest = (e: React.FormEvent) => {
        e.preventDefault()

        if (!selectedDatabase) {
            setMessage({ type: 'error', text: 'Veuillez sélectionner une base de données' })
            announce('Erreur: Veuillez sélectionner une base de données')
            return
        }

        setShowConfirmation(true)
        setMessage(null)
    }

    const handleConfirmDelete = async () => {
        if (confirmationText !== selectedDatabase) {
            setMessage({ type: 'error', text: 'Le nom de confirmation ne correspond pas' })
            announce('Erreur: Le nom de confirmation ne correspond pas')
            return
        }

        setIsDeleting(true)
        setMessage(null)

        try {
            const deleteData = {
                database_name: selectedDatabase
            }

            const response = await fetch('/api/admin/delete', {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(deleteData)
            })

            if (response.ok) {
                setMessage({
                    type: 'success',
                    text: `Base de données "${selectedDatabase}" supprimée avec succès !`
                })
                announce(`Base de données ${selectedDatabase} supprimée avec succès`)

                // Retirer la base de la liste
                setDatabases(databases.filter(db => db.name !== selectedDatabase))

                // Réinitialiser le formulaire
                setSelectedDatabase('')
                setConfirmationText('')
                setShowConfirmation(false)

            } else {
                const errorData = await response.json().catch(() => ({}))
                throw new Error(errorData.message || errorData.detail || 'Erreur lors de la suppression')
            }

        } catch (error) {
            const errorMsg = error instanceof Error ? error.message : 'Erreur de suppression'
            setMessage({ type: 'error', text: errorMsg })
            announce(`Erreur: ${errorMsg}`)
        } finally {
            setIsDeleting(false)
        }
    }

    const handleCancelDelete = () => {
        setShowConfirmation(false)
        setConfirmationText('')
        setMessage(null)
    }

    const isConfirmationValid = confirmationText === selectedDatabase

    return (
        <BaseLayout title="Supprimer une base de données - GenEWeb">
            <div className="space-y-8">
                {/* En-tête */}
                <div className="text-center">
                    <h1 className="text-3xl font-bold mb-2">Supprimer une base de données</h1>
                    <p className="text-muted-foreground">
                        Supprimer définitivement une base de données existante
                    </p>
                </div>

                <div className="bg-card border border-border rounded-lg overflow-hidden max-w-2xl mx-auto">
                    {/* Messages */}
                    {message && (
                        <div className={`p-4 border-b border-border ${message.type === 'success'
                                ? 'bg-green-50 dark:bg-green-950/50'
                                : 'bg-destructive/10'
                            }`}>
                            <div className={`flex items-center gap-2 ${message.type === 'success'
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

                    {/* Avertissement de sécurité */}
                    <div className="p-4 bg-red-50 dark:bg-red-950/50 border-b border-border">
                        <div className="flex items-start gap-3">
                            <AlertTriangle className="h-5 w-5 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />
                            <div className="text-sm">
                                <p className="font-medium text-red-800 dark:text-red-200 mb-1">
                                    ⚠️ Action irréversible
                                </p>
                                <p className="text-red-700 dark:text-red-300">
                                    La suppression d'une base de données est <strong>définitive</strong>.
                                    Toutes les données seront perdues et ne pourront pas être récupérées.
                                </p>
                            </div>
                        </div>
                    </div>

                    {/* Formulaire de suppression */}
                    <div className="p-8">
                        {!showConfirmation ? (
                            /* Étape 1: Sélection de la base */
                            <form onSubmit={handleDeleteRequest} className="space-y-6">

                                <Fieldset legend="Sélection de la base de données à supprimer">
                                    <div className="space-y-4">
                                        <div>
                                            <label className="block text-sm font-medium text-foreground mb-2">
                                                Base de données à supprimer :
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
                                            <div className="bg-red-50 dark:bg-red-950/50 rounded-lg p-4">
                                                <p className="text-sm text-red-700 dark:text-red-300">
                                                    <strong>Base sélectionnée :</strong> {selectedDatabase}
                                                </p>
                                                <p className="text-xs text-red-600 dark:text-red-400 mt-1">
                                                    Cette base sera définitivement supprimée !
                                                </p>
                                            </div>
                                        )}
                                    </div>
                                </Fieldset>

                                <div className="flex justify-end gap-4">
                                    <AccessibleButton
                                        type="submit"
                                        disabled={!selectedDatabase}
                                        className="bg-destructive hover:bg-destructive/90 text-destructive-foreground px-6 py-2"
                                        icon={Trash2}
                                    >
                                        Procéder à la suppression
                                    </AccessibleButton>
                                </div>
                            </form>
                        ) : (
                            /* Étape 2: Confirmation */
                            <div className="space-y-6">
                                <Fieldset legend="Confirmation de suppression">
                                    <div className="space-y-4">
                                        <div className="bg-red-50 dark:bg-red-950/50 rounded-lg p-4">
                                            <p className="text-sm text-red-700 dark:text-red-300 mb-3">
                                                Vous êtes sur le point de supprimer définitivement la base de données :
                                            </p>
                                            <p className="text-lg font-bold text-red-800 dark:text-red-200">
                                                {selectedDatabase}
                                            </p>
                                        </div>

                                        <div>
                                            <label className="block text-sm font-medium text-foreground mb-2">
                                                Pour confirmer, tapez le nom exact de la base de données :
                                            </label>
                                            <input
                                                type="text"
                                                value={confirmationText}
                                                onChange={(e) => setConfirmationText(e.target.value)}
                                                placeholder={selectedDatabase}
                                                className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
                                                autoComplete="off"
                                            />
                                            <p className="text-xs text-muted-foreground mt-1">
                                                Tapez exactement : <code className="bg-muted px-1 rounded">{selectedDatabase}</code>
                                            </p>
                                        </div>

                                        {confirmationText && !isConfirmationValid && (
                                            <p className="text-xs text-destructive">
                                                Le nom ne correspond pas. Tapez exactement "{selectedDatabase}"
                                            </p>
                                        )}
                                    </div>
                                </Fieldset>

                                <div className="flex justify-end gap-4">
                                    <AccessibleButton
                                        type="button"
                                        onClick={handleCancelDelete}
                                        className="bg-muted hover:bg-muted/80 text-muted-foreground px-6 py-2"
                                        disabled={isDeleting}
                                    >
                                        Annuler
                                    </AccessibleButton>

                                    <AccessibleButton
                                        type="button"
                                        onClick={handleConfirmDelete}
                                        disabled={isDeleting || !isConfirmationValid}
                                        className="bg-destructive hover:bg-destructive/90 text-destructive-foreground px-6 py-2"
                                        icon={isDeleting ? Loader2 : Trash2}
                                    >
                                        {isDeleting ? 'Suppression en cours...' : 'Confirmer la suppression'}
                                    </AccessibleButton>
                                </div>
                            </div>
                        )}
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
