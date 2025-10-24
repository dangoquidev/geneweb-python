import { useState, useRef } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import BaseLayout from './BaseLayout'
import { AccessibleInput } from '../components/shared/AccessibleForm'
import { AccessibleButton } from '../components/shared/AccessibleButton'
import { useLiveRegion } from '../components/shared/LiveRegion'
import { Database, FileUp, Upload, CheckCircle, AlertCircle } from 'lucide-react'
import { createDatabase, ApiError } from '../services/api'
import DatabaseList from '../components/admin/DatabaseList'

interface Fieldset {
  legend: string
  children: React.ReactNode
}

const Fieldset = ({ legend, children }: Fieldset) => (
  <fieldset className="border border-border rounded-lg p-6">
    <legend className="px-2 text-sm font-medium text-foreground">{legend}</legend>
    {children}
  </fieldset>
)

export default function AdminCreateImportPage() {
  const [searchParams] = useSearchParams()
  const activeTabParam = searchParams.get('tab') || 'simple'
  const [activeTab, setActiveTab] = useState<'simple' | 'gedcom' | 'geneweb'>(
    activeTabParam as 'simple' | 'gedcom' | 'geneweb'
  )

  // États des formulaires
  const [simpleName, setSimpleName] = useState('')
  const [gedcomFile, setGedcomFile] = useState<File | null>(null)
  const gedcomFileInputRef = useRef<HTMLInputElement>(null)
  const [outputName, setOutputName] = useState('')
  const [genewebFile, setGenewebFile] = useState<File | null>(null)
  const genewebFileInputRef = useRef<HTMLInputElement>(null)
  const [gweOutput, setGweOutput] = useState('')

  const [isProcessing, setIsProcessing] = useState(false)
  const [message, setMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null)
  const [refreshKey, setRefreshKey] = useState(0)

  const { announce } = useLiveRegion()

  const handleTabChange = (tab: 'simple' | 'gedcom' | 'geneweb') => {
    setActiveTab(tab)
    setMessage(null)
  }

  const refreshDatabaseList = () => {
    setRefreshKey(prev => prev + 1)
  }

  // Validation du nom de base (règles GenEWeb OCaml)
  const validateDatabaseName = (name: string): { valid: boolean; error?: string } => {
    if (!name.trim()) {
      return { valid: false, error: 'Veuillez saisir un nom pour la base' }
    }

    // GenEWeb n'autorise que : a-z, A-Z, 0-9, et tiret (-)
    const invalidChar = name.split('').find(c => !(/[a-zA-Z0-9-]/.test(c)))
    if (invalidChar) {
      return {
        valid: false,
        error: `Le caractère "${invalidChar}" n'est pas autorisé. Seuls les caractères alphanumériques (a-z, A-Z, 0-9) et le tiret (-) sont acceptés.`
      }
    }

    return { valid: true }
  }

  const handleSimpleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    // Valider le nom avant d'envoyer
    const validation = validateDatabaseName(simpleName)
    if (!validation.valid) {
      setMessage({ type: 'error', text: validation.error! })
      announce(`Erreur: ${validation.error}`)
      return
    }

    setIsProcessing(true)
    setMessage(null)

    try {
      // Appel API réel pour créer la base
      const result = await createDatabase({
        name: simpleName,
        db_type: 'pickle',
      })

      setMessage({ type: 'success', text: result.message })
      announce(`Base ${result.database_name} créée avec succès`)
      setSimpleName('')
      refreshDatabaseList()

    } catch (error) {
      let errorMsg = 'Erreur de création de la base'

      if (error instanceof ApiError) {
        // Extraire le message d'erreur de l'API
        errorMsg = error.details?.detail || error.details?.message || error.statusText
      } else if (error instanceof Error) {
        errorMsg = error.message
      }

      setMessage({ type: 'error', text: errorMsg })
      announce(`Erreur: ${errorMsg}`)
    } finally {
      setIsProcessing(false)
    }
  }

  const handleGedcomSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!gedcomFile) {
      setMessage({ type: 'error', text: 'Veuillez sélectionner un fichier GEDCOM' })
      return
    }

    setIsProcessing(true)
    setMessage(null)

    try {
      // Préparer les données du formulaire
      const formData = new FormData()
      formData.append('file', gedcomFile)

      // Nom de la base (outputName ou dérivé du fichier)
      const baseName = outputName || gedcomFile.name.replace(/\.(ged|gedcom)$/i, '').replace(/[^a-zA-Z0-9-]/g, '-')
      formData.append('database_name', baseName)
      formData.append('overwrite', 'false')
      formData.append('lenient', 'true')

      // Appel API réel pour importer le GEDCOM
      const response = await fetch('/api/import/gedcom', {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        // Essayer de lire le corps de la réponse
        let errorMessage = `Erreur HTTP ${response.status}`
        try {
          const errorData = await response.json()
          errorMessage = errorData.detail || errorData.message || errorMessage
        } catch {
          // Si ce n'est pas du JSON, lire comme texte
          const errorText = await response.text()
          if (errorText) {
            errorMessage = errorText.substring(0, 200) // Limiter la longueur
          }
        }
        throw new Error(errorMessage)
      }

      // Vérifier que la réponse contient du JSON
      const contentType = response.headers.get('content-type')
      if (!contentType || !contentType.includes('application/json')) {
        const text = await response.text()
        console.error('Response is not JSON:', text)
        throw new Error(`Réponse invalide du serveur (expected JSON, got ${contentType})`)
      }

      const result = await response.json()

      setMessage({
        type: 'success',
        text: `Import GEDCOM réussi ! ${result.persons_count} personnes et ${result.families_count} familles importées dans "${result.database_name}".`
      })
      announce(`Import GEDCOM réussi : ${result.persons_count} personnes, ${result.families_count} familles`)

      // Réinitialiser le formulaire et rafraîchir la liste
      setGedcomFile(null)
      setOutputName('')
      if (gedcomFileInputRef.current) {
        gedcomFileInputRef.current.value = ''
      }
      refreshDatabaseList()

    } catch (error) {
      let errorMsg = 'Erreur d\'import GEDCOM'

      if (error instanceof Error) {
        errorMsg = error.message
      }

      setMessage({ type: 'error', text: errorMsg })
      announce(`Erreur: ${errorMsg}`)
    } finally {
      setIsProcessing(false)
    }
  }

  const handleGenewebSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!genewebFile) {
      setMessage({ type: 'error', text: 'Veuillez sélectionner un fichier GeneWeb' })
      return
    }

    setIsProcessing(true)
    setMessage(null)

    try {
      // Simulation de l'import GeneWeb
      await new Promise(resolve => setTimeout(resolve, 2500))

      const baseName = gweOutput || genewebFile.name.replace(/\.(gw|txt)$/, '')
      setMessage({ type: 'success', text: `Import GeneWeb réussi ! Base "${baseName}" créée.` })
      announce(`Import GeneWeb réussi, base ${baseName} créée`)

    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : 'Erreur d\'import GeneWeb'
      setMessage({ type: 'error', text: errorMsg })
      announce(`Erreur: ${errorMsg}`)
    } finally {
      setIsProcessing(false)
    }
  }

  return (
    <BaseLayout title="Créer / Importer - GenEWeb">
      <div className="space-y-8">
        {/* En-tête */}
        <div className="text-center">
          <h1 className="text-3xl font-bold mb-2">Créer / Importer</h1>
          <p className="text-muted-foreground">
            Création et importation d'arbres généalogiques
          </p>
        </div>

        <div className="bg-card border border-border rounded-lg overflow-hidden">
          {/* Onglets */}
          <div className="border-b border-border">
            <nav className="flex" role="tablist" aria-label="Options de création">
              <button
                role="tab"
                aria-selected={activeTab === 'simple'}
                aria-controls="simple-panel"
                onClick={() => handleTabChange('simple')}
                className={`flex-1 px-6 py-4 text-sm font-medium border-b-2 transition-colors focus:outline-none focus:ring-2 focus:ring-inset focus:ring-primary ${
                  activeTab === 'simple'
                    ? 'border-primary text-primary bg-primary/5'
                    : 'border-transparent text-muted-foreground hover:text-foreground hover:border-border'
                }`}
              >
                <Database className="h-4 w-4 inline mr-2" aria-hidden="true" />
                Méthode simple
              </button>
              <button
                role="tab"
                aria-selected={activeTab === 'gedcom'}
                aria-controls="gedcom-panel"
                onClick={() => handleTabChange('gedcom')}
                className={`flex-1 px-6 py-4 text-sm font-medium border-b-2 transition-colors focus:outline-none focus:ring-2 focus:ring-inset focus:ring-primary ${
                  activeTab === 'gedcom'
                    ? 'border-primary text-primary bg-primary/5'
                    : 'border-transparent text-muted-foreground hover:text-foreground hover:border-border'
                }`}
              >
                <FileUp className="h-4 w-4 inline mr-2" aria-hidden="true" />
                Import GEDCOM
              </button>
              <button
                role="tab"
                aria-selected={activeTab === 'geneweb'}
                aria-controls="geneweb-panel"
                onClick={() => handleTabChange('geneweb')}
                className={`flex-1 px-6 py-4 text-sm font-medium border-b-2 transition-colors focus:outline-none focus:ring-2 focus:ring-inset focus:ring-primary ${
                  activeTab === 'geneweb'
                    ? 'border-primary text-primary bg-primary/5'
                    : 'border-transparent text-muted-foreground hover:text-foreground hover:border-border'
                }`}
              >
                <Upload className="h-4 w-4 inline mr-2" aria-hidden="true" />
                Import GeneWeb
              </button>
            </nav>
          </div>

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

          {/* Contenu des onglets */}
          <div className="p-8">

            {/* Onglet Méthode simple */}
            {activeTab === 'simple' && (
              <div id="simple-panel" role="tabpanel" aria-labelledby="simple-tab">
                <h2 className="text-xl font-semibold mb-6">
                  Méthode simple
                </h2>

                <form onSubmit={handleSimpleSubmit} className="space-y-6">
                  <Fieldset legend="Création d'une base vide">
                    <div className="space-y-4">
                      <div>
                        <AccessibleInput
                          id="simple-name"
                          label="Écrivez le nom que vous voulez pour votre base de données :"
                          type="text"
                          value={simpleName}
                          onChange={(e: React.ChangeEvent<HTMLInputElement>) => setSimpleName(e.target.value)}
                          placeholder="ma-famille"
                          required
                          className="w-full max-w-md"
                          help="Caractères autorisés : lettres (a-z, A-Z), chiffres (0-9) et tiret (-). Les espaces ne sont pas autorisés."
                        />
                      </div>

                      <div>
                        <p className="text-sm text-muted-foreground mb-4">
                          Puis cliquez sur ce bouton :
                        </p>
                        <AccessibleButton
                          type="submit"
                          disabled={isProcessing || !simpleName.trim()}
                          className="bg-primary hover:bg-primary/90 text-primary-foreground px-6 py-2"
                        >
                          {isProcessing ? 'Création...' : 'Créer'}
                        </AccessibleButton>
                      </div>
                    </div>
                  </Fieldset>
                </form>
              </div>
            )}

            {/* Onglet Import GEDCOM */}
            {activeTab === 'gedcom' && (
              <div id="gedcom-panel" role="tabpanel" aria-labelledby="gedcom-tab">
                <h2 className="text-xl font-semibold mb-6">
                  Importer un fichier GEDCOM
                </h2>

                <form onSubmit={handleGedcomSubmit} className="space-y-6">
                  <Fieldset legend="Sélection du fichier GEDCOM">
                    <div className="space-y-4">
                      <div>
                        <label className="block text-sm font-medium text-foreground mb-2">
                          Sélectionnez votre fichier GEDCOM :
                        </label>
                        <input
                          ref={gedcomFileInputRef}
                          type="file"
                          accept=".ged,.gedcom"
                          onChange={(e) => setGedcomFile(e.target.files?.[0] || null)}
                          className="block w-full text-sm text-muted-foreground file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-medium file:bg-primary/10 file:text-primary hover:file:bg-primary/20"
                          aria-describedby="gedcom-file-help"
                        />
                        <p id="gedcom-file-help" className="text-xs text-muted-foreground mt-1">
                          Formats acceptés: .ged, .gedcom
                        </p>
                        {gedcomFile && (
                          <p className="text-sm text-green-600 dark:text-green-400 mt-2">
                            Fichier sélectionné: {gedcomFile.name}
                          </p>
                        )}
                      </div>

                      <AccessibleInput
                        id="output-name"
                        label="Nom de la base de données (optionnel) :"
                        type="text"
                        value={outputName}
                        onChange={(e: React.ChangeEvent<HTMLInputElement>) => setOutputName(e.target.value)}
                        placeholder="Sera déduit du nom du fichier GEDCOM"
                        className="w-full max-w-md"
                        help="Si omis, sera déduit du nom du fichier GEDCOM"
                      />

                      <div>
                        <AccessibleButton
                          type="submit"
                          disabled={isProcessing || !gedcomFile}
                          className="bg-primary hover:bg-primary/90 text-primary-foreground px-6 py-2"
                        >
                          {isProcessing ? 'Import en cours...' : 'Importer GEDCOM'}
                        </AccessibleButton>
                      </div>
                    </div>
                  </Fieldset>
                </form>
              </div>
            )}

            {/* Onglet Import GeneWeb */}
            {activeTab === 'geneweb' && (
              <div id="geneweb-panel" role="tabpanel" aria-labelledby="geneweb-tab">
                <h2 className="text-xl font-semibold mb-6">
                  Importer un fichier source GeneWeb
                </h2>

                <form onSubmit={handleGenewebSubmit} className="space-y-6">
                  <Fieldset legend="Sélection du fichier GeneWeb">
                    <div className="space-y-4">
                      <div>
                        <label className="block text-sm font-medium text-foreground mb-2">
                          Sélectionnez votre fichier source GeneWeb :
                        </label>
                        <input
                          type="file"
                          accept=".gw,.txt"
                          onChange={(e) => setGenewebFile(e.target.files?.[0] || null)}
                          className="block w-full text-sm text-muted-foreground file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-medium file:bg-primary/10 file:text-primary hover:file:bg-primary/20"
                          aria-describedby="geneweb-file-help"
                        />
                        <p id="geneweb-file-help" className="text-xs text-muted-foreground mt-1">
                          Formats acceptés: .gw, .txt
                        </p>
                        {genewebFile && (
                          <p className="text-sm text-green-600 dark:text-green-400 mt-2">
                            Fichier sélectionné: {genewebFile.name}
                          </p>
                        )}
                      </div>

                      <AccessibleInput
                        id="gwe-output"
                        label="Nom de la base de données (optionnel) :"
                        type="text"
                        value={gweOutput}
                        onChange={(e: React.ChangeEvent<HTMLInputElement>) => setGweOutput(e.target.value)}
                        placeholder="Sera déduit du nom du fichier"
                        className="w-full max-w-md"
                        help="Si omis, sera déduit du nom du fichier source"
                      />

                      <div>
                        <AccessibleButton
                          type="submit"
                          disabled={isProcessing || !genewebFile}
                          className="bg-primary hover:bg-primary/90 text-primary-foreground px-6 py-2"
                        >
                          {isProcessing ? 'Import en cours...' : 'Importer GeneWeb'}
                        </AccessibleButton>
                      </div>
                    </div>
                  </Fieldset>
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
