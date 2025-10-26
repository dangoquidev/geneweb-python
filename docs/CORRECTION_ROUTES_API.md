# Correction des Routes API Obsolètes

## 🐛 Problème Détecté

Les logs du serveur montraient des erreurs 404 :
```
INFO: 127.0.0.1:39356 - "GET /api/roundtrip-test-2/info HTTP/1.1" 404 Not Found
```

## 🔍 Diagnostic

Le code frontend utilisait des **routes API obsolètes** qui n'existent plus :
- ❌ `/api/{database_name}/info` → Obsolète
- ❌ `/api/{database_name}/search` → Obsolète

Ces routes étaient un héritage de l'ancienne architecture et ont été remplacées par :
- ✅ `/api/databases/{database_name}` → Info de la base
- ✅ `/api/databases/{database_name}/search` → Recherche dans la base

## 🛠️ Corrections Appliquées

### Backend : Nouvelle Route de Recherche

**Fichier** : `src/backend/api/routes/database_persons.py`

Ajout de la route de recherche par base :

```python
@router.get("/databases/{database_name}/search")
async def search_database_persons(
    database_name: str,
    q: str,
    limit: int = 50
) -> List[PersonResponse]:
    """Recherche de personnes dans une base spécifique."""
    # Recherche simple dans first_name, surname, public_name, aliases
    ...
```

### Frontend : Mise à Jour des Hooks et Composants

#### 1. Hook `useDatabaseInfo.ts`

```typescript
// AVANT
fetch(`/api/${baseName}/info`)

// APRÈS
fetch(`/api/databases/${encodeURIComponent(baseName)}`)
```

#### 2. Hook `useSearch.ts`

```typescript
// AVANT
fetch(`/api/${baseName}/search?q=${query}`)

// APRÈS
fetch(`/api/databases/${encodeURIComponent(baseName)}/search?q=${query}`)

// + Adaptation pour le nouveau format de réponse (array direct)
const results = Array.isArray(data) ? data : (data.results || []);
```

#### 3. Composant `App.tsx`

```typescript
// Info de la base
fetch(`/api/databases/${encodeURIComponent(selected)}`)

// Recherche
fetch(`/api/databases/${encodeURIComponent(selected)}/search?q=${query}`)
```

## ✅ Tests de Validation

### 1. Route d'Information

```bash
curl "http://127.0.0.1:8000/api/databases/test"
# ✅ Retourne les infos de la base
```

**Résultat** :
```json
{
  "base_name": "test",
  "persons": 5,
  "families": 2,
  "path": "data/test.pickle",
  "version": "1.0",
  "created_date": "2025-10-24T13:51:43.131803",
  "modified_date": "2025-10-24T13:51:43.131803"
}
```

### 2. Route de Recherche

```bash
curl "http://127.0.0.1:8000/api/databases/test/search?q=John"
# ✅ Retourne les personnes correspondantes
```

**Résultat** :
```json
[
  {
    "id": "I1",
    "first_name": "John",
    "surname": "Doe",
    ...
  }
]
```

### 3. Base avec Tirets (Cas Problématique)

```bash
curl "http://127.0.0.1:8000/api/databases/roundtrip-test-2"
# ✅ Plus d'erreur 404
```

**Résultat** :
```json
{
  "base_name": "roundtrip-test-2",
  "persons": 5,
  "families": 1,
  "path": "data/roundtrip-test-2.pickle",
  "version": "1.0",
  "created_date": "2025-10-26T15:32:14.840644",
  "modified_date": "2025-10-26T15:32:14.840644"
}
```

## 📊 Tableau de Correspondance des Routes

| Ancien Format | Nouveau Format | Description |
|--------------|----------------|-------------|
| `/api/{base}/info` | `/api/databases/{base}` | Informations de la base |
| `/api/{base}/search` | `/api/databases/{base}/search` | Recherche de personnes |
| ❌ N/A | `/api/databases/{base}/persons` | Liste des personnes |
| ❌ N/A | `/api/databases/{base}/families` | Liste des familles |
| ❌ N/A | `/api/databases/{base}/statistics` | Statistiques détaillées |

## 🔑 Points Importants

### Encodage des URLs

Toutes les nouvelles routes utilisent `encodeURIComponent()` pour gérer correctement :
- Les tirets : `roundtrip-test-2` ✅
- Les espaces : `Ma Base` → `Ma%20Base` ✅
- Les caractères spéciaux : `base_émilie` → `base_%C3%A9milie` ✅

### Format de Réponse

**Ancienne route de recherche** :
```json
{
  "results": [...],
  "count": 10
}
```

**Nouvelle route** :
```json
[...]  // Array direct
```

Le code frontend a été adapté pour gérer les deux formats pendant la transition :
```typescript
const results = Array.isArray(data) ? data : (data.results || []);
```

## 📁 Fichiers Modifiés

### Backend
- 📝 `src/backend/api/routes/database_persons.py` - Ajout route `/search`

### Frontend
- 📝 `src/frontend/src/hooks/useDatabaseInfo.ts` - Correction route `/info`
- 📝 `src/frontend/src/hooks/useSearch.ts` - Correction route `/search` + format
- 📝 `src/frontend/src/App.tsx` - Correction routes `/info` et `/search`

## ✅ Résultat

- ✅ Plus d'erreurs 404 dans les logs
- ✅ Les hooks frontend fonctionnent avec les nouvelles routes
- ✅ Recherche fonctionnelle dans toutes les bases
- ✅ Gestion correcte des noms avec caractères spéciaux
- ✅ Rétrocompatibilité pour l'ancien format de réponse

## 🚀 Prochaines Étapes

Si d'autres composants utilisent les anciennes routes, rechercher avec :

```bash
# Rechercher les anciennes routes
grep -r "/api/.*/" src/frontend/ --include="*.ts" --include="*.tsx"
```

Puis remplacer par le nouveau format :
- `/api/{base}/...` → `/api/databases/{base}/...`
