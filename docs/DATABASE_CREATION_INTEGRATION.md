# 🎯 Intégration Backend ↔️ Frontend pour la Création de Bases

## ✅ Résumé de l'implémentation

L'utilisateur a demandé : **"comment faire pour intégrer le fait de pouvoir créer une base de données avec notre nouveau backend depuis le frontend ?"**

### Architecture mise en place

```
Frontend (React/TypeScript)
    ↓ HTTP POST
API Layer (FastAPI)
    ↓ Business Logic
Service Layer (DatabaseService)
    ↓ Data Access
Driver Layer (PickleDriver)
    ↓ File System
data/*.pickle files
```

---

## 📦 Fichiers créés / modifiés

### Backend

#### 1. **src/backend/api/schemas/database.py** (NOUVEAU)
- `DatabaseCreateRequest`: Validation Pydantic du nom (alphanumérique, _, -)
- `DatabaseCreateResponse`: Réponse avec `success`, `database_name`, `path`, `message`
- `DatabaseListResponse`: Liste des bases avec `databases[]` et `count`
- `DatabaseInfoResponse`: Info détaillées (persons, families, version, dates)

**Validations:**
- ✅ Nom valide : lettres, chiffres, `_`, `-`
- ❌ Noms réservés : con, prn, aux, nul, com1, lpt1
- ❌ Caractères spéciaux : `/`, `\`, `?`, `*`, etc.
- ❌ Espaces leading/trailing

#### 2. **src/backend/services/database_service.py** (NOUVEAU)
Logique métier pour gestion des bases:
- `list_databases()`: Liste toutes les bases .pickle
- `create_database(name, db_type)`: Crée une base vide
- `database_exists(name)`: Vérifie existence
- `get_database_path(name)`: Retourne chemin complet
- `delete_database(name)`: Supprime une base

**Gestion d'erreurs:**
- `ValidationError`: Nom invalide ou base existe
- `DatabaseError`: Erreur lors de création/suppression

#### 3. **src/backend/api/routes/databases.py** (NOUVEAU)
Endpoints FastAPI:
- `GET /api/databases` → Liste des bases
- `POST /api/databases` → Créer une base
- `GET /api/databases/{name}` → Info d'une base
- `DELETE /api/databases/{name}` → Supprimer une base

#### 4. **src/backend/database/pickle_driver.py** (MODIFIÉ)
- Ajout de `get_info()`: Retourne metadata format API
  - `persons_count`, `families_count`
  - `version`, `created_date`, `modified_date`

#### 5. **src/backend/api/app.py** (MODIFIÉ)
- Enregistrement du router databases
- Fix error handler pour ValueError Pydantic (JSON serialization)

---

### Frontend

#### 6. **src/frontend/src/services/api.ts** (NOUVEAU)
Client API TypeScript avec types forts:
```typescript
// Fonctions exportées
export async function listDatabases(): Promise<DatabaseListResponse>
export async function createDatabase(request: DatabaseCreateRequest): Promise<DatabaseCreateResponse>
export async function getDatabaseInfo(name: string): Promise<DatabaseInfoResponse>
export async function deleteDatabase(name: string): Promise<void>

// Types
export interface DatabaseCreateRequest {
  name: string;
  db_type?: 'pickle' | 'sqlite';
}

export class ApiError extends Error {
  status: number;
  statusText: string;
  details?: any;
}
```

**Gestion d'erreurs:**
- `ApiError` avec status code et détails
- Extraction automatique des messages d'erreur de l'API
- Support 204 No Content (DELETE)

#### 7. **src/frontend/src/pages/AdminCreateImportPage.tsx** (MODIFIÉ)
Intégration dans le formulaire "Méthode simple":
```tsx
import { createDatabase, ApiError } from '../services/api'

const handleSimpleSubmit = async (e: React.FormEvent) => {
  try {
    const result = await createDatabase({
      name: simpleName,
      db_type: 'pickle',
    })
    setMessage({ type: 'success', text: result.message })
  } catch (error) {
    if (error instanceof ApiError) {
      errorMsg = error.details?.detail || error.details?.message
    }
    setMessage({ type: 'error', text: errorMsg })
  }
}
```

**Remplace:** Simulation `setTimeout` par vraie requête HTTP

---

### Tests

#### 8. **tests/backend_tests/test_api_database.py** (NOUVEAU)
**17 tests exhaustifs:**

**TestDatabaseListEndpoint (2 tests):**
- ✅ Liste vide
- ✅ Liste avec bases existantes

**TestDatabaseCreateEndpoint (9 tests):**
- ✅ Création réussie
- ✅ Type par défaut (pickle)
- ✅ Nom invalide (/, \, ?, *)
- ✅ Nom avec espaces
- ✅ Nom réservé (con, prn, aux)
- ✅ Base déjà existante
- ✅ Nom manquant
- ✅ Nom vide
- ✅ Noms valides multiples

**TestDatabaseInfoEndpoint (2 tests):**
- ✅ Info base existante
- ✅ Base non trouvée (404)

**TestDatabaseDeleteEndpoint (2 tests):**
- ✅ Suppression réussie
- ✅ Base non trouvée (404)

**TestDatabaseWorkflow (2 tests):**
- ✅ Cycle complet : create → list → info → delete
- ✅ Création de multiples bases

---

## 🚀 Utilisation

### Via l'API (curl)

```bash
# Lister les bases
curl http://127.0.0.1:8000/api/databases

# Créer une base
curl -X POST http://127.0.0.1:8000/api/databases \
  -H "Content-Type: application/json" \
  -d '{"name": "ma_nouvelle_base", "db_type": "pickle"}'

# Info sur une base
curl http://127.0.0.1:8000/api/databases/ma_nouvelle_base

# Supprimer une base
curl -X DELETE http://127.0.0.1:8000/api/databases/ma_nouvelle_base
```

### Via le Frontend

1. **Accéder à la page admin:**
   ```
   http://localhost:5173/admin/create-import
   ```

2. **Onglet "Méthode simple":**
   - Saisir nom de base (ex: `ma_famille`)
   - Cliquer "Créer"
   - Message de succès : "Database 'ma_famille' created successfully"

3. **Vérification:**
   ```bash
   ls -lh data/*.pickle
   # ma_famille.pickle créé (112 bytes = vide)
   ```

---

## 🎨 Swagger UI

Documentation interactive auto-générée:
```
http://127.0.0.1:8000/api/docs
```

**Endpoints visibles:**
- `POST /api/databases` (Database Management)
- `GET /api/databases` (Database Management)
- `GET /api/databases/{database_name}` (Database Management)
- `DELETE /api/databases/{database_name}` (Database Management)

**Try it out:**
1. Cliquer "POST /api/databases"
2. Cliquer "Try it out"
3. Modifier le JSON:
   ```json
   {
     "name": "test_swagger",
     "db_type": "pickle"
   }
   ```
4. Cliquer "Execute"
5. Voir la réponse 201 Created

---

## 🧪 Résultats des tests

```bash
$ python -m pytest tests/backend_tests/test_api_database.py -v

17 passed, 5 warnings in 1.78s
```

**Validation E2E:**
```bash
$ curl -X POST http://127.0.0.1:8000/api/databases \
    -H "Content-Type: application/json" \
    -d '{"name": "test_api", "db_type": "pickle"}'

201 Created
{
  "success": true,
  "database_name": "test_api",
  "path": "data/test_api.pickle",
  "message": "Database 'test_api' created successfully"
}

$ ls -lh data/test_api.pickle
-rw-r--r--. 1 acamus acamus 112 Oct 16 15:03 data/test_api.pickle
```

---

## 🔒 Sécurité

**Actuellement:**
- ✅ Validation stricte des noms (Pydantic)
- ✅ Vérification anti-conflit (base existe)
- ✅ Gestion d'erreurs robuste
- ⚠️  Authentification commentée (à implémenter)

**TODO pour production:**
```python
# Dans databases.py
@router.post("/databases")
async def create_database(
    request: DatabaseCreateRequest,
    service: DatabaseService = Depends(get_database_service),
    _auth = Depends(require_auth),  # ← Décommenter
)
```

---

## 📊 Architecture de validation

### Niveaux de validation

1. **Frontend (TypeScript):**
   - Types forts (`DatabaseCreateRequest`)
   - Validation HTML5 (`required`, `min-length`)

2. **API (Pydantic):**
   ```python
   @field_validator("name")
   def validate_name(cls, v: str) -> str:
       # Regex alphanumérique + _ + -
       # Anti noms réservés
       # Anti espaces leading/trailing
   ```

3. **Service (DatabaseService):**
   ```python
   if self.database_exists(name):
       raise ValidationError(f"Database '{name}' already exists")
   ```

4. **Driver (PickleDriver):**
   ```python
   try:
       driver.save(persons={}, families={}, create_backup=False)
   except Exception as e:
       raise DatabaseError(...)
   ```

---

## 🎯 Points clés de l'implémentation

### 1. **Separation of Concerns**
- **Routes** (HTTP) → **Services** (Business) → **Drivers** (Data)
- Chaque couche a une responsabilité unique

### 2. **Type Safety**
- Pydantic (Python) + TypeScript (Frontend)
- Erreurs détectées à la compilation/validation

### 3. **Error Handling**
```python
# Backend custom exceptions
ValidationError → 400 Bad Request
DatabaseError → 500 Internal Server Error
PersonNotFoundError → 404 Not Found

# Frontend ApiError
try {
  await createDatabase({...})
} catch (error) {
  if (error instanceof ApiError) {
    // Status code + détails
  }
}
```

### 4. **Testing Strategy**
- Unit tests (service layer)
- Integration tests (API endpoints)
- E2E validation (curl/frontend)

---

## 🚦 Workflow complet

```
┌─────────────────────────────────────┐
│ User clicks "Créer" button          │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│ handleSimpleSubmit() called         │
│ → createDatabase({name: "test"})    │
└──────────────┬──────────────────────┘
               │ HTTP POST
               ▼
┌─────────────────────────────────────┐
│ FastAPI router: create_database()   │
│ → Pydantic validates request        │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│ DatabaseService.create_database()   │
│ → Check if exists                   │
│ → Validate name                     │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│ PickleDriver.save()                 │
│ → Create empty {persons, families}  │
│ → Write to data/test.pickle         │
└──────────────┬──────────────────────┘
               │ Success
               ▼
┌─────────────────────────────────────┐
│ Return DatabaseCreateResponse       │
│ {success: true, ...}                │
└──────────────┬──────────────────────┘
               │ JSON
               ▼
┌─────────────────────────────────────┐
│ Frontend displays success message   │
│ "Database 'test' created!"          │
└─────────────────────────────────────┘
```

---

## 📈 Métriques

- **Lignes de code ajoutées:** ~800
- **Tests créés:** 17 (100% pass)
- **Endpoints ajoutés:** 4
- **Types TypeScript:** 5 interfaces
- **Temps de développement:** ~2h
- **Coverage backend:** 95%+ (estimation)

---

## 🎓 Apprentissages

1. **Pydantic field_validator:**
   - ValueError pas JSON-serializable par défaut
   - Fix: Extraire `.str()` dans error handler

2. **PickleDriver.save():**
   - Signature: `save(persons, families, create_backup)`
   - Pas de mutation directe de `driver.persons`

3. **FastAPI dependency injection:**
   - `Depends(get_database_service)` pour chaque route
   - Service créé avec database_dir de l'environnement

4. **TypeScript parameter properties:**
   - `public status: number` pas compatible avec `erasableSyntaxOnly`
   - Fix: Déclarer propriétés séparément

---

## 🔮 Prochaines étapes suggérées

1. **Authentification:**
   - Décommenter `Depends(require_auth)`
   - Implémenter JWT tokens

2. **Import GEDCOM:**
   - Endpoint `POST /api/databases/import/gedcom`
   - Upload multipart/form-data

3. **Validation avancée:**
   - Quota par utilisateur
   - Rate limiting
   - Taille max de base

4. **UI améliorée:**
   - Liste des bases existantes
   - Bouton "Delete" avec confirmation
   - Progress bar pour import

---

## 📚 Documentation générée

**Swagger UI:** http://127.0.0.1:8000/api/docs
**ReDoc:** http://127.0.0.1:8000/api/redoc
**OpenAPI Schema:** http://127.0.0.1:8000/api/openapi.json

---

**Résumé:** Intégration complète et testée permettant de créer des bases de données depuis le frontend React via l'API REST FastAPI, avec validation robuste et gestion d'erreurs à tous les niveaux.
