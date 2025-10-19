import { Link } from 'react-router-dom'
import BaseLayout from './BaseLayout'
import { Database, FileUp, Save, Settings, Trash2, RefreshCw } from 'lucide-react'
import { useTranslation } from 'react-i18next'

/**
 * Page d'accueil du panel d'administration GenEWeb
 * Reproduction fidèle du template welcome.htm original
 */
export default function AdminHomePage() {
  const { t } = useTranslation('common')
  return (
    <BaseLayout title={t('admin.admin')}>
      <div className="space-y-8">
        {/* En-tête */}
        <div className="text-center">
          <h1 className="text-3xl font-bold mb-2">{t('admin.panel_title')}</h1>
          <p className="text-muted-foreground">{t('admin.manage_create_trees')}</p>
        </div>

        {/* Navigation principale - Structure originale welcome.htm */}
        <div className="bg-card border border-border rounded-lg p-8">
            <div className="grid md:grid-cols-2 gap-8">

              {/* Section Gauche - Consult & Save */}
              <div className="space-y-8">
                {/* Consult */}
                <div>
                  <h2 className="text-xl font-semibold mb-4">{t('admin.consult')}</h2>
                  <ul className="space-y-3">
                    <li>
                      <Link
                        to="/admin/consult"
                        className="flex items-center gap-2 text-primary hover:text-primary/80 hover:underline transition-colors"
                      >
                        <Database className="h-4 w-4" />
                        {t('admin.trees_list')}
                      </Link>
                    </li>
                    <li>
                      <Link
                        to="/admin/errors"
                        className="flex items-center gap-2 text-primary hover:text-primary/80 hover:underline transition-colors"
                      >
                        <Database className="h-4 w-4" />
                        {t('admin.error_history_stats')}
                      </Link>
                    </li>
                  </ul>
                </div>

                {/* Save */}
                <div>
                  <h2 className="text-xl font-semibold mb-4">{t('admin.save')}</h2>
                  <ul className="space-y-3">
                    <li>
                      <Link
                        to="/admin/export?tab=gedcom"
                        className="flex items-center gap-2 text-primary hover:text-primary/80 hover:underline transition-colors"
                      >
                        <Save className="h-4 w-4" />
                        {t('admin.gedcom_source')}
                      </Link>
                    </li>
                    <li>
                      <Link
                        to="/admin/export?tab=geneweb"
                        className="flex items-center gap-2 text-primary hover:text-primary/80 hover:underline transition-colors"
                      >
                        <Save className="h-4 w-4" />
                        {t('admin.geneweb_source')}
                      </Link>
                    </li>
                  </ul>
                </div>
              </div>

            {/* Section Droite - Create Family Tree */}
            <div>
              <h2 className="text-xl font-semibold mb-4">{t('admin.create_tree')}</h2>
              <ul className="space-y-3">
                <li>
                  <Link
                    to="/admin/create-import?tab=gedcom"
                    className="flex items-center gap-2 text-primary hover:text-primary/80 hover:underline transition-colors"
                  >
                    <FileUp className="h-4 w-4" />
                    {t('admin.from_gedcom_source')}
                  </Link>
                </li>
                <li>
                  <Link
                    to="/admin/create-import?tab=geneweb"
                    className="flex items-center gap-2 text-primary hover:text-primary/80 hover:underline transition-colors"
                  >
                    <FileUp className="h-4 w-4" />
                    {t('admin.from_geneweb_source')}
                  </Link>
                </li>
                <li>
                  <Link
                    to="/admin/create-import?tab=simple"
                    className="flex items-center gap-2 text-primary hover:text-primary/80 hover:underline transition-colors"
                  >
                    <Database className="h-4 w-4" />
                    {t('admin.empty_gwc')}
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
              <h3 className="text-lg font-semibold mb-4">{t('admin.advanced_options')}</h3>
              <ul className="space-y-2 text-sm">
                <li>
                  <Link
                    to="/admin/cleanup"
                    className="flex items-center gap-2 text-primary hover:text-primary/80 hover:underline transition-colors"
                  >
                    <RefreshCw className="h-3 w-3" />
                    {t('admin.cleanup')}
                  </Link>
                </li>
                <li>
                  <Link
                    to="/admin/rename"
                    className="flex items-center gap-2 text-primary hover:text-primary/80 hover:underline transition-colors"
                  >
                    <Settings className="h-3 w-3" />
                    {t('admin.rename')}
                  </Link>
                </li>
                <li>
                  <Link
                    to="/admin/delete"
                    className="flex items-center gap-2 text-primary hover:text-primary/80 hover:underline transition-colors"
                  >
                    <Trash2 className="h-3 w-3" />
                    {t('admin.delete')}
                  </Link>
                </li>
              </ul>
            </div>

            {/* Configuration */}
            <div>
              <h3 className="text-lg font-semibold mb-4">{t('admin.configure')}</h3>
              <ul className="space-y-2 text-sm">
                <li>
                  <Link
                    to="/admin/config/database"
                    className="flex items-center gap-2 text-primary hover:text-primary/80 hover:underline transition-colors"
                  >
                    <Settings className="h-3 w-3" />
                    {t('admin.db_settings')}
                  </Link>
                </li>
                <li>
                  <Link
                    to="/admin/config/gwd"
                    className="flex items-center gap-2 text-primary hover:text-primary/80 hover:underline transition-colors"
                  >
                    <Settings className="h-3 w-3" />
                    {t('admin.gwd_settings')}
                  </Link>
                </li>
              </ul>
            </div>
          </div>

          {/* Footer avec documentation */}
          <div className="mt-8 pt-6 border-t border-border">
            <p className="text-sm text-muted-foreground text-center">{t('admin.docs_prompt')}</p>
          </div>
        </div>
      </div>
    </BaseLayout>
  )
}
