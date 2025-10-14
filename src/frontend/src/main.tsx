import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { createBrowserRouter, RouterProvider } from 'react-router-dom'
import './index.css'
import HomePage from './pages/HomePage'
import DatabasePage from './pages/DatabasePage'
import AdminHomePage from './pages/AdminHomePage'
import AdminCreateImportPage from './pages/AdminCreateImportPage'
import AdminConsultPage from './pages/AdminConsultPage'
import A11yDemoPage from './pages/A11yDemoPage'
import { LiveRegionProvider } from './components/shared/LiveRegion'

const router = createBrowserRouter([
  { path: '/', element: <HomePage /> },
  { path: '/database/:baseName', element: <DatabasePage /> },
  { path: '/admin', element: <AdminHomePage /> },
  { path: '/admin/create-import', element: <AdminCreateImportPage /> },
  { path: '/admin/consult', element: <AdminConsultPage /> },
  { path: '/a11y-demo', element: <A11yDemoPage /> },
])

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <LiveRegionProvider>
      <RouterProvider router={router} />
    </LiveRegionProvider>
  </StrictMode>,
)
