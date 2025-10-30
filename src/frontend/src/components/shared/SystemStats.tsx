import { Database, Users, UsersRound, Clock, Activity, TrendingUp } from 'lucide-react'
import { useTranslation } from 'react-i18next'

type StatCardProps = {
  icon: React.ComponentType<{ className?: string }>
  title: string
  value: string | number
  subtitle?: string
  trend?: {
    value: number
    positive: boolean
  }
  color?: 'blue' | 'green' | 'purple' | 'orange' | 'red'
}

type SystemStatsProps = {
  stats: {
    total_databases: number
    total_persons: number
    total_families: number
    uptime: string
    memory_usage?: string
    active_users?: number
  }
  loading?: boolean
}

/**
 * Carte de statistique individuelle - Accessible WCAG 2.2 AA
 */
function StatCard({ icon: Icon, title, value, subtitle, trend, color = 'blue' }: StatCardProps) {
  const colorClasses = {
    blue: 'bg-blue-500/10 text-blue-600',
    green: 'bg-green-500/10 text-green-600',
    purple: 'bg-purple-500/10 text-purple-600',
    orange: 'bg-orange-500/10 text-orange-600',
    red: 'bg-red-500/10 text-red-600'
  }

  const formatValue = (val: string | number) => {
    if (typeof val === 'number') {
      return val.toLocaleString()
    }
    return val
  }

  // Générer un ID unique pour l'association aria-labelledby
  const cardId = `stat-${title.toLowerCase().replace(/\s+/g, '-')}`
  const valueId = `${cardId}-value`
  const titleId = `${cardId}-title`
  const subtitleId = subtitle ? `${cardId}-subtitle` : undefined
  const trendId = trend ? `${cardId}-trend` : undefined

  return (
    <div
      className="bg-card border border-border rounded-lg p-4 hover:shadow-sm transition-shadow focus-within:ring-2 focus-within:ring-ring focus-within:ring-offset-2"
      role="img"
      aria-labelledby={`${titleId} ${valueId} ${subtitleId || ''} ${trendId || ''}`.trim()}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div
            className={`p-2 rounded-lg ${colorClasses[color]}`}
            aria-hidden="true"
          >
            <Icon className="h-5 w-5" />
          </div>
          <div>
            <div
              id={valueId}
              className="text-2xl font-bold"
              aria-label={`${formatValue(value)} ${title.toLowerCase()}`}
            >
              {formatValue(value)}
            </div>
            <div
              id={titleId}
              className="text-sm text-muted-foreground"
            >
              {title}
            </div>
            {subtitle && (
              <div
                id={subtitleId}
                className="text-xs text-muted-foreground mt-1"
              >
                {subtitle}
              </div>
            )}
          </div>
        </div>

        {trend && (
          <div
            id={trendId}
            className={`text-sm font-medium ${
              trend.positive ? 'text-green-600' : 'text-red-600'
            }`}
            aria-label={`Tendance: ${trend.positive ? 'hausse' : 'baisse'} de ${Math.abs(trend.value)} pourcent`}
          >
            <TrendingUp
              className={`h-4 w-4 inline mr-1 ${
                trend.positive ? '' : 'rotate-180'
              }`}
              aria-hidden="true"
            />
            <span aria-hidden="true">
              {trend.value > 0 ? '+' : ''}{trend.value}%
            </span>
          </div>
        )}
      </div>
    </div>
  )
}

/**
 * Composant d'affichage des statistiques système
 * Réutilisable dans différentes pages admin - Conforme WCAG 2.2 AA
 */
export default function SystemStats({ stats, loading = false }: SystemStatsProps) {
  const { t } = useTranslation('common')
  if (loading) {
    return (
      <section
        aria-label={t('admin.system_stats_loading')}
        aria-live="polite"
        aria-busy="true"
      >
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {[...Array(4)].map((_, i) => (
            <div
              key={i}
              className="bg-card border border-border rounded-lg p-4 animate-pulse"
              aria-label={`${t('admin.loading_stats')}`}
            >
              <div className="flex items-center gap-3">
                <div className="bg-muted rounded-lg w-9 h-9" aria-hidden="true"></div>
                <div className="flex-1">
                  <div className="bg-muted h-6 rounded mb-2" aria-hidden="true"></div>
                  <div className="bg-muted h-4 rounded w-2/3" aria-hidden="true"></div>
                </div>
              </div>
            </div>
          ))}
        </div>
        <div className="sr-only">{t('admin.system_stats_loading')}</div>
      </section>
    )
  }

  return (
    <section
      aria-label={t('admin.system_stats')}
      aria-live="polite"
      role="region"
    >
      <h2 className="sr-only">{t('admin.system_stats')}</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          icon={Database}
          title={t('admin.databases')}
          value={stats.total_databases}
          color="blue"
        />

        <StatCard
          icon={Users}
          title="Persons"
          value={stats.total_persons}
          color="green"
        />

        <StatCard
          icon={UsersRound}
          title="Families"
          value={stats.total_families}
          color="purple"
        />

        <StatCard
          icon={Clock}
          title="Uptime"
          value={stats.uptime}
          subtitle={stats.memory_usage ? `Memory: ${stats.memory_usage}` : undefined}
          color="orange"
        />

        {stats.active_users !== undefined && (
          <StatCard
            icon={Activity}
            title="Active users"
            value={stats.active_users}
            color="green"
          />
        )}
      </div>
    </section>
  )
}
