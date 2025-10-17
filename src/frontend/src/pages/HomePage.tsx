import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import BaseLayout from "./BaseLayout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useLiveRegion } from "@/components/shared/LiveRegion";

export default function HomePage() {
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
    announce('Accueil GenEWeb ouvert');
  }, [announce]);
  return (
    <BaseLayout title="GenEWeb Server">
      {/* Header avec logo et titre */}
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
        <div className="text-center">
          <h1 className="text-3xl font-semibold mb-1">Serveur Généalogique</h1>
          <p className="text-muted-foreground">Base de données généalogiques en ligne</p>
        </div>
      </div>

      {/* Section des bases de données */}
      <div className="flex justify-center mb-6">
        <div className="w-full max-w-6xl">
          <Card className="border-0 shadow-sm" role="region" aria-labelledby="bases-heading">
            <CardHeader className="bg-primary text-primary-foreground rounded-t-lg">
              <CardTitle className="flex items-center gap-2" id="bases-heading">
                <span className="i-fa6-solid:database" />
                Bases de données disponibles
              </CardTitle>
            </CardHeader>
            <CardContent className="p-4">
              {loading ? (
                <div className="text-center py-10" role="status" aria-live="polite">
                  <div className="text-blue-500 text-3xl mb-2">⏳</div>
                  <h4 className="text-muted-foreground">Chargement des bases de données...</h4>
                </div>
              ) : error ? (
                <div className="text-center py-10" role="alert">
                  <div className="text-red-500 text-3xl mb-2">❌</div>
                  <h4 className="text-muted-foreground">Erreur de connexion</h4>
                  <p className="text-muted-foreground text-sm">{error}</p>
                  <Button
                    className="mt-2"
                    onClick={() => window.location.reload()}
                    aria-label="Réessayer de charger les bases"
                  >
                    Réessayer
                  </Button>
                </div>
              ) : databases.length > 0 ? (
                <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3" role="list">
                  {databases.map((db) => (
                    <div key={db} role="listitem">
                      <Link to={`/database/${db}`} className="block" aria-label={`Ouvrir la base ${db}`}>
                        <Card className="h-full hover:opacity-90 transition">
                          <CardContent className="p-6 text-center">
                            <div className="text-green-500 text-2xl mb-2" aria-hidden="true">🌳</div>
                            <div className="font-medium">{db}</div>
                            <div className="text-muted-foreground text-xs">Cliquez pour accéder</div>
                          </CardContent>
                        </Card>
                      </Link>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-10">
                  <div className="text-yellow-400 text-3xl mb-2">⚠️</div>
                  <h4 className="text-muted-foreground">Aucune base de données trouvée</h4>
                  <p className="text-muted-foreground text-sm">Placez vos fichiers .pickle dans le répertoire des bases.</p>
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
              <h2 id="server-info-heading" className="font-medium mb-3">Informations du serveur</h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-center">
                <div>
                  <div className="text-2xl">🔌</div>
                  <div className="text-sm opacity-90">Port</div>
                  <strong>2317</strong>
                </div>
                <div>
                  <div className="text-2xl">📁</div>
                  <div className="text-sm opacity-90">Bases</div>
                  <div className="text-xs text-muted-foreground">{databases.length} disponible{databases.length !== 1 ? 's' : ''}</div>
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

      {/* Outils */}
      <div className="flex justify-center">
        <div className="w-full max-w-3xl">
          <Card className="border-0 shadow-sm" role="region" aria-labelledby="tools-heading">
            <CardHeader className="bg-secondary text-secondary-foreground rounded-t-lg">
              <CardTitle className="text-base" id="tools-heading">Outils</CardTitle>
            </CardHeader>
            <CardContent className="p-4">
              <div className="flex flex-wrap justify-center gap-2">
                <Button variant="outline" asChild>
                  <a href="/admin" title="Administration" aria-label="Ouvrir l'administration">⚙️ Administration</a>
                </Button>
                <Button variant="outline" onClick={() => alert('Fonctionnalité en développement')}>
                  <span aria-hidden="true">📊</span> <span className="sr-only">Afficher</span> Statistiques globales
                </Button>
                <Button variant="outline" onClick={() => alert('Documentation disponible sur GitHub')}>
                  <span aria-hidden="true">❓</span> <span className="sr-only">Ouvrir</span> Aide
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </BaseLayout>
  )
}
