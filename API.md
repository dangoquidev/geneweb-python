# GenEWeb REST API

API REST moderne pour GenEWeb, remplaçant le serveur legacy gwd.

## 🚀 Démarrage rapide

```bash
# Démarrer l'API (recommandé)
make run

# Démarrer avec auto-reload (développement)
make run-dev

# Démarrer avec port/database personnalisés
make run-api
```

L'API sera accessible sur:
- **API**: http://127.0.0.1:8000
- **Documentation Swagger**: http://127.0.0.1:8000/api/docs
- **Documentation ReDoc**: http://127.0.0.1:8000/api/redoc
- **OpenAPI JSON**: http://127.0.0.1:8000/api/openapi.json

## 📚 Endpoints disponibles

### Health & Status
- `GET /api/health` - Health check simple
- `GET /api/status` - Statut détaillé avec compteurs

### Personnes (7 endpoints)
- `GET /api/persons` - Liste avec pagination
- `POST /api/persons` - Créer (auth requis)
- `GET /api/persons/{id}` - Détails d'une personne
- `PUT /api/persons/{id}` - Modifier (auth requis)
- `DELETE /api/persons/{id}` - Supprimer (auth requis)
- `GET /api/persons/{id}/statistics` - Statistiques personnelles
- `GET /api/persons/{id}/duplicates` - Détection de doublons

### Familles (8 endpoints)
- `GET /api/families` - Liste des familles
- `POST /api/families` - Créer (auth requis)
- `GET /api/families/{id}` - Détails d'une famille
- `PUT /api/families/{id}` - Modifier (auth requis)
- `DELETE /api/families/{id}` - Supprimer (auth requis)
- `POST /api/families/{id}/children/{child_id}` - Ajouter un enfant
- `DELETE /api/families/{id}/children/{child_id}` - Retirer un enfant
- `GET /api/families/{id}/statistics` - Statistiques familiales

### Recherche & Généalogie (7 endpoints)
- `GET /api/search/persons` - Recherche avec query params
- `POST /api/search/persons` - Recherche avancée avec filtres
- `GET /api/search/ancestors/{id}` - Arbre d'ancêtres
- `GET /api/search/descendants/{id}` - Arbre de descendants
- `GET /api/search/relatives/{id}` - Tous les proches
- `GET /api/search/relationship/{id1}/{id2}` - Chemin de parenté
- `GET /api/search/statistics` - Statistiques globales

## 🔧 Configuration

### Variables d'environnement

L'API utilise des variables d'environnement pour la configuration:

```bash
export GENEWEB_DATABASE_PATH="data/ma_famille.pickle"
export GENEWEB_DEBUG="true"
```

### Ligne de commande

```bash
python run_api.py --help

Options:
  --host HOST              Host to bind to (default: 127.0.0.1)
  --port PORT              Port to bind to (default: 8000)
  --db DATABASE_PATH       Path to database file (default: data/showcase.pickle)
  --debug                  Enable debug mode with detailed errors
  --reload                 Enable auto-reload on code changes
```

## 🧪 Tests

```bash
# Tous les tests (295 tests)
make test

# Tests API uniquement
PYTHONPATH=src python -m pytest tests/backend_tests/api/ -v

# Tests de migration legacy
PYTHONPATH=src python -m pytest tests/backend_tests/database/test_legacy_migration.py -v
```

## 📊 Compatibilité

### Migration automatique des données legacy

L'API inclut un système de migration automatique pour les bases de données legacy:

- **IDs complexes**: Extrait l'ID depuis des dicts comme `{'id': 'P1', 'name_key': '...'}`
- **Sexe flexible**: Convertit `'Male'`, `'Female'` → enums `Sex.MALE`, `Sex.FEMALE`
- **Dates partielles**: Support des dates incomplètes (year only, etc.)
- **Structures imbriquées**: Migration automatique des objets Date, Family, etc.

### Formats supportés

- **Nouveau format**: Objets Python natifs (Person, Family, Date)
- **Format legacy**: Dictionnaires avec structures complexes
- **Migration transparente**: Chargement automatique sans conversion manuelle

## 🔒 Sécurité

### Authentification (à venir)

Les endpoints de modification (POST, PUT, DELETE) nécessitent une authentification:

```python
# Actuellement: placeholder
headers = {"Authorization": "Bearer <token>"}
```

### CORS

Configuration CORS pour React frontend:

```python
# Mode debug: tous les origins
allow_origins=["*"]

# Mode production: origins spécifiques
allow_origins=["http://localhost:3000", "http://localhost:5173"]
```

## 🐛 Debugging

### Mode debug

```bash
# Active les erreurs détaillées
make run  # debug=True par défaut
```

### Logs

```bash
# Niveau debug
python run_api.py --debug

# Niveau info (production)
python run_api.py
```

## 📖 Documentation interactive

L'API génère automatiquement une documentation interactive:

1. **Swagger UI** (http://127.0.0.1:8000/api/docs)
   - Interface interactive pour tester les endpoints
   - Essayer directement les requêtes
   - Voir les schémas de validation

2. **ReDoc** (http://127.0.0.1:8000/api/redoc)
   - Documentation lisible et élégante
   - Recherche intégrée
   - Exemples de code

3. **OpenAPI JSON** (http://127.0.0.1:8000/api/openapi.json)
   - Schéma complet pour génération de clients
   - Compatible avec des outils comme Postman, Insomnia

## 🚀 Intégration React

### Exemple de client API

```typescript
// api/client.ts
const API_BASE = 'http://127.0.0.1:8000/api';

export async function getPersons(skip = 0, limit = 100) {
  const response = await fetch(`${API_BASE}/persons?skip=${skip}&limit=${limit}`);
  return response.json();
}

export async function searchPersons(query: string) {
  const response = await fetch(`${API_BASE}/search/persons?query=${query}`);
  return response.json();
}

export async function getAncestors(personId: string, maxGenerations = 5) {
  const response = await fetch(
    `${API_BASE}/search/ancestors/${personId}?max_generations=${maxGenerations}`
  );
  return response.json();
}
```

### Hooks React

```typescript
// hooks/usePersons.ts
import { useQuery } from '@tanstack/react-query';
import { getPersons } from '../api/client';

export function usePersons(skip = 0, limit = 100) {
  return useQuery({
    queryKey: ['persons', skip, limit],
    queryFn: () => getPersons(skip, limit)
  });
}
```

## 🔄 Migration depuis gwd legacy

### Différences principales

| Aspect | Legacy (gwd) | Moderne (REST API) |
|--------|-------------|-------------------|
| Port | 2317 | 8000 |
| Format | HTML/Templates | JSON REST |
| Documentation | Manuelle | Auto-générée |
| Frontend | Server-side | React SPA |
| Tests | Manuels | 295 tests automatisés |

### Lancer l'ancien serveur

```bash
# Si besoin de l'ancien serveur
make run-legacy
```

## 📝 TODO

- [ ] Implémenter l'authentification JWT
- [ ] Ajouter rate limiting
- [ ] WebSocket pour notifications temps réel
- [ ] Cache Redis pour performance
- [ ] Pagination cursor-based
- [ ] Filtres avancés (dates, lieux complexes)
- [ ] Export formats multiples (GEDCOM, JSON, CSV)
- [ ] Gestion des médias (photos, documents)

## 🤝 Contribution

Voir [CONTRIBUTING.md](CONTRIBUTING.md) et [CODING_CONVENTIONS.md](docs/CODING_CONVENTIONS.md)

## 📄 Licence

Voir [LICENSE](LICENSE)
