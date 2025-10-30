import { Link } from 'react-router-dom'
import BaseLayout from './BaseLayout'
import { Archive, Download, Database, FileText, RotateCcw } from 'lucide-react'

/**
 * Page de sauvegarde et restauration GenEWeb
 * Reproduction fidèle de la page save.htm OCaml
 */
export default function AdminBackupPage() {
  return (
    <BaseLayout title="Sauvegarde et restauration - GenEWeb">
      <div className="space-y-8">
        {/* En-tête */}
        <div className="text-center">
          <h1 className="text-3xl font-bold mb-2 flex items-center justify-center gap-3">
            <Archive className="h-8 w-8 text-primary" aria-hidden="true" />
            Sauvegarde et restauration
          </h1>
          <p className="text-muted-foreground">
            Sauvegarder et restaurer vos bases de données généalogiques
          </p>
        </div>

        <div className="bg-card border border-border rounded-lg overflow-hidden">
          <div className="p-8 space-y-8">

            {/* Section Sauvegarde */}
            <div className="space-y-6">
              <h2 className="text-xl font-semibold border-b border-border pb-2">
                <Download className="h-5 w-5 inline mr-2 text-primary" aria-hidden="true" />
                Sauvegarde de vos données
              </h2>

              <div className="bg-blue-50 dark:bg-blue-950/30 border border-blue-200 dark:border-blue-800 rounded-lg p-6">
                <p className="text-sm text-blue-800 dark:text-blue-200 mb-4">
                  <strong>Pour sauvegarder votre base de données :</strong>
                </p>
                <p className="text-sm text-blue-700 dark:text-blue-300 mb-6">
                  Appliquez l'extraction d'un fichier source GeneWeb. Ensuite, copiez le fichier obtenu
                  ailleurs sur le disque, ou mieux, sur un support externe.
                </p>

                <div className="space-y-4">
                  <div className="bg-white dark:bg-gray-900 rounded-lg border border-blue-200 dark:border-blue-700 p-4">
                    <h3 className="font-medium text-blue-900 dark:text-blue-100 mb-2 flex items-center gap-2">
                      <FileText className="h-4 w-4" aria-hidden="true" />
                      Export GEDCOM
                    </h3>
                    <p className="text-sm text-blue-700 dark:text-blue-300 mb-3">
                      Format standard compatible avec la plupart des logiciels de généalogie
                    </p>
                    <Link
                      to="/admin/export?tab=gedcom"
                      className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-md transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                    >
                      <Download className="h-4 w-4" aria-hidden="true" />
                      Exporter en GEDCOM
                    </Link>
                  </div>

                  <div className="bg-white dark:bg-gray-900 rounded-lg border border-blue-200 dark:border-blue-700 p-4">
                    <h3 className="font-medium text-blue-900 dark:text-blue-100 mb-2 flex items-center gap-2">
                      <Database className="h-4 w-4" aria-hidden="true" />
                      Export GeneWeb (GWU)
                    </h3>
                    <p className="text-sm text-blue-700 dark:text-blue-300 mb-3">
                      Format source natif de GeneWeb, préserve toutes les données
                    </p>
                    <Link
                      to="/admin/export?tab=geneweb"
                      className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-green-600 hover:bg-green-700 rounded-md transition-colors focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2"
                    >
                      <Database className="h-4 w-4" aria-hidden="true" />
                      Exporter en GeneWeb
                    </Link>
                  </div>
                </div>
              </div>
            </div>

            {/* Section Restauration */}
            <div className="space-y-6">
              <h2 className="text-xl font-semibold border-b border-border pb-2">
                <RotateCcw className="h-5 w-5 inline mr-2 text-primary" aria-hidden="true" />
                Restauration de vos données
              </h2>

              <div className="bg-green-50 dark:bg-green-950/30 border border-green-200 dark:border-green-800 rounded-lg p-6">
                <p className="text-sm text-green-800 dark:text-green-200 mb-4">
                  <strong>Pour restaurer une base de données :</strong>
                </p>
                <p className="text-sm text-green-700 dark:text-green-300 mb-6">
                  Appliquez la création depuis un fichier source GeneWeb ou GEDCOM.
                </p>

                <div className="space-y-4">
                  <div className="bg-white dark:bg-gray-900 rounded-lg border border-green-200 dark:border-green-700 p-4">
                    <h3 className="font-medium text-green-900 dark:text-green-100 mb-2 flex items-center gap-2">
                      <FileText className="h-4 w-4" aria-hidden="true" />
                      Import GEDCOM
                    </h3>
                    <p className="text-sm text-green-700 dark:text-green-300 mb-3">
                      Créer une nouvelle base depuis un fichier GEDCOM
                    </p>
                    <Link
                      to="/admin/create-import?tab=gedcom"
                      className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-md transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                    >
                      <FileText className="h-4 w-4" aria-hidden="true" />
                      Importer GEDCOM
                    </Link>
                  </div>

                  <div className="bg-white dark:bg-gray-900 rounded-lg border border-green-200 dark:border-green-700 p-4">
                    <h3 className="font-medium text-green-900 dark:text-green-100 mb-2 flex items-center gap-2">
                      <Database className="h-4 w-4" aria-hidden="true" />
                      Import GeneWeb (GWC)
                    </h3>
                    <p className="text-sm text-green-700 dark:text-green-300 mb-3">
                      Créer une nouvelle base depuis un fichier source GeneWeb
                    </p>
                    <Link
                      to="/admin/create-import?tab=geneweb"
                      className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-green-600 hover:bg-green-700 rounded-md transition-colors focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2"
                    >
                      <Database className="h-4 w-4" aria-hidden="true" />
                      Importer GeneWeb
                    </Link>
                  </div>
                </div>
              </div>
            </div>

            {/* Conseils et bonnes pratiques */}
            <div className="bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800 rounded-lg p-6">
              <h3 className="font-medium text-amber-900 dark:text-amber-100 mb-3">
                📋 Conseils pour vos sauvegardes
              </h3>
              <ul className="space-y-2 text-sm text-amber-800 dark:text-amber-200">
                <li className="flex items-start gap-2">
                  <span className="text-amber-600 dark:text-amber-400">•</span>
                  <span>Effectuez des sauvegardes régulières de vos données importantes</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-amber-600 dark:text-amber-400">•</span>
                  <span>Stockez vos sauvegardes sur un support externe (clé USB, disque dur externe, cloud)</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-amber-600 dark:text-amber-400">•</span>
                  <span>Le format GeneWeb préserve toutes les données spécifiques à votre base</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-amber-600 dark:text-amber-400">•</span>
                  <span>Le format GEDCOM est plus universel et compatible avec d'autres logiciels</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-amber-600 dark:text-amber-400">•</span>
                  <span>Testez périodiquement la restauration de vos sauvegardes</span>
                </li>
              </ul>
            </div>
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
