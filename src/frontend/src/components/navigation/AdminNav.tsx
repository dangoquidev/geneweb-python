import { Shield, Home, FileUp, Search, Settings, BarChart3 } from 'lucide-react'
import { Link } from '../Router'
import { useTranslation } from 'react-i18next'

type AdminNavProps = {
  currentPath?: string
}

/**
 * Navigation pour le panel d'administration
 */
export default function AdminNav({ currentPath }: AdminNavProps) {
  const { t } = useTranslation('common')
  const navItems = [
    {
      path: '/admin',
      icon: Home,
      label: t('home.welcome'),
      description: ''
    },
    {
      path: '/admin/create-import',
      icon: FileUp,
      label: t('admin.create_import'),
      description: ''
    },
    {
      path: '/admin/consult',
      icon: Search,
      label: t('admin.consult'),
      description: ''
    },
    {
      path: '/admin/settings',
      icon: Settings,
      label: 'Settings',
      description: ''
    },
    {
      path: '/admin/statistics',
      icon: BarChart3,
      label: t('database.statistics'),
      description: ''
    }
  ]

  const isActive = (path: string) => {
    return currentPath === path || (currentPath?.startsWith(path) && path !== '/admin')
  }

  return (
    <nav className="bg-card border border-border rounded-lg p-4">
      <div className="flex items-center gap-2 mb-4 pb-4 border-b border-border">
        <Shield className="h-5 w-5 text-primary" />
        <h2 className="font-semibold">{t('admin.admin')}</h2>
      </div>

      <div className="space-y-1">
        {navItems.map((item) => (
          <Link
            key={item.path}
            to={item.path}
            className={`flex items-center gap-3 p-3 rounded-lg transition-colors ${
              isActive(item.path)
                ? 'bg-primary text-primary-foreground'
                : 'hover:bg-muted text-muted-foreground hover:text-foreground'
            }`}
          >
            <item.icon className="h-4 w-4 flex-shrink-0" />
            <div className="flex-1 min-w-0">
              <div className="font-medium text-sm">{item.label}</div>
              <div className={`text-xs ${
                isActive(item.path)
                  ? 'text-primary-foreground/80'
                  : 'text-muted-foreground'
              }`}>
                {item.description}
              </div>
            </div>
          </Link>
        ))}
      </div>

      <div className="mt-6 pt-4 border-t border-border">
        <Link
          to="/"
          className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors"
        >
          ← {t('admin.back_to_bases')}
        </Link>
      </div>
    </nav>
  )
}
