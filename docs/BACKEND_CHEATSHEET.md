# GenEWeb Backend – Cheat Sheet pour créer des routes (FR)

Ce document explique comment fonctionne le backend Python de GenEWeb (structure, conventions, accès DB) et donne une recette claire pour ajouter proprement de nouvelles routes API consommables par le front (React).

## Vue d’ensemble de l’architecture

- **Serveur HTTP**
  - `src/backend/servers/gwd_simple.py` (serveur recommandé pour le front) :
    - Monte l’API moderne sous le préfixe `/api/...`.
    - Utilise des classes d’endpoints modulaires situées dans `src/backend/api/endpoints/`.
    - Sert le front en dev via Vite (proxy) ou en prod (dossier `dist`).
  - `src/backend/geneweb/web/gwd_server.py` et `src/backend/geneweb/web/server.py` :
    - Implémentations plus proches de l’original OCaml (utile pour référence/tests).

- **Endpoints modulaires (API)**
  - Répertoire: `src/backend/api/endpoints/`
    - `database_endpoints.py` — listing des bases, info d’une base.
    - `search_endpoints.py` — recherche personnes (simple/avancée).
    - `statistics_endpoints.py` — statistiques (naissances récentes, pyramide des âges, etc.).
  - Les endpoints sont des classes orientées « handler » qui reçoivent un `BaseHTTPRequestHandler` et écrivent elles-mêmes la réponse JSON.

- **Routing API**
  - Géré dans `src/backend/servers/gwd_simple.py`, méthode `handle_api_request` du handler `GeneWebHTTPHandler`.
  - Routes existantes (GET) :
    - `/api/databases`
    - `/api/{base}/info`
    - `/api/{base}/search` et `/api/{base}/search/advanced`
    - `/api/{base}/statistics/{stat_type}` (ex: `latest-births`, `population-pyramid`, `general-stats`, ...)

- **Accès Base de Données**
  - Driver: `src/backend/geneweb/db/driver.py`
    - `create_database_driver(path, driver_type="pickle")` → `PickleDatabaseDriver`.
    - API du driver: `open_database(read_only=True)`, `close_database()`, `get_persons()`, `get_families()`, `search_persons(q, limit)`, `get_person(id)`, `get_family(id)`, etc.
    - Les types de données (Person, Family, dates, etc.) sont définis dans `src/backend/geneweb/core/definitions.py`.
  - Les données sont chargées depuis des fichiers `.pickle` (ex: `data/ma_famille.pickle`).

## Conventions de code (API)

- **Organisation**
  - Une nouvelle feature API = 1 classe d’endpoint dans `src/backend/api/endpoints/` quand il y a une logique cohérente (ex: `PersonEndpoints`, `FamilyEndpoints`).
  - Chaque méthode de la classe gère une sous-route (ex: `handle_get_person`, `handle_create_person`).

- **I/O HTTP**
  - Le handler se conforme à `http.server.BaseHTTPRequestHandler`.
  - Utilisez une méthode utilitaire privée pour renvoyer du JSON proprement (voir `_send_json_response` existant) :
    - `Content-Type: application/json; charset=utf-8`
    - `Cache-Control: no-store`
    - `Content-Length` correct

- **Erreurs**
  - 404 si base inexistante.
  - 400 pour requête invalide (paramètres manquants/mal formés).
  - 500 pour erreurs internes non prévues.

- **Nommage**
  - Endpoints: noms explicites au singulier/pluriel selon la ressource (`/persons`, `/families`, `/statistics`).
  - Paramètres query: en `snake_case` (`first_name`, `birth_year`, `limit`).
  - Variables Python: `snake_case`. Classes: `PascalCase`.

- **Sécurité / confidentialité**
  - Pour l’instant, pas d’auth obligatoire côté API publique. Si besoin d’auth plus tard, centraliser dans le handler et documenter les headers.

## Ajouter une nouvelle route – Étapes

Exemple: Ajouter `/api/{base}/persons/{id}` (GET) et `/api/{base}/persons` (GET list, filtrage simple)

1) Créer une nouvelle classe d’endpoints

- Fichier: `src/backend/api/endpoints/person_endpoints.py`
- Classe: `PersonEndpoints` avec méthodes:
  - `handle_get_person(handler, base_name: str, person_id: str)`
  - `handle_list_persons(handler, base_name: str, query_string: str)` (supporte `limit`, filtres simples)
- Patterns à copier: regarder `search_endpoints.py` et `database_endpoints.py` pour:
  - Résolution du chemin de base: `os.path.join(database_dir, f"{base_name}.pickle")` puis vérif `os.path.exists`.
  - Ouverture DB: `db = create_database_driver(path, "pickle"); db.open_database(read_only=True)` puis `finally: db.close_database()`.
  - Construction réponse JSON via `_send_json_response`.

2) Exporter la classe dans `src/backend/api/endpoints/__init__.py`

```startLine:endLine:/home/dango/Documents/epitech/tek5/pool/Awkward_legacy/src/backend/api/endpoints/__init__.py
from .database_endpoints import DatabaseEndpoints
from .search_endpoints import SearchEndpoints
from .statistics_endpoints import StatisticsEndpoints
# Ajouter:
# from .person_endpoints import PersonEndpoints
```

3) Brancher le routing dans `gwd_simple.py`

- Ouvrir `src/backend/servers/gwd_simple.py`.
- Dans `GeneWebHTTPHandler.__init__`, instancier votre nouvel endpoint:

```startLine:endLine:/home/dango/Documents/epitech/tek5/pool/Awkward_legacy/src/backend/servers/gwd_simple.py
self.database_endpoints = DatabaseEndpoints(gwd_config.database_dir)
self.search_endpoints = SearchEndpoints(gwd_config.database_dir)
self.statistics_endpoints = StatisticsEndpoints(gwd_config.database_dir)
# Ajouter:
# self.person_endpoints = PersonEndpoints(gwd_config.database_dir)
```

- Dans `handle_api_request`, router les nouvelles routes:

```startLine:endLine:/home/dango/Documents/epitech/tek5/pool/Awkward_legacy/src/backend/servers/gwd_simple.py
# ...
elif action == "persons":
    if len(parts) == 3:
        # GET /api/{base}/persons (liste)
        self.person_endpoints.handle_list_persons(self, base_name, query_string)
        return
    elif len(parts) == 4:
        # GET /api/{base}/persons/{id}
        self.person_endpoints.handle_get_person(self, base_name, parts[3])
        return
# ...
```

4) Implémenter la logique d’accès DB

- Pour `handle_get_person`: `db_driver.get_person(int(person_id))` et formater la réponse (types simples: `str`, `int`, dates via util `geneweb_date_to_string` si utile).
- Pour `handle_list_persons`: parcourir `db_driver.get_persons()`; appliquer filtres (`q`, `sex`, `limit`) et renvoyer une liste normalisée (mêmes clés que `search_endpoints` si possible pour homogénéité front).

5) Réponses JSON – format recommandé

- Toujours renvoyer un objet racine avec:
  - `base`: nom de la base
  - `resource`: nom de la ressource (`"person"`, `"persons"`)
  - `result` ou `results`: objet ou liste
  - `total` et `limit` pour les listes
  - timestamp optionnel `generated_at` pour debug

Exemple minimal succès:

```json
{
  "base": "ma_famille",
  "resource": "person",
  "result": {
    "id": "123",
    "first_name": "Jean",
    "surname": "Dupont",
    "sex": "M",
    "birth_date": "12/03/1940",
    "birth_place": "Paris"
  }
}
```

Exemple liste:

```json
{
  "base": "ma_famille",
  "resource": "persons",
  "query": "jean",
  "results": [
    {"id": "123", "first_name": "Jean", "surname": "Dupont"},
    {"id": "456", "first_name": "Jean-Paul", "surname": "Martin"}
  ],
  "total": 2,
  "limit": 50
}
```

Exemple erreur:

```json
{"error": "Database 'ma_famille' not found"}
```

## Bonnes pratiques

- **Compatibilité front**: réutiliser autant que possible les mêmes clés que `search_endpoints`/`statistics_endpoints` pour simplifier le typage côté front.
- **Dates**: utiliser `_format_date` des endpoints existants ou `geneweb_date_to_string` pour rendre une string stable.
- **Logs**: utilisez `logging.getLogger("geneweb.api.<feature>")` dans votre classe pour tracer les erreurs.
- **Performances**: gardez `limit` par défaut raisonnable (50 ou 100). Pour des scans complets (statistiques), paginez si nécessaire.
- **Lisibilité**: fonctions courtes, division claire entre parsing des inputs, accès DB, mapping modèle→DTO, réponse.

## Exemples curl (dev)

- Lister les bases:
```bash
curl -s http://localhost:2317/api/databases | jq
```

- Info base:
```bash
curl -s http://localhost:2317/api/ma_famille/info | jq
```

- Recherche simple:
```bash
curl -s "http://localhost:2317/api/ma_famille/search?q=dupont&limit=20" | jq
```

- Recherche avancée:
```bash
curl -s "http://localhost:2317/api/ma_famille/search/advanced?first_name=jean&surname=dupont&birth_year=1940" | jq
```

- Statistiques (exemples):
```bash
curl -s "http://localhost:2317/api/ma_famille/statistics/latest-births?limit=10" | jq
curl -s "http://localhost:2317/api/ma_famille/statistics/general-stats" | jq
```

- (Après ajout) Personne par id:
```bash
curl -s http://localhost:2317/api/ma_famille/persons/123 | jq
```

## Où mettre les fichiers et comment nommer

- Nouveau domaine fonctionnel: fichier `src/backend/api/endpoints/<domaine>_endpoints.py`.
- Classe `PascalCase` nommée `<Domaine>Endpoints` avec méthodes `handle_*`.
- Routing: ajouter dans `gwd_simple.py` → `handle_api_request` + instanciation dans `__init__`.
- Exports: ajouter dans `src/backend/api/endpoints/__init__.py`.

## Checklist rapide (PR prête)

- Classe endpoint créée et testée localement.
- Routing branché dans `gwd_simple.py` (instanciation + routes).
- Réponses JSON avec headers corrects et champs `results/total/limit` pour les listes.
- Gestion des erreurs (404/400/500) propre.
- Exemples `curl` valides dans la description PR.
- Noms cohérents avec les endpoints existants.
