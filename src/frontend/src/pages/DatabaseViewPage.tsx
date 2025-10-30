import { useState, useEffect } from 'react'
import { Link, useParams } from 'react-router-dom'
import BaseLayout from './BaseLayout'
import { Database, User, Users, Activity, AlertCircle, ArrowLeft } from 'lucide-react'
import { useLiveRegion } from '../components/shared/LiveRegion'
import {
  getDatabaseStatistics,
  listDatabasePersons,
  ApiError,
  type PersonResponse,
  type DatabaseStatisticsResponse
} from '../services/api'

/**
 * Page de consultation d'une base de données GenEWeb
 * Affiche les statistiques et la liste des personnes
 */
export default function DatabaseViewPage() {
  const { databaseName } = useParams<{ databaseName: string }>()
  const [statistics, setStatistics] = useState<DatabaseStatisticsResponse | null>(null)
  const [persons, setPersons] = useState<PersonResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [page, setPage] = useState(0)
  const [hasMore, setHasMore] = useState(true)
  const { announce } = useLiveRegion()

  const ITEMS_PER_PAGE = 50

  useEffect(() => {
    if (!databaseName) return

    const fetchData = async () => {
      try {
        setLoading(true)
        setError(null)
        announce(`Chargement de la base ${databaseName}`)

        // Load statistics
        const stats = await getDatabaseStatistics(databaseName)
        setStatistics(stats)

        // Load first page of persons
        const personsData = await listDatabasePersons(databaseName, 0, ITEMS_PER_PAGE)
        setPersons(personsData)
        setHasMore(personsData.length === ITEMS_PER_PAGE)

        announce(`Base ${databaseName} chargée : ${stats.persons_count} personnes`)
      } catch (err) {
        let errorMsg = 'Erreur lors du chargement de la base'

        if (err instanceof ApiError) {
          errorMsg = err.details?.detail || err.details?.message || err.statusText
        } else if (err instanceof Error) {
          errorMsg = err.message
        }

        setError(errorMsg)
        announce(`Erreur: ${errorMsg}`)
        console.error('Error loading database:', err)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [databaseName])

  const loadMorePersons = async () => {
    if (!databaseName || !hasMore) return

    try {
      const nextPage = page + 1
      const morePersons = await listDatabasePersons(
        databaseName,
        nextPage * ITEMS_PER_PAGE,
        ITEMS_PER_PAGE
      )

      setPersons(prev => [...prev, ...morePersons])
      setPage(nextPage)
      setHasMore(morePersons.length === ITEMS_PER_PAGE)
      announce(`${morePersons.length} personnes supplémentaires chargées`)
    } catch (err) {
      console.error('Error loading more persons:', err)
      announce('Erreur lors du chargement de personnes supplémentaires')
    }
  }

  const formatDate = (date?: { year?: number; month?: number; day?: number }) => {
    if (!date?.year) return '?'
    let result = date.year.toString()
    if (date.month) result = `${date.month}/${result}`
    if (date.day) result = `${date.day}/${result}`
    return result
  }

  const formatLifespan = (person: PersonResponse) => {
    const birth = formatDate(person.birth_date)
    const death = person.death_date ? formatDate(person.death_date) : ''
    if (birth === '?' && !death) return ''
    return `(${birth} - ${death || '...'})`
  }

  return (
    <BaseLayout title={`${databaseName || 'Base'} - GenEWeb`}>
      <div className="space-y-8">
        {/* En-tête avec navigation */}
        <div className="flex items-center gap-4">
          <Link
            to="/admin/consult"
            className="flex items-center gap-2 text-muted-foreground hover:text-foreground transition-colors"
          >
            <ArrowLeft className="h-4 w-4" />
            Retour aux bases
          </Link>
        </div>

        <div className="text-center">
          <div className="flex items-center justify-center gap-3 mb-2">
            <Database className="h-8 w-8 text-primary" aria-hidden="true" />
            <h1 className="text-3xl font-bold">{databaseName}</h1>
          </div>
          <p className="text-muted-foreground">
            Base de données généalogique
          </p>
        </div>

        {/* État de chargement */}
        {loading && (
          <div className="flex items-center justify-center py-12">
            <div className="flex items-center gap-3 text-muted-foreground">
              <Activity className="h-5 w-5 animate-spin" aria-hidden="true" />
              <span>Chargement de la base...</span>
            </div>
          </div>
        )}

        {/* Gestion d'erreur */}
        {error && (
          <div className="mb-6 p-4 bg-destructive/10 border border-destructive/20 rounded-lg">
            <div className="flex items-center gap-2 text-destructive">
              <AlertCircle className="h-5 w-5 flex-shrink-0" aria-hidden="true" />
              <span className="font-medium">Erreur:</span>
              <span>{error}</span>
            </div>
          </div>
        )}

        {/* Statistiques */}
        {!loading && !error && statistics && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-card border border-border rounded-lg p-6">
              <div className="flex items-center gap-3 mb-2">
                <User className="h-5 w-5 text-primary" aria-hidden="true" />
                <h3 className="text-sm font-medium text-muted-foreground">Personnes</h3>
              </div>
              <p className="text-3xl font-bold text-foreground">{statistics.persons_count}</p>
            </div>

            <div className="bg-card border border-border rounded-lg p-6">
              <div className="flex items-center gap-3 mb-2">
                <Users className="h-5 w-5 text-primary" aria-hidden="true" />
                <h3 className="text-sm font-medium text-muted-foreground">Familles</h3>
              </div>
              <p className="text-3xl font-bold text-foreground">{statistics.families_count}</p>
            </div>

            {statistics.oldest_birth_year && (
              <div className="bg-card border border-border rounded-lg p-6">
                <h3 className="text-sm font-medium text-muted-foreground mb-2">Plus ancienne naissance</h3>
                <p className="text-3xl font-bold text-foreground">{statistics.oldest_birth_year}</p>
              </div>
            )}

            {statistics.newest_birth_year && (
              <div className="bg-card border border-border rounded-lg p-6">
                <h3 className="text-sm font-medium text-muted-foreground mb-2">Plus récente naissance</h3>
                <p className="text-3xl font-bold text-foreground">{statistics.newest_birth_year}</p>
              </div>
            )}
          </div>
        )}

        {/* Liste des personnes */}
        {!loading && !error && persons.length > 0 && (
          <div className="bg-card border border-border rounded-lg p-6">
            <h2 className="text-xl font-semibold mb-4">Personnes</h2>

            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="border-b border-border">
                  <tr>
                    <th className="text-left py-3 px-4 font-medium text-muted-foreground">Nom</th>
                    <th className="text-left py-3 px-4 font-medium text-muted-foreground">Prénom</th>
                    <th className="text-left py-3 px-4 font-medium text-muted-foreground">Dates</th>
                    <th className="text-left py-3 px-4 font-medium text-muted-foreground">Lieu de naissance</th>
                    <th className="text-left py-3 px-4 font-medium text-muted-foreground">Occupation</th>
                  </tr>
                </thead>
                <tbody>
                  {persons.map((person) => (
                    <tr
                      key={person.id}
                      className="border-b border-border hover:bg-muted/50 transition-colors"
                    >
                      <td className="py-3 px-4 font-medium">{person.surname}</td>
                      <td className="py-3 px-4">{person.first_name}</td>
                      <td className="py-3 px-4 text-sm text-muted-foreground">
                        {formatLifespan(person)}
                      </td>
                      <td className="py-3 px-4 text-sm">
                        {person.birth_place || '-'}
                      </td>
                      <td className="py-3 px-4 text-sm">
                        {person.occupation || '-'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Bouton "Charger plus" */}
            {hasMore && (
              <div className="mt-6 text-center">
                <button
                  onClick={loadMorePersons}
                  className="bg-primary hover:bg-primary/90 text-primary-foreground px-6 py-2 rounded-md font-medium transition-colors focus:ring-2 focus:ring-primary focus:ring-offset-2"
                >
                  Charger plus de personnes
                </button>
              </div>
            )}

            {/* Info pagination */}
            <div className="mt-4 text-center text-sm text-muted-foreground">
              {persons.length} personne{persons.length > 1 ? 's' : ''} affichée{persons.length > 1 ? 's' : ''}
              {statistics && ` sur ${statistics.persons_count}`}
            </div>
          </div>
        )}

        {/* Aucune personne */}
        {!loading && !error && persons.length === 0 && (
          <div className="text-center py-12 bg-muted/30 border border-border rounded-lg">
            <User className="h-12 w-12 text-muted-foreground mx-auto mb-4" aria-hidden="true" />
            <p className="text-muted-foreground text-lg">Aucune personne dans cette base</p>
          </div>
        )}
      </div>
    </BaseLayout>
  )
}
