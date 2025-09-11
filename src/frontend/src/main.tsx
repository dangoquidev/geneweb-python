import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { createBrowserRouter, RouterProvider } from 'react-router-dom'
import './index.css'
import HomePage from './pages/HomePage'
import DatabasePage from './pages/DatabasePage'

const router = createBrowserRouter([
  { path: '/', element: <HomePage /> },
  { path: '/database/:baseName', element: <DatabasePage /> },
])

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <RouterProvider router={router} />
  </StrictMode>,
)
