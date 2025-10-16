import { useState } from 'react'
import { AccessibleButton, IconButton } from '../components/shared/AccessibleButton'
import { AccessibleInput, AccessibleTextarea, AccessibleSelect, Fieldset } from '../components/shared/AccessibleForm'
import { StatusMessage, useLiveRegion } from '../components/shared/LiveRegion'
import { Settings, Save, Eye, Download } from 'lucide-react'

/**
 * Page de démonstration des composants accessibles
 * Utile pour tester la conformité WCAG 2.2 AA
 */
export default function A11yDemoPage() {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    description: '',
    category: '',
    newsletter: false
  })
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [showSuccess, setShowSuccess] = useState(false)
  const [loading, setLoading] = useState(false)
  
  const { announceSuccess, announceError } = useLiveRegion()

  const validateForm = () => {
    const newErrors: Record<string, string> = {}
    
    if (!formData.name.trim()) {
      newErrors.name = 'Le nom est obligatoire'
    }
    
    if (!formData.email.trim()) {
      newErrors.email = 'L\'email est obligatoire'
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = 'Format d\'email invalide'
    }
    
    if (!formData.category) {
      newErrors.category = 'Veuillez sélectionner une catégorie'
    }
    
    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!validateForm()) {
      announceError('Le formulaire contient des erreurs')
      return
    }
    
    setLoading(true)
    
    // Simulation d'envoi
    try {
      await new Promise(resolve => setTimeout(resolve, 2000))
      setShowSuccess(true)
      announceSuccess('Formulaire envoyé avec succès')
      setFormData({ name: '', email: '', description: '', category: '', newsletter: false })
    } catch (error) {
      announceError('Erreur lors de l\'envoi du formulaire')
    } finally {
      setLoading(false)
    }
  }

  const categoryOptions = [
    { value: '', label: 'Sélectionnez une catégorie' },
    { value: 'general', label: 'Général' },
    { value: 'support', label: 'Support technique' },
    { value: 'feature', label: 'Demande de fonctionnalité' },
    { value: 'bug', label: 'Signalement de bug' }
  ]

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-8">
      {/* En-tête avec hiérarchie correcte */}
      <header>
        <h1 className="text-3xl font-bold mb-2">Démonstration Accessibilité</h1>
        <p className="text-muted-foreground">
          Page de test des composants conformes WCAG 2.2 AA
        </p>
      </header>

      {/* Section boutons */}
      <section aria-labelledby="buttons-heading">
        <h2 id="buttons-heading" className="text-xl font-semibold mb-4">
          Boutons Accessibles
        </h2>
        <div className="space-y-4">
          <div className="flex flex-wrap gap-4">
            <AccessibleButton variant="primary">
              Bouton Principal
            </AccessibleButton>
            
            <AccessibleButton variant="secondary" icon={Settings}>
              Avec Icône
            </AccessibleButton>
            
            <AccessibleButton variant="outline" loading={loading}>
              {loading ? 'Chargement...' : 'Charger'}
            </AccessibleButton>
            
            <AccessibleButton variant="destructive" disabled>
              Désactivé
            </AccessibleButton>
          </div>
          
          <div className="flex flex-wrap gap-4">
            <IconButton
              icon={Eye}
              variant="ghost"
              aria-label="Voir les détails"
              tooltip="Afficher les informations détaillées"
            />
            
            <IconButton
              icon={Download}
              variant="outline"
              aria-label="Télécharger le fichier"
            />
            
            <AccessibleButton
              variant={formData.newsletter ? "primary" : "outline"}
              onClick={() => setFormData(prev => ({ ...prev, newsletter: !prev.newsletter }))}
              aria-pressed={formData.newsletter}
            >
              Newsletter {formData.newsletter ? "✓" : ""}
            </AccessibleButton>
          </div>
        </div>
      </section>

      {/* Section formulaire */}
      <section aria-labelledby="form-heading">
        <h2 id="form-heading" className="text-xl font-semibold mb-4">
          Formulaire Accessible
        </h2>
        
        <form onSubmit={handleSubmit} className="space-y-6" noValidate>
          <Fieldset legend="Informations personnelles">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <AccessibleInput
                id="demo-name"
                label="Nom complet"
                type="text"
                value={formData.name}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                error={errors.name}
                help="Entrez votre nom et prénom"
                required
                validationState={errors.name ? 'invalid' : formData.name ? 'valid' : 'neutral'}
              />
              
              <AccessibleInput
                id="demo-email"
                label="Adresse email"
                type="email"
                value={formData.email}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setFormData(prev => ({ ...prev, email: e.target.value }))}
                error={errors.email}
                help="Format: exemple@domaine.com"
                required
                validationState={errors.email ? 'invalid' : formData.email && /\S+@\S+\.\S+/.test(formData.email) ? 'valid' : 'neutral'}
              />
            </div>
          </Fieldset>

          <Fieldset legend="Détails de la demande">
            <AccessibleSelect
              id="demo-category"
              label="Catégorie"
              value={formData.category}
              onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setFormData(prev => ({ ...prev, category: e.target.value }))}
              options={categoryOptions}
              error={errors.category}
              help="Choisissez le type de demande"
              required
              validationState={errors.category ? 'invalid' : formData.category ? 'valid' : 'neutral'}
            />
            
            <AccessibleTextarea
              id="demo-description"
              label="Description"
              value={formData.description}
              onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setFormData(prev => ({ ...prev, description: e.target.value }))}
              help="Décrivez votre demande en détail"
              maxLength={500}
              showCharCount={true}
              rows={4}
            />
          </Fieldset>

          <div className="flex justify-end gap-4">
            <AccessibleButton
              type="button"
              variant="outline"
              onClick={() => {
                setFormData({ name: '', email: '', description: '', category: '', newsletter: false })
                setErrors({})
                setShowSuccess(false)
              }}
            >
              Réinitialiser
            </AccessibleButton>
            
            <AccessibleButton
              type="submit"
              variant="primary"
              loading={loading}
              loadingText="Envoi du formulaire en cours"
              icon={Save}
            >
              Envoyer
            </AccessibleButton>
          </div>
        </form>
      </section>

      {/* Messages de statut */}
      <section aria-labelledby="status-heading">
        <h2 id="status-heading" className="text-xl font-semibold mb-4">
          Messages de Statut
        </h2>
        
        <div className="space-y-4">
          <StatusMessage
            type="success"
            message="Votre demande a été envoyée avec succès !"
            visible={showSuccess}
            onDismiss={() => setShowSuccess(false)}
          />
          
          <StatusMessage
            type="info"
            message="Information: Utilisez Tab pour naviguer entre les éléments"
            visible={true}
          />
          
          <StatusMessage
            type="warning"
            message="Attention: Certains champs sont obligatoires"
            visible={Object.keys(errors).length > 0}
          />
        </div>
      </section>

      {/* Instructions d'accessibilité */}
      <section aria-labelledby="instructions-heading">
        <h2 id="instructions-heading" className="text-xl font-semibold mb-4">
          Instructions d'Accessibilité
        </h2>
        
        <div className="bg-muted/50 rounded-lg p-4 space-y-2 text-sm">
          <p><strong>Navigation clavier :</strong></p>
          <ul className="list-disc list-inside space-y-1 ml-4">
            <li><kbd className="bg-background px-2 py-1 rounded">Tab</kbd> - Élément suivant</li>
            <li><kbd className="bg-background px-2 py-1 rounded">Shift+Tab</kbd> - Élément précédent</li>
            <li><kbd className="bg-background px-2 py-1 rounded">Entrée</kbd> ou <kbd className="bg-background px-2 py-1 rounded">Espace</kbd> - Activer bouton</li>
            <li><kbd className="bg-background px-2 py-1 rounded">Échap</kbd> - Fermer modal/menu</li>
          </ul>
          
          <p className="pt-2"><strong>Lecteurs d'écran :</strong></p>
          <ul className="list-disc list-inside space-y-1 ml-4">
            <li>Les erreurs sont annoncées automatiquement</li>
            <li>Le statut des champs est indiqué (valide/invalide)</li>
            <li>Les changements d'état sont annoncés</li>
            <li>Tous les contrôles ont des labels descriptifs</li>
          </ul>
        </div>
      </section>
    </div>
  )
}