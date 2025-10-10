import { Link } from 'react-router-dom'
import BaseLayout from './BaseLayout'
import { Database, FileUp, Save, Settings, Trash2, RefreshCw } from 'lucide-react'

/**
 * Page d'accueil du panel d'administration GenEWeb
 * Reproduction fidèle du template welcome.htm original
 */
export default function AdminHomePage() {
  return (
    <BaseLayout title="Administration GenEWeb">
      <div className="space-y-8">
        {/* En-tête */}
        <div className="text-center">
          <h1 className="text-3xl font-bold mb-2">Panel d'Administration GenEWeb</h1>
          <p className="text-muted-foreground">
            Gestion et création d'arbres généalogiques
          </p>
        </div>

        {/* Navigation principale - Structure originale welcome.htm */}
        <div className="bg-card border border-border rounded-lg p-8">
            <div className="grid md:grid-cols-2 gap-8">
              
              {/* Section Gauche - Consult & Save */}
              <div className="space-y-8">
                {/* Consult */}
                <div>
                  <h2 className="text-xl font-semibold mb-4">
                    Consulter
                  </h2>
                  <ul className="space-y-3">
                    <li>
                      <Link 
                        to="/admin/consult"
                        className="flex items-center gap-2 text-primary hover:text-primary/80 hover:underline transition-colors"
                      >
                        <Database className="h-4 w-4" />
                        Arbres généalogiques (liste)
                      </Link>
                    </li>
                    <li>
                      <Link 
                        to="/admin/errors"
                        className="flex items-center gap-2 text-primary hover:text-primary/80 hover:underline transition-colors"
                      >
                        <Database className="h-4 w-4" />
                        Historique d'erreurs et statistiques
                      </Link>
                    </li>
                  </ul>
                </div>

                {/* Save */}
                <div>
                  <h2 className="text-xl font-semibold mb-4">
                    Sauvegarder
                  </h2>
                  <ul className="space-y-3">
                    <li>
                      <Link 
                        to="/admin/export/gedcom"
                        className="flex items-center gap-2 text-primary hover:text-primary/80 hover:underline transition-colors"
                      >
                        <Save className="h-4 w-4" />
                        Fichier source GEDCOM (gwb2ged)
                      </Link>
                    </li>
                    <li>
                      <Link 
                        to="/admin/export/geneweb"
                        className="flex items-center gap-2 text-primary hover:text-primary/80 hover:underline transition-colors"
                      >
                        <Save className="h-4 w-4" />
                        Fichier source GeneWeb (gwu)
                      </Link>
                    </li>
                  </ul>
                </div>
              </div>

            {/* Section Droite - Create Family Tree */}
            <div>
              <h2 className="text-xl font-semibold mb-4">
                Créer un arbre généalogique
              </h2>
              <ul className="space-y-3">
                <li>
                  <Link 
                    to="/admin/create-import?tab=gedcom"
                    className="flex items-center gap-2 text-primary hover:text-primary/80 hover:underline transition-colors"
                  >
                    <FileUp className="h-4 w-4" />
                    À partir d'un fichier source GEDCOM (ged2gwb)
                  </Link>
                </li>
                <li>
                  <Link 
                    to="/admin/create-import?tab=geneweb"
                    className="flex items-center gap-2 text-primary hover:text-primary/80 hover:underline transition-colors"
                  >
                    <FileUp className="h-4 w-4" />
                    À partir d'un fichier source GeneWeb (gwc)
                  </Link>
                </li>
                <li>
                  <Link 
                    to="/admin/create-import?tab=simple"
                    className="flex items-center gap-2 text-primary hover:text-primary/80 hover:underline transition-colors"
                  >
                    <Database className="h-4 w-4" />
                    Vide (gwc)
                  </Link>
                </li>
              </ul>
            </div>
          </div>

          <hr className="my-8 border-border" />

          {/* Options avancées - Structure originale */}
          <div className="grid md:grid-cols-2 gap-8">
            
            {/* Options avancées */}
            <div>
              <h3 className="text-lg font-semibold mb-4">
                Options avancées
              </h3>
              <ul className="space-y-2 text-sm">
                <li>
                  <Link 
                    to="/admin/cleanup"
                    className="flex items-center gap-2 text-primary hover:text-primary/80 hover:underline transition-colors"
                  >
                    <RefreshCw className="h-3 w-3" />
                    Nettoyage (cleanup)
                  </Link>
                </li>
                <li>
                  <Link 
                    to="/admin/rename"
                    className="flex items-center gap-2 text-primary hover:text-primary/80 hover:underline transition-colors"
                  >
                    <Settings className="h-3 w-3" />
                    Renommage (rename)
                  </Link>
                </li>
                <li>
                  <Link 
                    to="/admin/delete"
                    className="flex items-center gap-2 text-primary hover:text-primary/80 hover:underline transition-colors"
                  >
                    <Trash2 className="h-3 w-3" />
                    Suppression (delete)
                  </Link>
                </li>
              </ul>
            </div>

            {/* Configuration */}
            <div>
              <h3 className="text-lg font-semibold mb-4">
                Configurer
              </h3>
              <ul className="space-y-2 text-sm">
                <li>
                  <Link 
                    to="/admin/config/database"
                    className="flex items-center gap-2 text-primary hover:text-primary/80 hover:underline transition-colors"
                  >
                    <Settings className="h-3 w-3" />
                    Paramètres d'une base de données (.gwf)
                  </Link>
                </li>
                <li>
                  <Link 
                    to="/admin/config/gwd"
                    className="flex items-center gap-2 text-primary hover:text-primary/80 hover:underline transition-colors"
                  >
                    <Settings className="h-3 w-3" />
                    Paramètres du service gwd (gwd)
                  </Link>
                </li>
              </ul>
            </div>
          </div>

          {/* Footer avec documentation */}
          <div className="mt-8 pt-6 border-t border-border">
            <p className="text-sm text-muted-foreground text-center">
              Vous pouvez aussi consulter la documentation complète de GenEWeb
            </p>
          </div>
        </div>
      </div>
    </BaseLayout>
  )
}