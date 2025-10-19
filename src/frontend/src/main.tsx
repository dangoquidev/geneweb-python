import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { createBrowserRouter, RouterProvider } from 'react-router-dom'
import './index.css'
import './i18n'
import i18next from 'i18next'
import HomePage from './pages/HomePage'
import DatabasePage from './pages/DatabasePage'
import AdminHomePage from './pages/AdminHomePage'
import AdminCreateImportPage from './pages/AdminCreateImportPage'
import AdminConsultPage from './pages/AdminConsultPage'
import AdminExportPage from './pages/AdminExportPage'
import AdminBackupPage from './pages/AdminBackupPage'
import AdminRenamePage from './pages/AdminRenamePage'
import AdminDeletePage from './pages/AdminDeletePage'
import AdminCleanupPage from './pages/AdminCleanupPage'
import AdminMergePage from './pages/AdminMergePage'
import AdminGwuPage from './pages/AdminGwuPage'
import AdminConsangPage from './pages/AdminConsangPage'
import AdminUpdateNldbPage from './pages/AdminUpdateNldbPage'
import AdminConnexPage from './pages/AdminConnexPage'
import AdminGwdiffPage from './pages/AdminGwdiffPage'
import AdminGwfixbasePage from './pages/AdminGwfixbasePage'
import AdminConfigDatabasePage from './pages/AdminConfigDatabasePage'
import AdminConfigGwdPage from './pages/AdminConfigGwdPage'
import AdminErrorsPage from './pages/AdminErrorsPage'
import { LiveRegionProvider } from './components/shared/LiveRegion'

const router = createBrowserRouter([
  { path: '/', element: <HomePage /> },
  { path: '/database/:baseName', element: <DatabasePage /> },
  { path: '/admin', element: <AdminHomePage /> },
  { path: '/admin/create-import', element: <AdminCreateImportPage /> },
  { path: '/admin/consult', element: <AdminConsultPage /> },
  { path: '/admin/export', element: <AdminExportPage /> },
  { path: '/admin/backup', element: <AdminBackupPage /> },
  { path: '/admin/rename', element: <AdminRenamePage /> },
  { path: '/admin/delete', element: <AdminDeletePage /> },
  { path: '/admin/cleanup', element: <AdminCleanupPage /> },
  { path: '/admin/merge', element: <AdminMergePage /> },
  { path: '/admin/gwu', element: <AdminGwuPage /> },
  { path: '/admin/consang', element: <AdminConsangPage /> },
  { path: '/admin/update-nldb', element: <AdminUpdateNldbPage /> },
  { path: '/admin/connex', element: <AdminConnexPage /> },
  { path: '/admin/gwdiff', element: <AdminGwdiffPage /> },
  { path: '/admin/gwfixbase', element: <AdminGwfixbasePage /> },
  { path: '/admin/config/database', element: <AdminConfigDatabasePage /> },
  { path: '/admin/config/gwd', element: <AdminConfigGwdPage /> },
  { path: '/admin/errors', element: <AdminErrorsPage /> },
])

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <LiveRegionProvider>
      <RouterProvider router={router} />
    </LiveRegionProvider>
  </StrictMode>,
)

// Keep <html lang> in sync with current language
document.documentElement.lang = i18next.language || 'fr'
i18next.on('languageChanged', (lng) => {
  document.documentElement.lang = lng
})
