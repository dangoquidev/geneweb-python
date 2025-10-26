# Solution : Consultation des Bases de Données

## 🎯 Problème

Le frontend affichait la liste des bases de données mais ne permettait pas de les consulter. Les liens pointaient vers des URLs `/{base_name}` qui n'existaient pas car :

1. **Architecture héritée** : GenEWeb OCaml utilisait un serveur `gwd` séparé pour servir les bases
2. **API incomplète** : L'API REST moderne avait des routes pour gérer les données mais pas pour consulter des bases spécifiques
3. **Routes manquantes** : Pas de mécanisme pour charger dynamiquement une base et accéder à son contenu

## ✅ Solution Implémentée

### Backend : Nouvelles Routes API

#### 1. Routes de Consultation par Base

**Fichier** : `src/backend/api/routes/database_persons.py`

Routes ajoutées :
- `GET /api/databases/{database_name}/persons` - Liste les personnes d'une base
- `GET /api/databases/{database_name}/persons/{person_id}` - Détails d'une personne
- `GET /api/databases/{database_name}/statistics` - Statistiques de la base

**Fichier** : `src/backend/api/routes/database_families.py`

Routes ajoutées :
- `GET /api/databases/{database_name}/families` - Liste les familles d'une base
- `GET /api/databases/{database_name}/families/{family_id}` - Détails d'une famille

#### 2. Chargement Dynamique des Bases

```python
def get_database_driver(database_name: str, service: DatabaseService) -> PickleDriver:
    """Charge dynamiquement une base de données par son nom."""
    if not service.database_exists(database_name):
        raise HTTPException(status_code=404, detail=f"Database '{database_name}' not found")

    db_path = service.get_database_path(database_name)
    driver = PickleDriver(db_path)
    driver.load()
    driver.repository = Repository(driver)  # Attache un repository
    return driver
```

#### 3. Intégration dans l'App

**Fichier** : `src/backend/api/app.py`

```python
# Nouvelles routes enregistrées
app.include_router(database_persons.router, prefix="/api", tags=["Database Consultation"])
app.include_router(database_families.router, prefix="/api", tags=["Database Consultation"])
```

### Frontend : Page de Consultation

#### 1. Nouvelle Page DatabaseViewPage

**Fichier** : `src/frontend/src/pages/DatabaseViewPage.tsx`

Fonctionnalités :
- ✅ Affiche les statistiques de la base (nombre de personnes, familles, années)
- ✅ Liste paginée des personnes avec leurs informations
- ✅ Bouton "Charger plus" pour la pagination
- ✅ Navigation vers la liste des bases
- ✅ Gestion des erreurs et états de chargement

#### 2. Mise à Jour de AdminConsultPage

**Changement** : Les liens pointent maintenant vers `/admin/databases/{databaseName}` au lieu de `/{databaseName}`

```tsx
// AVANT
url: `/${name}`  // Pointait vers gwd (inexistant)

// APRÈS
url: `/admin/databases/${encodeURIComponent(name)}`  // Pointe vers notre page
```

#### 3. Nouvelles Fonctions API

**Fichier** : `src/frontend/src/services/api.ts`

Fonctions ajoutées :
```typescript
listDatabasePersons(databaseName, skip, limit) → PersonResponse[]
getDatabasePerson(databaseName, personId) → PersonResponse
listDatabaseFamilies(databaseName, skip, limit) → FamilyResponse[]
getDatabaseFamily(databaseName, familyId) → FamilyResponse
getDatabaseStatistics(databaseName) → DatabaseStatisticsResponse
```

#### 4. Routing

**Fichier** : `src/frontend/src/main.tsx`

```tsx
{ path: '/admin/databases/:databaseName', element: <DatabaseViewPage /> }
```

## 📊 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        FRONTEND                              │
├─────────────────────────────────────────────────────────────┤
│  AdminConsultPage.tsx                                        │
│  ├─ Liste les bases disponibles                             │
│  └─ Liens vers → /admin/databases/{name}                    │
│                                                              │
│  DatabaseViewPage.tsx                                        │
│  ├─ Affiche statistiques de la base                         │
│  ├─ Liste les personnes (paginée)                           │
│  └─ Bouton "Charger plus"                                   │
└─────────────────────────────────────────────────────────────┘
                            ↕ HTTP
┌─────────────────────────────────────────────────────────────┐
│                        BACKEND API                           │
├─────────────────────────────────────────────────────────────┤
│  Routes Existantes (base par défaut)                        │
│  ├─ GET /api/persons                                        │
│  ├─ GET /api/families                                       │
│  └─ GET /api/databases                                      │
│                                                              │
│  Nouvelles Routes (base dynamique) ✨                       │
│  ├─ GET /api/databases/{name}/persons                       │
│  ├─ GET /api/databases/{name}/persons/{id}                  │
│  ├─ GET /api/databases/{name}/families                      │
│  ├─ GET /api/databases/{name}/families/{id}                 │
│  └─ GET /api/databases/{name}/statistics                    │
└─────────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────────┐
│                    DATABASE LAYER                            │
├─────────────────────────────────────────────────────────────┤
│  DatabaseService                                             │
│  ├─ get_database_path(name) → Path                          │
│  ├─ database_exists(name) → bool                            │
│  └─ list_databases() → List[str]                            │
│                                                              │
│  PickleDriver + Repository                                   │
│  └─ Chargement dynamique de la base                         │
└─────────────────────────────────────────────────────────────┘
```

## 🧪 Tests Effectués

### Backend

```bash
# Liste des bases
curl http://127.0.0.1:8000/api/databases
# ✅ {"databases": ["test", "test-family", ...], "count": 9}

# Personnes d'une base
curl "http://127.0.0.1:8000/api/databases/test/persons?limit=3"
# ✅ [{"id": "I1", "first_name": "John", "surname": "Doe"}, ...]

# Statistiques d'une base
curl http://127.0.0.1:8000/api/databases/test/statistics
# ✅ {"database_name": "test", "persons_count": 5, "families_count": 2, ...}
```

### Frontend

1. ✅ Page `/admin/consult` affiche la liste des bases
2. ✅ Clic sur "Consulter" → navigation vers `/admin/databases/test`
3. ✅ Page DatabaseViewPage affiche les statistiques et la liste des personnes
4. ✅ Pagination fonctionne avec le bouton "Charger plus"

## 🎨 Expérience Utilisateur

### Avant
- ❌ Liste des bases visible
- ❌ Liens vers `/{base}` → 404 (route inexistante)
- ❌ Impossible de voir le contenu d'une base

### Après
- ✅ Liste des bases visible
- ✅ Liens vers `/admin/databases/{base}` → Page fonctionnelle
- ✅ Statistiques de la base affichées
- ✅ Liste des personnes avec pagination
- ✅ Informations : nom, prénom, dates, lieu, occupation
- ✅ Indicateur de chargement et gestion d'erreurs

## 📁 Fichiers Créés/Modifiés

### Backend
- ✨ **Créé** : `src/backend/api/routes/database_persons.py`
- ✨ **Créé** : `src/backend/api/routes/database_families.py`
- 📝 **Modifié** : `src/backend/api/app.py` (ajout des routes)

### Frontend
- ✨ **Créé** : `src/frontend/src/pages/DatabaseViewPage.tsx`
- 📝 **Modifié** : `src/frontend/src/pages/AdminConsultPage.tsx` (URLs corrigées)
- 📝 **Modifié** : `src/frontend/src/services/api.ts` (nouvelles fonctions)
- 📝 **Modifié** : `src/frontend/src/main.tsx` (ajout de la route)

## 🚀 Pour Aller Plus Loin

### Améliorations Possibles

1. **Recherche dans une base**
   ```typescript
   GET /api/databases/{name}/search?q=Martin
   ```

2. **Vue détaillée d'une personne**
   ```typescript
   // Page : /admin/databases/{name}/persons/{id}
   // Affiche : informations complètes, famille, événements, etc.
   ```

3. **Arbre généalogique**
   ```typescript
   GET /api/databases/{name}/persons/{id}/tree?generations=3
   ```

4. **Export filtré**
   ```typescript
   GET /api/databases/{name}/export/gedcom?persons=I1,I2,I3
   ```

5. **Statistiques avancées**
   - Répartition géographique
   - Distribution des naissances par siècle
   - Professions les plus courantes

## 🔐 Sécurité

**Note** : Les routes de consultation sont actuellement publiques. Pour une production, considérez :

```python
@router.get("/databases/{database_name}/persons")
async def list_database_persons(
    database_name: str,
    user: dict = Depends(require_auth),  # ← Authentification
    ...
):
    # Vérifier les permissions d'accès à cette base
    if not has_permission(user, database_name):
        raise HTTPException(403, "Access denied")
    ...
```

## 📚 Documentation API

Les nouvelles routes sont automatiquement documentées dans Swagger :
- **Swagger UI** : http://127.0.0.1:8000/api/docs
- **ReDoc** : http://127.0.0.1:8000/api/redoc

Recherchez le tag **"Database Consultation"** dans la documentation.

## ✅ Résultat Final

**Le frontend peut maintenant consulter les bases de données !**

1. Liste les bases disponibles
2. Sélectionne une base
3. Affiche son contenu (personnes, familles, statistiques)
4. Navigation fluide entre les pages
5. Gestion d'erreurs robuste
6. Pagination pour les grandes bases

🎉 **Problème résolu !**
