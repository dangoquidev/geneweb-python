import { useState, useEffect } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import BaseLayout from './BaseLayout'
import { AccessibleInput, Fieldset } from '../components/shared/AccessibleForm'
import { AccessibleButton } from '../components/shared/AccessibleButton'
import { useLiveRegion } from '../components/shared/LiveRegion'
import { Download, FileText, Database, CheckCircle, AlertCircle, Loader2 } from 'lucide-react'

interface DatabaseInfo {
    name: string
    size?: number
    records?: number
    last_modified?: string
}

/**
 * Page d'export/sauvegarde des bases de données GenEWeb
 * Reproduction fidèle des fonctionnalités de sauvegarde OCaml
 */
export default function AdminExportPage() {
    const [searchParams] = useSearchParams()
    const activeTabParam = searchParams.get('tab') || 'gedcom'
    const [activeTab, setActiveTab] = useState<'gedcom' | 'geneweb'>(
        activeTabParam as 'gedcom' | 'geneweb'
    )
    const [databases, setDatabases] = useState<DatabaseInfo[]>([])
    const [selectedDatabase, setSelectedDatabase] = useState('')
    const [outputName, setOutputName] = useState('')
    const [includeImages, setIncludeImages] = useState(false)
    const [includeNotes, setIncludeNotes] = useState(true)
    const [isExporting, setIsExporting] = useState(false)
    const [message, setMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null)
    const [mounted, setMounted] = useState(false)

    const { announce } = useLiveRegion()

    const handleTabChange = (tab: 'gedcom' | 'geneweb') => {
        setActiveTab(tab)
        setMessage(null)
    }

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

    const handleExport = async (e: React.FormEvent) => {
        e.preventDefault()

        if (!selectedDatabase) {
            setMessage({ type: 'error', text: 'Veuillez sélectionner une base de données' })
            announce('Erreur: Veuillez sélectionner une base de données')
            return
        }

        setIsExporting(true)
        setMessage(null)

        try {
            if (activeTab === 'gedcom') {
                // Export GEDCOM via la vraie API avec options
                const params = new URLSearchParams({
                    include_notes: includeNotes.toString(),
                    include_images: includeImages.toString(),
                })
                const response = await fetch(`/api/export/${selectedDatabase}/gedcom?${params}`)

                if (!response.ok) {
                    throw new Error(`Erreur HTTP ${response.status}`)
                }

                // Télécharger le fichier
                const blob = await response.blob()
                const url = window.URL.createObjectURL(blob)
                const link = document.createElement('a')
                link.href = url
                link.download = `${outputName || selectedDatabase}.ged`
                document.body.appendChild(link)
                link.click()
                document.body.removeChild(link)
                window.URL.revokeObjectURL(url)

                setMessage({
                    type: 'success',
                    text: `Export GEDCOM réussi ! Téléchargement de ${link.download} lancé.`
                })
                announce(`Export GEDCOM réussi, téléchargement de ${link.download} lancé`)

            } else {
                // Export GeneWeb via la vraie API avec options
                const params = new URLSearchParams({
                    include_notes: includeNotes.toString(),
                })
                const response = await fetch(`/api/export/${selectedDatabase}/geneweb?${params}`)

                if (!response.ok) {
                    throw new Error(`Erreur HTTP ${response.status}`)
                }

                // Télécharger le fichier
                const blob = await response.blob()
                const url = window.URL.createObjectURL(blob)
                const link = document.createElement('a')
                link.href = url
                link.download = `${outputName || selectedDatabase}.gw`
                document.body.appendChild(link)
                link.click()
                document.body.removeChild(link)
                window.URL.revokeObjectURL(url)

                setMessage({
                    type: 'success',
                    text: `Export GeneWeb réussi ! Téléchargement de ${link.download} lancé.`
                })
                announce(`Export GeneWeb réussi, téléchargement de ${link.download} lancé`)
            }

        } catch (error) {
            const errorMsg = error instanceof Error ? error.message : `Erreur d'export ${activeTab}`
            setMessage({ type: 'error', text: errorMsg })
            announce(`Erreur: ${errorMsg}`)
        } finally {
            setIsExporting(false)
        }
    }

    const isGedcom = activeTab === 'gedcom'
    const pageTitle = isGedcom ? 'Export GEDCOM' : 'Export GeneWeb'
    const fileExtension = isGedcom ? '.ged' : '.gw'

    return (
        <BaseLayout title={`${pageTitle} - GenEWeb`}>
            <div className="space-y-8">
                {/* En-tête */}
                <div className="text-center">
                    <h1 className="text-3xl font-bold mb-2">{pageTitle}</h1>
                    <p className="text-muted-foreground">
                        {isGedcom
                            ? 'Exporter vos données au format GEDCOM standard'
                            : 'Sauvegarder vos données au format source GeneWeb'
                        }
                    </p>
                </div>

                <div className="bg-card border border-border rounded-lg overflow-hidden">
                    {/* Navigation entre les types */}
                    <div className="border-b border-border">
                        <nav className="flex" role="tablist" aria-label="Types d'export">
                            <button
                                role="tab"
                                aria-selected={activeTab === 'gedcom'}
                                aria-controls="gedcom-panel"
                                onClick={() => handleTabChange('gedcom')}
                                className={`flex-1 px-6 py-4 text-sm font-medium border-b-2 transition-colors focus:outline-none focus:ring-2 focus:ring-inset focus:ring-primary ${activeTab === 'gedcom'
                                    ? 'border-primary text-primary bg-primary/5'
                                    : 'border-transparent text-muted-foreground hover:text-foreground hover:border-border'
                                    }`}
                            >
                                <FileText className="h-4 w-4 inline mr-2" aria-hidden="true" />
                                Export GEDCOM
                            </button>
                            <button
                                role="tab"
                                aria-selected={activeTab === 'geneweb'}
                                aria-controls="geneweb-panel"
                                onClick={() => handleTabChange('geneweb')}
                                className={`flex-1 px-6 py-4 text-sm font-medium border-b-2 transition-colors focus:outline-none focus:ring-2 focus:ring-inset focus:ring-primary ${activeTab === 'geneweb'
                                    ? 'border-primary text-primary bg-primary/5'
                                    : 'border-transparent text-muted-foreground hover:text-foreground hover:border-border'
                                    }`}
                            >
                                <Database className="h-4 w-4 inline mr-2" aria-hidden="true" />
                                Export GeneWeb
                            </button>
                        </nav>
                    </div>

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

                    {/* Contenu des onglets */}
                    <div className="p-8">

                        {/* Onglet Export GEDCOM */}
                        {activeTab === 'gedcom' && (
                            <div id="gedcom-panel" role="tabpanel" aria-labelledby="gedcom-tab">
                                <h2 className="text-xl font-semibold mb-6">
                                    Export GEDCOM
                                </h2>

                                <form onSubmit={handleExport} className="space-y-6">

                                    <Fieldset legend="Sélection de la base de données">
                                        <div className="space-y-4">
                                            <div>
                                                <label className="block text-sm font-medium text-foreground mb-2">
                                                    Base de données à exporter :
                                                </label>
                                                <select
                                                    value={selectedDatabase}
                                                    onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setSelectedDatabase(e.target.value)}
                                                    className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
                                                    required
                                                >
                                                    <option key="empty-gedcom" value="">Sélectionnez une base de données</option>
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

                                            <AccessibleInput
                                                id="output-name"
                                                label={`Nom du fichier de sortie (sans extension ${fileExtension}) :`}
                                                type="text"
                                                value={outputName}
                                                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setOutputName(e.target.value)}
                                                placeholder={`${selectedDatabase || 'export'}_${activeTab}`}
                                                className="w-full max-w-md"
                                                help={`Le fichier sera généré avec l'extension ${fileExtension}`}
                                            />
                                        </div>
                                    </Fieldset>

                                    <Fieldset legend="Options d'export GEDCOM">
                                        <div className="space-y-4">
                                            <div className="flex items-center gap-3">
                                                <input
                                                    type="checkbox"
                                                    id="include-notes"
                                                    checked={includeNotes}
                                                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => setIncludeNotes(e.target.checked)}
                                                    className="h-4 w-4 text-primary focus:ring-2 focus:ring-primary focus:ring-offset-2 border-border rounded"
                                                />
                                                <label htmlFor="include-notes" className="text-sm text-foreground">
                                                    Inclure les notes et commentaires
                                                </label>
                                            </div>

                                            <div className="flex items-center gap-3">
                                                <input
                                                    type="checkbox"
                                                    id="include-images"
                                                    checked={includeImages}
                                                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => setIncludeImages(e.target.checked)}
                                                    className="h-4 w-4 text-primary focus:ring-2 focus:ring-primary focus:ring-offset-2 border-border rounded"
                                                />
                                                <label htmlFor="include-images" className="text-sm text-foreground">
                                                    Inclure les références aux images
                                                </label>
                                            </div>

                                            <div className="bg-muted/50 rounded-lg p-4 text-sm">
                                                <p className="font-medium mb-2">
                                                    À propos du format GEDCOM :
                                                </p>
                                                <ul className="space-y-1 text-muted-foreground">
                                                    <li>• Format standard d'échange généalogique</li>
                                                    <li>• Compatible avec la plupart des logiciels de généalogie</li>
                                                    <li>• Inclut les personnes, familles, événements et sources</li>
                                                </ul>
                                            </div>
                                        </div>
                                    </Fieldset>

                                    <div className="flex justify-end gap-4">
                                        <AccessibleButton
                                            type="submit"
                                            disabled={isExporting || !selectedDatabase}
                                            className="bg-primary hover:bg-primary/90 text-primary-foreground px-6 py-2"
                                            icon={isExporting ? Loader2 : Download}
                                        >
                                            {isExporting
                                                ? `Export ${activeTab} en cours...`
                                                : `Exporter en ${activeTab.toUpperCase()}`
                                            }
                                        </AccessibleButton>
                                    </div>
                                </form>
                            </div>
                        )}

                        {/* Onglet Export GeneWeb */}
                        {activeTab === 'geneweb' && (
                            <div id="geneweb-panel" role="tabpanel" aria-labelledby="geneweb-tab">
                                <h2 className="text-xl font-semibold mb-6">
                                    Export GeneWeb
                                </h2>

                                <form onSubmit={handleExport} className="space-y-6">

                                    <Fieldset legend="Sélection de la base de données">
                                        <div className="space-y-4">
                                            <div>
                                                <label className="block text-sm font-medium text-foreground mb-2">
                                                    Base de données à exporter :
                                                </label>
                                                <select
                                                    value={selectedDatabase}
                                                    onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setSelectedDatabase(e.target.value)}
                                                    className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
                                                    required
                                                >
                                                    <option key="empty-geneweb" value="">Sélectionnez une base de données</option>
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

                                            <AccessibleInput
                                                id="output-name-gw"
                                                label={`Nom du fichier de sortie (sans extension ${fileExtension}) :`}
                                                type="text"
                                                value={outputName}
                                                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setOutputName(e.target.value)}
                                                placeholder={`${selectedDatabase || 'export'}_${activeTab}`}
                                                className="w-full max-w-md"
                                                help={`Le fichier sera généré avec l'extension ${fileExtension}`}
                                            />
                                        </div>
                                    </Fieldset>

                                    <Fieldset legend="Options d'export GeneWeb">
                                        <div className="space-y-4">
                                            <div className="flex items-center gap-3">
                                                <input
                                                    type="checkbox"
                                                    id="include-notes-gw"
                                                    checked={includeNotes}
                                                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => setIncludeNotes(e.target.checked)}
                                                    className="h-4 w-4 text-primary focus:ring-2 focus:ring-primary focus:ring-offset-2 border-border rounded"
                                                />
                                                <label htmlFor="include-notes-gw" className="text-sm text-foreground">
                                                    Inclure les notes et commentaires
                                                </label>
                                            </div>

                                            <div className="bg-muted/50 rounded-lg p-4 text-sm">
                                                <p className="font-medium mb-2">
                                                    À propos du format GeneWeb :
                                                </p>
                                                <ul className="space-y-1 text-muted-foreground">
                                                    <li>• Format source natif de GeneWeb</li>
                                                    <li>• Préserve toutes les données spécifiques à GeneWeb</li>
                                                    <li>• Peut être réimporté sans perte d'information</li>
                                                </ul>
                                            </div>
                                        </div>
                                    </Fieldset>

                                    <div className="flex justify-end gap-4">
                                        <AccessibleButton
                                            type="submit"
                                            disabled={isExporting || !selectedDatabase}
                                            className="bg-primary hover:bg-primary/90 text-primary-foreground px-6 py-2"
                                            icon={isExporting ? Loader2 : Download}
                                        >
                                            {isExporting
                                                ? `Export ${activeTab} en cours...`
                                                : `Exporter en ${activeTab.toUpperCase()}`
                                            }
                                        </AccessibleButton>
                                    </div>
                                </form>
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
