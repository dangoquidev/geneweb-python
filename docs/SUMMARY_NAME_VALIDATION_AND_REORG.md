# Résumé : Mode Reorg et Validation des Noms

## 🔍 Questions Répondues

### 1. Espaces dans les noms de base

**Question** : "si il y a un espace dans le nom de base que j'essaye de créer, il y a une erreur. Comment c'était géré avant dans l'ocaml ?"

**Réponse** : Dans GenEWeb OCaml, **les espaces ne sont PAS autorisés** dans les noms de bases.

#### Fonction de Validation OCaml

```ocaml
(* lib/util/mutil.ml *)
let good_name s =
  let rec loop i =
    if i = String.length s then true
    else
      match s.[i] with
      | 'a' .. 'z' | 'A' .. 'Z' | '0' .. '9' | '-' -> loop (i + 1)
      | _ -> false
  in
  loop 0
```

**Caractères autorisés uniquement** :
- Lettres minuscules : `a-z`
- Lettres majuscules : `A-Z`
- Chiffres : `0-9`
- Tiret : `-`

**Caractères INTERDITS** :
- ❌ Espaces
- ❌ Underscore `_`
- ❌ Point `.`
- ❌ Slash `/`
- ❌ Caractères accentués (é, à, ç, etc.)
- ❌ Caractères spéciaux (@, #, !, ?, *, etc.)

#### Message d'Erreur OCaml

```
The database name "ma base" contains a forbidden character.
Allowed characters: a..z, A..Z, 0..9, -
```

### 2. Mode Reorg

**Question** : "c'est quoi le mode reorg ?"

**Réponse** : Le mode reorg (réorganisé) est une organisation moderne des fichiers de GenEWeb.

#### Comparaison

| Aspect | Mode Classic (Legacy) | Mode Reorg (Moderne) |
|--------|----------------------|---------------------|
| **Structure** | Fichiers dispersés | Tout dans un dossier `.gwb/` |
| **Config** | `bases/base.gwf` | `bases/base.gwb/config/base.gwf` |
| **Portraits** | `bases/images/base/` | `bases/base.gwb/documents/portraits/` |
| **Organisation** | Partagée entre bases | Isolée par base |
| **Backup** | Plusieurs dossiers à sauvegarder | Un seul dossier |
| **Défaut** | Ancien GenEWeb | GenEWeb moderne |

#### Exemple Visuel

**Mode Classic** :
```
data/
├── ma_famille.gwb/       # Fichiers base
├── ma_famille.gwf        # Config (racine)
├── images/
│   └── ma_famille/       # Portraits dispersés
└── etc/
    └── ma_famille/       # Config dispersée
```

**Mode Reorg** :
```
data/
└── ma_famille.gwb/       # TOUT dans un dossier
    ├── base.*            # Fichiers base
    ├── config/
    │   └── ma_famille.gwf
    └── documents/
        └── portraits/
```

#### Avantages du Mode Reorg

1. **Auto-contenu** : Copier/déplacer = un seul dossier
2. **Isolation** : Pas de mélange entre bases
3. **Backup simple** : `cp -r ma_famille.gwb backup/`
4. **Hébergement multiple** : Plusieurs bases sans conflits
5. **Permissions** : Gestion Unix simplifiée

## 🛠️ Implémentation Python

### 1. Validation des Noms (FAIT ✅)

#### Backend (`src/backend/services/database_service.py`)

```python
@staticmethod
def validate_database_name(name: str) -> None:
    """Valide selon les règles GenEWeb OCaml."""
    if not name:
        raise ValidationError("Database name cannot be empty")

    for i, char in enumerate(name):
        if not (char.isalnum() or char == '-'):
            raise ValidationError(
                f"Database name '{name}' contains invalid character '{char}' at position {i}. "
                f"Only alphanumerics (a-z, A-Z, 0-9) and hyphen (-) are allowed."
            )
```

#### Frontend (`src/frontend/src/pages/AdminCreateImportPage.tsx`)

```typescript
const validateDatabaseName = (name: string): { valid: boolean; error?: string } => {
  if (!name.trim()) {
    return { valid: false, error: 'Veuillez saisir un nom pour la base' }
  }

  const invalidChar = name.split('').find(c => !(/[a-zA-Z0-9-]/.test(c)))
  if (invalidChar) {
    return {
      valid: false,
      error: `Le caractère "${invalidChar}" n'est pas autorisé. Seuls les caractères alphanumériques (a-z, A-Z, 0-9) et le tiret (-) sont acceptés.`
    }
  }

  return { valid: true }
}
```

**Aide visible** :
```
Caractères autorisés : lettres (a-z, A-Z), chiffres (0-9) et tiret (-).
Les espaces ne sont pas autorisés.
```

### 2. Mode Reorg (Documentation créée ✅)

Documentation complète dans : `docs/GENEWEB_REORG_MODE.md`

**Interface mise à jour** :
```tsx
<label>Mode Reorg (organisation moderne)</label>
<p>Active la nouvelle organisation des fichiers : tous les fichiers
de la base sont regroupés dans un dossier unique nom_base.gwb/.
Recommandé pour les nouvelles bases.</p>
```

## 🧪 Tests Créés

### Script de Test Validation

`test_database_name_validation.sh`

Teste automatiquement :
- ✅ Noms valides : `mafamille`, `ma-famille`, `base-2024`
- ❌ Noms invalides : `ma famille`, `ma_famille`, `ma.base`
- ❌ Caractères spéciaux : `@`, `#`, `!`, `?`, `*`
- ❌ Caractères accentués : `é`, `à`, `ç`

Exécution :
```bash
./test_database_name_validation.sh
```

## 📝 Fichiers Modifiés/Créés

### Créés
- ✅ `docs/GENEWEB_REORG_MODE.md` - Documentation complète du mode reorg
- ✅ `test_database_name_validation.sh` - Script de test de validation

### Modifiés
- ✅ `src/backend/services/database_service.py` - Ajout validation `validate_database_name()`
- ✅ `src/frontend/src/pages/AdminCreateImportPage.tsx` - Validation frontend + explication reorg

## 🎯 Exemples d'Utilisation

### Noms de Base Valides
```
✅ ma-famille
✅ dupont-2024
✅ ArbreDuponts
✅ genealogie-france
✅ base123
```

### Noms de Base Invalides
```
❌ ma famille          (espace)
❌ ma_famille          (underscore)
❌ ma.famille          (point)
❌ famille-dupont's    (apostrophe)
❌ généalogie          (accent)
```

### Solution : Remplacer les Espaces

```
"ma famille" → "ma-famille"
"base dupont" → "base-dupont"
"généalogie française" → "genealogie-francaise"
```

## 🔜 Prochaines Étapes (Optionnel)

Pour implémenter complètement le mode reorg dans Python :

1. **Classe DatabasePaths** (proposée dans la doc)
   - Détection automatique du mode
   - Gestion des chemins selon le mode
   - Création de la structure

2. **Support dans DatabaseService**
   ```python
   def create_database(self, name: str, mode: DatabaseMode = DatabaseMode.REORG):
       paths = DatabasePaths(self.database_dir, name, mode)
       paths.create_structure()
       # ...
   ```

3. **API REST**
   ```python
   class DatabaseCreateRequest(BaseModel):
       name: str
       db_type: str = "pickle"
       reorg: bool = True  # Par défaut en mode reorg
   ```

4. **Migration Classic → Reorg**
   - Utilitaire de conversion
   - Script de migration automatique

## 📚 Références

- **Code OCaml** : `legacy/ocaml-old-project/lib/GWPARAM.ml`
- **Validation** : `legacy/ocaml-old-project/lib/util/mutil.ml` (fonction `good_name`)
- **Documentation** : `docs/GENEWEB_REORG_MODE.md`
