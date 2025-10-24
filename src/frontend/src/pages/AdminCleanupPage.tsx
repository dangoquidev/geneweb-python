import AdminToolPage from './AdminToolPage'

/**
 * Page Cleanup - Nettoyage des bases de données
 */
export default function AdminCleanupPage() {
    return (
        <AdminToolPage
            title="Nettoyage"
            description="Nettoyage et optimisation des bases de données"
            toolName="nettoyage"
        />
    )
}
