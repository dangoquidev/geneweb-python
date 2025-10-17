import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import BaseLayout from "./BaseLayout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useLiveRegion } from "@/components/shared/LiveRegion";
import { useTranslation } from 'react-i18next'
import { Input } from "@/components/ui/input";
import { Checkbox } from "@/components/ui/checkbox";

export default function HomePage() {
  const { t } = useTranslation('common')
  const [databases, setDatabases] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { announce } = useLiveRegion();

  useEffect(() => {
    fetch('/api/databases')
      .then(response => {
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
      })
      .then(data => {
        setDatabases(data.databases || []);
        setLoading(false);
      })
      .catch(err => {
        console.error('Error fetching databases:', err);
        setError(err.message);
        setLoading(false);
      });
  }, []);

  // Announce page on mount
  useEffect(() => {
    announce(t('home.welcome'));
  }, [announce, t]);
  return (
    <BaseLayout title={t('app.title')}>
      {/* Header */}
      <div className="grid md:grid-cols-3 items-center py-6 gap-4">
        <div className="text-center">
          <svg className="mx-auto h-24 w-40" viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg" aria-hidden="true" focusable="false">
            <g fill="#2f6400">
              <circle cx="100" cy="20" r="8" />
              <line x1="100" y1="28" x2="100" y2="50" stroke="#2f6400" strokeWidth="2" />
              <line x1="70" y1="50" x2="130" y2="50" stroke="#2f6400" strokeWidth="2" />
              <circle cx="70" cy="50" r="6" />
              <circle cx="130" cy="50" r="6" />
              <line x1="70" y1="56" x2="70" y2="75" stroke="#2f6400" strokeWidth="1.5" />
              <line x1="130" y1="56" x2="130" y2="75" stroke="#2f6400" strokeWidth="1.5" />
              <line x1="50" y1="75" x2="90" y2="75" stroke="#2f6400" strokeWidth="1.5" />
              <line x1="110" y1="75" x2="150" y2="75" stroke="#2f6400" strokeWidth="1.5" />
              <circle cx="50" cy="75" r="4" />
              <circle cx="90" cy="75" r="4" />
              <circle cx="110" cy="75" r="4" />
              <circle cx="150" cy="75" r="4" />
              <path d="M40,85 Q45,95 50,85" fill="#4a8c2a" />
              <path d="M85,85 Q90,95 95,85" fill="#4a8c2a" />
              <path d="M105,85 Q110,95 115,85" fill="#4a8c2a" />
              <path d="M145,85 Q150,95 155,85" fill="#4a8c2a" />
            </g>
            <text x="100" y="110" textAnchor="middle" fontFamily="serif" fontSize="16" fontWeight="bold" fill="#2f6400">GeneWeb</text>
          </svg>
        </div>
      </div>

      {/* Search module */}
      <div className="flex justify-center mb-6">
        <div className="w-full max-w-6xl">
          <Card className="border-0 shadow-sm" role="region" aria-labelledby="bases-heading">
            <CardHeader className="bg-primary text-primary-foreground rounded-t-lg">
              <CardTitle className="flex items-center gap-2" id="bases-heading">
                <span className="i-fa6-solid:database" />
                Search
              </CardTitle>
            </CardHeader>
            <CardContent className="p-4">
              {/* Free-form search */}
              <form
                onSubmit={(e) => { e.preventDefault(); alert('Search not implemented'); }}
                className="space-y-4"
              >
                <div>
                  <label className="block text-sm font-medium mb-2" htmlFor="q">Free-form search</label>
                  <Input id="q" placeholder="individual, surname, alias, key" />
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-2" htmlFor="firstName">First name</label>
                    <Input id="firstName" placeholder="First name" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-2" htmlFor="surname">Surname</label>
                    <Input id="surname" placeholder="Surname" />
                  </div>
                </div>
                <div className="flex flex-wrap items-center gap-6">
                  <label className="flex items-center gap-2">
                    <Checkbox id="one-first-name" />
                    <span className="text-sm">One first name</span>
                  </label>
                  <label className="flex items-center gap-2">
                    <Checkbox id="same-order" />
                    <span className="text-sm">Same order</span>
                  </label>
                  <label className="flex items-center gap-2">
                    <Checkbox id="partial" />
                    <span className="text-sm">Partial</span>
                  </label>
                </div>
                <div>
                  <Button type="submit">Search</Button>
                </div>
              </form>

              {/* Existing DB list presentation */}
              {loading ? (
                <div className="text-center py-10" role="status" aria-live="polite">
                  <div className="text-blue-500 text-3xl mb-2">⏳</div>
                  <h4 className="text-muted-foreground">{t('database.loading')}</h4>
                </div>
              ) : error ? (
                <div className="text-center py-10" role="alert">
                  <div className="text-red-500 text-3xl mb-2">❌</div>
                  <h4 className="text-muted-foreground">{t('app.error')}</h4>
                  <p className="text-muted-foreground text-sm">{error}</p>
                  <Button
                    className="mt-2"
                    onClick={() => window.location.reload()}
                    aria-label="Reload"
                  >
                    Reload
                  </Button>
                </div>
              ) : databases.length > 0 ? (
                <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3" role="list">
                  {databases.map((db) => (
                    <div key={db} role="listitem">
                      <Link to={`/database/${db}`} className="block" aria-label={`Open database ${db}`}>
                        <Card className="h-full hover:opacity-90 transition">
                          <CardContent className="p-6 text-center">
                            <div className="text-green-500 text-2xl mb-2" aria-hidden="true">🌳</div>
                            <div className="font-medium">{db}</div>
                            <div className="text-muted-foreground text-xs">Open</div>
                          </CardContent>
                        </Card>
                      </Link>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-10">
                  <div className="text-yellow-400 text-3xl mb-2">⚠️</div>
                  <h4 className="text-muted-foreground">{t('database.no_results')}</h4>
                  <p className="text-muted-foreground text-sm">{t('home.description')}</p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Informations du serveur */}
      <div className="flex justify-center mb-6">
        <div className="w-full max-w-3xl">
          <Card role="region" aria-labelledby="server-info-heading">
            <CardContent className="p-6">
              <h2 id="server-info-heading" className="font-medium mb-3">GenEWeb</h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-center">
                <div>
                  <div className="text-2xl">🔌</div>
                  <div className="text-sm opacity-90">Port</div>
                  <strong>2317</strong>
                </div>
                <div>
                  <div className="text-2xl">📁</div>
                  <div className="text-sm opacity-90">DB</div>
                  <div className="text-xs text-muted-foreground">{databases.length}</div>
                </div>
                <div>
                  <div className="text-2xl">🐍</div>
                  <div className="text-sm opacity-90">Version</div>
                  <div className="text-xs">GenEWeb Python</div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Tools */}
      <div className="flex justify-center mb-6">
        <div className="w-full max-w-3xl">
          <Card className="border-0 shadow-sm" role="region" aria-labelledby="tools-heading">
            <CardHeader className="bg-secondary text-secondary-foreground rounded-t-lg">
              <CardTitle className="text-base" id="tools-heading">{t('tools.title')}</CardTitle>
            </CardHeader>
            <CardContent className="p-4">
              <div className="flex flex-wrap justify-center gap-2">
                <Button variant="outline" onClick={() => alert('Add notes')}>{t('tools.add_notes')}</Button>
                <Button variant="outline" onClick={() => alert('Statistics')}>{t('database.statistics')}</Button>
                <Button variant="outline" onClick={() => alert('Anniversaries')}>{t('tools.anniversaries')}</Button>
                <Button variant="outline" onClick={() => alert('Places/surname')}>{t('tools.places_surname')}</Button>
                <Button variant="outline" onClick={() => alert('Calendars')}>{t('tools.calendars')}</Button>
                <Button variant="outline" onClick={() => alert('Configuration')}>{t('tools.configuration')}</Button>
                <Button variant="outline" onClick={() => alert('Add note')}>{t('tools.add_note')}</Button>
                <Button variant="outline" onClick={() => alert('Add family')}>{t('tools.add_family')}</Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Books section */}
      <div className="flex justify-center">
        <div className="w-full max-w-5xl">
          <Card className="border-0 shadow-sm" role="region" aria-labelledby="books-heading">
            <CardHeader className="bg-muted text-foreground rounded-t-lg">
              <CardTitle className="text-base" id="books-heading">{t('books.title')}</CardTitle>
            </CardHeader>
            <CardContent className="p-4">
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2">
                <Button variant="outline" onClick={() => alert('First names')}>{t('books.first_names')}</Button>
                <Button variant="outline" onClick={() => alert('Surnames')}>{t('books.surnames')}</Button>
                <Button variant="outline" onClick={() => alert('Public names')}>{t('books.public_names')}</Button>
                <Button variant="outline" onClick={() => alert('Qualifiers')}>{t('books.qualifiers')}</Button>
                <Button variant="outline" onClick={() => alert('Aliases')}>{t('books.aliases')}</Button>
                <Button variant="outline" onClick={() => alert('Occupations')}>{t('books.occupations')}</Button>
                <Button variant="outline" onClick={() => alert('Places')}>{t('books.places')}</Button>
                <Button variant="outline" onClick={() => alert('Sources')}>{t('books.sources')}</Button>
                <Button variant="outline" onClick={() => alert('Titles')}>{t('books.titles')}</Button>
                <Button variant="outline" onClick={() => alert('Domains')}>{t('books.domains')}</Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </BaseLayout>
  )
}
