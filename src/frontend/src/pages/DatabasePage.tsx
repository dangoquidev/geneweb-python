import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import BaseLayout from "./BaseLayout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";

type DatabaseInfo = {
  base_name: string
  persons: number
  families: number
  path: string
  version: string
}

type SearchResult = {
  id: string
  first_name: string
  surname: string
  occupation: string
  sex: string
  birth_date: string
  death_date: string
}

export default function DatabasePage() {
  const { baseName } = useParams<{ baseName: string }>();
  const [dbInfo, setDbInfo] = useState<DatabaseInfo | null>(null);
  
  // Search form fields
  const [globalSearch, setGlobalSearch] = useState("");
  const [firstName, setFirstName] = useState("");
  const [surname, setSurname] = useState("");
  const [title, setTitle] = useState("");
  const [field, setField] = useState("");
  
  // Search options
  const [oneFirstName, setOneFirstName] = useState(false);
  const [sameOrder, setSameOrder] = useState(false);
  const [partial, setPartial] = useState(false);
  
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [searching, setSearching] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!baseName) return;
    
    fetch(`/api/${baseName}/info`)
      .then(response => {
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
      })
      .then(data => {
        setDbInfo(data);
        setLoading(false);
      })
      .catch(err => {
        console.error('Error fetching database info:', err);
        setError(err.message);
        setLoading(false);
      });
  }, [baseName]);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!baseName) return;

    // Build search query from all fields
    const searchTerms = [];
    if (globalSearch.trim()) searchTerms.push(globalSearch.trim());
    if (firstName.trim()) searchTerms.push(firstName.trim());
    if (surname.trim()) searchTerms.push(surname.trim());
    if (title.trim()) searchTerms.push(title.trim());
    if (field.trim()) searchTerms.push(field.trim());
    
    if (searchTerms.length === 0) return;

    const query = searchTerms.join(' ');
    
    setSearching(true);
    try {
      const response = await fetch(`/api/${baseName}/search?q=${encodeURIComponent(query)}`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setSearchResults(data.results || []);
    } catch (err) {
      console.error('Error searching:', err);
      setError(err instanceof Error ? err.message : 'Search failed');
    } finally {
      setSearching(false);
    }
  };

  const clearSearch = () => {
    setGlobalSearch("");
    setFirstName("");
    setSurname("");
    setTitle("");
    setField("");
    setSearchResults([]);
  };

  if (loading) {
    return (
      <BaseLayout title="GenEWeb - Chargement...">
        <div className="flex justify-center items-center min-h-[400px]">
          <div className="text-center">
            <div className="text-4xl mb-4">⏳</div>
            <h2 className="text-xl">Chargement de la base de données...</h2>
          </div>
        </div>
      </BaseLayout>
    );
  }

  if (error || !dbInfo) {
    return (
      <BaseLayout title="GenEWeb - Erreur">
        <div className="flex justify-center items-center min-h-[400px]">
          <div className="text-center">
            <div className="text-4xl mb-4">❌</div>
            <h2 className="text-xl mb-2">Erreur de chargement</h2>
            <p className="text-muted-foreground mb-4">{error || 'Base de données introuvable'}</p>
            <Button asChild>
              <Link to="/">Retour à l'accueil</Link>
            </Button>
          </div>
        </div>
      </BaseLayout>
    );
  }

  return (
    <BaseLayout
      title={`${baseName} - GenEWeb`}
      showNavbar
      navbarItems={
        <div className="flex items-center gap-4">
          <span className="text-sm opacity-90">{baseName}</span>
          <Link className="text-sm opacity-90 hover:opacity-100" to="/">Accueil</Link>
        </div>
      }
    >
      {/* En-tête */}
      <div className="flex justify-center mb-6">
        <div className="w-full max-w-6xl text-center">
          <h1 className="text-3xl font-semibold mb-1 flex items-center justify-center gap-2">
            🌳 Base {baseName}
          </h1>
          <p className="text-muted-foreground">Base de données généalogique</p>
        </div>
      </div>

      {/* Statistiques */}
      <div className="flex justify-center mb-6">
        <div className="w-full max-w-3xl">
          <Card>
            <CardHeader className="border-b border-border">
              <CardTitle className="text-center">📊 Informations sur la base</CardTitle>
            </CardHeader>
            <CardContent className="p-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-center">
                <div>
                  <div className="text-2xl mb-2">👥</div>
                  <h4 className="text-xl font-bold">{dbInfo.persons.toLocaleString()}</h4>
                  <small className="text-muted-foreground">{dbInfo.persons === 1 ? 'Personne' : 'Personnes'}</small>
                </div>
                <div>
                  <div className="text-2xl mb-2">❤️</div>
                  <h4 className="text-xl font-bold">{dbInfo.families.toLocaleString()}</h4>
                  <small className="text-muted-foreground">{dbInfo.families === 1 ? 'Famille' : 'Familles'}</small>
                </div>
              </div>
              <div className="mt-4 text-sm space-y-1">
                <div><strong>Chemin:</strong> <code className="text-xs">{dbInfo.path}</code></div>
                <div><strong>Version:</strong> {dbInfo.version}</div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Recherche */}
      <div className="flex justify-center mb-6">
        <div className="w-full max-w-5xl">
          <Card>
            <CardHeader className="border-b border-border">
              <CardTitle className="text-center">🔍 Recherche avancée dans la base</CardTitle>
            </CardHeader>
            <CardContent className="p-6">
              <form onSubmit={handleSearch} className="space-y-4">
                {/* Global search field */}
                <div>
                  <label className="block text-sm font-medium mb-2">
                    Recherche globale (individu, nom, nom public, alias, clé)
                  </label>
                  <Input
                    type="search"
                    placeholder="Recherche dans tous les champs..."
                    value={globalSearch}
                    onChange={(e) => setGlobalSearch(e.target.value)}
                    autoFocus
                  />
                </div>

                {/* Name fields */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-2">Prénom</label>
                    <Input
                      type="text"
                      placeholder="Prénom(s)"
                      value={firstName}
                      onChange={(e) => setFirstName(e.target.value)}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-2">Nom de famille</label>
                    <Input
                      type="text"
                      placeholder="Nom de famille"
                      value={surname}
                      onChange={(e) => setSurname(e.target.value)}
                    />
                  </div>
                </div>

                {/* Title and field */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-2">Titre</label>
                    <Input
                      type="text"
                      placeholder="Titre (M., Mme, Dr...)"
                      value={title}
                      onChange={(e) => setTitle(e.target.value)}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-2">Domaine</label>
                    <Input
                      type="text"
                      placeholder="Profession, domaine..."
                      value={field}
                      onChange={(e) => setField(e.target.value)}
                    />
                  </div>
                </div>

                {/* Search options */}
                <div className="border-t pt-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="space-y-3">
                      <h4 className="text-sm font-medium">Options de recherche</h4>
                      <div className="space-y-2">
                        <label className="flex items-center space-x-2 cursor-pointer">
                          <Checkbox
                            checked={oneFirstName}
                            onCheckedChange={(checked) => setOneFirstName(checked === true)}
                          />
                          <span className="text-sm">Un seul prénom</span>
                        </label>
                        <label className="flex items-center space-x-2 cursor-pointer">
                          <Checkbox
                            checked={sameOrder}
                            onCheckedChange={(checked) => setSameOrder(checked === true)}
                          />
                          <span className="text-sm">Même ordre</span>
                        </label>
                        <label className="flex items-center space-x-2 cursor-pointer">
                          <Checkbox
                            checked={partial}
                            onCheckedChange={(checked) => setPartial(checked === true)}
                          />
                          <span className="text-sm">Recherche partielle</span>
                        </label>
                      </div>
                    </div>
                    <div className="flex flex-col justify-end space-y-2">
                      <Button type="submit" disabled={searching} className="w-full">
                        {searching ? "Recherche en cours..." : "🔍 Rechercher"}
                      </Button>
                      <Button type="button" variant="outline" onClick={clearSearch} className="w-full">
                        🗑️ Effacer
                      </Button>
                    </div>
                  </div>
                </div>

                <div className="text-center text-xs text-muted-foreground">
                  Remplissez un ou plusieurs champs pour effectuer une recherche
                </div>
              </form>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Résultats de recherche */}
      {searchResults.length > 0 && (
        <div className="flex justify-center mb-6">
          <div className="w-full max-w-5xl">
            <Card>
              <CardHeader className="border-b border-border">
                <CardTitle className="text-center">
                  📋 Résultats de recherche ({searchResults.length})
                </CardTitle>
                <div className="text-center text-sm text-muted-foreground">
                  {searchResults.length >= 50 && "Seuls les 50 premiers résultats sont affichés"}
                </div>
              </CardHeader>
              <CardContent className="p-4">
                <div className="space-y-3">
                  {searchResults.map(person => (
                    <Card key={person.id} className="border-l-4 border-l-primary hover:shadow-md transition-shadow">
                      <CardContent className="p-4">
                        <div className="flex items-start justify-between">
                          <div className="flex items-start gap-3 flex-1">
                            <Badge variant={person.sex === 'M' ? 'default' : 'destructive'} className="mt-0.5">
                              {person.sex === 'M' ? '♂️' : '♀️'}
                            </Badge>
                            <div className="flex-1">
                              <h5 className="font-semibold text-lg mb-1">
                                {person.first_name} {person.surname}
                              </h5>
                              
                              <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-sm text-muted-foreground">
                                {person.birth_date && (
                                  <div className="flex items-center gap-1">
                                    <span>🎂</span>
                                    <span>Né{person.sex === 'F' ? 'e' : ''} le {person.birth_date}</span>
                                  </div>
                                )}
                                {person.death_date && (
                                  <div className="flex items-center gap-1">
                                    <span>✝️</span>
                                    <span>Décédé{person.sex === 'F' ? 'e' : ''} le {person.death_date}</span>
                                  </div>
                                )}
                                {person.occupation && (
                                  <div className="flex items-center gap-1 md:col-span-2">
                                    <span>💼</span>
                                    <span>{person.occupation}</span>
                                  </div>
                                )}
                              </div>
                            </div>
                          </div>
                          <div className="text-right">
                            <div className="text-xs text-muted-foreground mb-2">ID: {person.id}</div>
                            <Button size="sm" variant="outline" disabled>
                              👁️ Voir la fiche
                            </Button>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
                
                {searchResults.length >= 50 && (
                  <div className="mt-4 p-3 bg-blue-50 dark:bg-blue-950/20 rounded-lg text-center text-sm">
                    <div className="text-blue-700 dark:text-blue-300">
                      ℹ️ Seuls les 50 premiers résultats sont affichés. Affinez votre recherche pour des résultats plus précis.
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      )}

      {/* Message si pas de résultats après recherche */}
      {searchResults.length === 0 && searching === false && (globalSearch || firstName || surname || title || field) && (
        <div className="flex justify-center mb-6">
          <div className="w-full max-w-3xl">
            <Card>
              <CardContent className="p-8 text-center">
                <div className="text-4xl mb-4">🔍</div>
                <h3 className="text-lg font-medium mb-2">Aucun résultat trouvé</h3>
                <p className="text-muted-foreground mb-4">
                  Votre recherche n'a donné aucun résultat. Essayez de :
                </p>
                <div className="text-sm text-muted-foreground space-y-1">
                  <div>• Vérifier l'orthographe</div>
                  <div>• Utiliser moins de mots-clés</div>
                  <div>• Essayer des variantes du nom</div>
                  <div>• Activer la recherche partielle</div>
                </div>
                <Button className="mt-4" onClick={clearSearch}>
                  🗑️ Nouvelle recherche
                </Button>
              </CardContent>
            </Card>
          </div>
        </div>
      )}

      {/* Outils de navigation */}
      <div className="flex justify-center">
        <div className="w-full max-w-5xl">
          <Card>
            <CardHeader className="border-b border-border">
              <CardTitle className="text-center">🛠️ Outils de navigation</CardTitle>
            </CardHeader>
            <CardContent className="p-6">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-4">
                <Button variant="outline" onClick={clearSearch}>
                  🔍 Nouvelle recherche
                </Button>
                <Button variant="outline" disabled>
                  📊 Statistiques détaillées
                </Button>
                <Button variant="outline" asChild>
                  <Link to="/">🏠 Retour aux bases</Link>
                </Button>
              </div>
              <hr className="my-4 border-border" />
              <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                <Button variant="outline" size="sm" disabled>📅 Calendrier</Button>
                <Button variant="outline" size="sm" disabled>🎂 Anniversaires</Button>
                <Button variant="outline" size="sm" disabled>🗺️ Lieux</Button>
                <Button variant="outline" size="sm" disabled>⚙️ Configuration</Button>
              </div>
              <div className="text-center text-sm text-muted-foreground mt-3">
                Certaines fonctionnalités sont en cours de développement
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </BaseLayout>
  );
}
