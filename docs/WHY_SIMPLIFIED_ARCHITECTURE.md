# Pourquoi notre implémentation Python est différente de GenEWeb OCaml

## 🎯 Philosophie du Projet

Notre projet **n'est PAS une réécriture complète de GenEWeb**, mais une **modernisation du cœur généalogique** avec une architecture simplifiée.

## 📊 Comparaison des Fonctionnalités

| Fonctionnalité | GenEWeb OCaml (Original) | Notre Python (Modernisé) | Statut |
|----------------|--------------------------|--------------------------|---------|
| **Base de données** | Format binaire custom | Pickle Python | ✅ Implémenté |
| **API REST** | CGI/Serveur custom | FastAPI moderne | ✅ Implémenté |
| **Personnes/Familles** | Modèles complets | Modèles Python (Pydantic) | ✅ Implémenté |
| **Interface Web** | Templates historiques | React + TypeScript moderne | ✅ Implémenté |
| **Portraits** | Dossier `images/` | ❌ Non implémenté | 📋 Futur |
| **Documents sources** | Dossier `src/` | ❌ Non implémenté | 📋 Futur |
| **Configuration .gwf** | Fichier texte custom | ❌ Non implémenté | 📋 Futur |
| **Multilangue** | Fichiers `lang/` | ❌ Non implémenté | 📋 Futur |
| **Thèmes/Templates** | Dossier `etc/` | ❌ Non implémenté | 📋 Futur |
| **Wizards/Authentification** | Système custom | ❌ Non implémenté | 📋 Futur |
| **Forum** | Plugin OCaml | ❌ Non implémenté | ❌ Pas prévu |
| **Export GEDCOM** | Binaire `gwb2ged` | ❌ Non implémenté | 📋 Futur |
| **Import GEDCOM** | Binaire `ged2gwb` | ❌ Non implémenté | 📋 Futur |
| **Consanguinité** | Calculs complexes | ❌ Non implémenté | 📋 Futur |
| **Relations** | Algorithmes avancés | ❌ Non implémenté | 📋 Futur |

## 🏗️ Notre Architecture Actuelle

### Structure Minimale

```
Awkward_legacy/
├── src/
│   └── backend/
│       ├── api/          # FastAPI REST
│       ├── core/         # Modèles (Person, Family)
│       ├── database/     # PickleDriver
│       └── services/     # Business logic
├── data/
│   ├── showcase.pickle   # Bases de données
│   ├── ma_famille.pickle
│   └── test.pickle
└── tests/                # Tests unitaires
```

**C'est tout !** Pas de dossiers `images/`, `src/`, `etc/`, `lang/`.

### Pourquoi cette Simplicité ?

#### 1. **Phase MVP (Minimum Viable Product)**

Nous construisons d'abord le **cœur du système** :
- ✅ Stockage des personnes et familles
- ✅ API pour accéder aux données
- ✅ Interface web moderne
- ✅ Tests unitaires

Les fonctionnalités avancées viendront **ensuite**, une fois le socle solide.

#### 2. **Principe YAGNI (You Aren't Gonna Need It)**

Ne pas implémenter ce qui n'est pas utilisé :
- **Portraits** ? Pas de gestion d'images pour l'instant → Pas de dossier `images/`
- **Configuration .gwf** ? Pas de wizards/permissions pour l'instant → Pas de `.gwf`
- **Multilangue** ? Interface en français/anglais hardcodée → Pas de dossier `lang/`
- **Templates** ? Un seul thème React → Pas de dossier `etc/`

#### 3. **Architecture Moderne vs Legacy**

GenEWeb OCaml (1998-2025) :
```ocaml
(* Structure monolithique avec tout mélangé *)
images/base_name/portrait.jpg
src/base_name/document.pdf
etc/base_name/template.txt
lang/fr/lexicon.txt
base_name.gwf
base_name.gwb/
```

Notre Python (2025) :
```python
# Architecture moderne, séparation des préoccupations
data/base_name.pickle          # Une base = un fichier
static/                        # Assets séparés (futur)
config/                        # Configuration centralisée (futur)
```

#### 4. **Format de Stockage Différent**

**OCaml** : Format binaire custom complexe
- Nécessite beaucoup de fichiers auxiliaires
- Index, caches, fichiers de config

**Python Pickle** : Format sérialisation Python natif
- Tout-en-un : personnes + familles dans un seul fichier
- Plus simple à gérer
- Pas besoin de fichiers externes pour l'instant

## 🔮 Feuille de Route (Roadmap)

### Phase 1 : Cœur Généalogique ✅ (ACTUELLE)

- ✅ Modèles de données (Person, Family)
- ✅ Stockage Pickle
- ✅ API REST (CRUD basique)
- ✅ Interface web simple
- ✅ Tests unitaires

### Phase 2 : Fonctionnalités Avancées 📋 (PROCHAINE)

- 📋 **Import/Export GEDCOM** (priorité haute)
- 📋 **Recherche avancée** (noms, dates, lieux)
- 📋 **Visualisations** (arbres généalogiques graphiques)
- 📋 **Statistiques** (âges, répartition géographique)

### Phase 3 : Médias et Documents 📋

- 📋 **Gestion des portraits** → Dossier `static/portraits/`
- 📋 **Documents sources** → Dossier `static/documents/`
- 📋 **Galerie photos**
- 📋 **Stockage S3/Cloud** (optionnel)

### Phase 4 : Multi-utilisateurs 📋

- 📋 **Authentification** (JWT moderne, pas .gwf)
- 📋 **Rôles** (admin, contributeur, lecteur)
- 📋 **Permissions** par base
- 📋 **Audit logs**

### Phase 5 : Internationalisation 📋

- 📋 **i18n** (React-i18next ou similaire)
- 📋 **Langues** : FR, EN, DE, ES, etc.
- 📋 **Formats de dates** localisés

### Phase 6 : Compatibilité GenEWeb 📋

- 📋 **Lecture bases OCaml** (format .gwb)
- 📋 **Support mode reorg**
- 📋 **Migration OCaml → Python**
- 📋 **Configuration .gwf** (compatibilité)

## 🎨 Différences Philosophiques

| Aspect | GenEWeb OCaml | Notre Python |
|--------|---------------|--------------|
| **Âge** | 27 ans (1998-2025) | Nouveau (2025) |
| **Approche** | Monolithique, tout-en-un | Modulaire, microservices-ready |
| **Interface** | Templates HTML statiques | SPA React moderne |
| **API** | CGI, formulaires HTML | REST JSON, OpenAPI |
| **Base de données** | Format binaire custom | Pickle (simple), SQLite/PostgreSQL (futur) |
| **Configuration** | Fichiers texte .gwf | Variables d'environnement, JSON/YAML (futur) |
| **Déploiement** | Serveur dédié, Unix | Docker, Cloud-native |
| **Authentification** | HTTP Basic, .gwf | JWT, OAuth2 (futur) |
| **Médias** | Dossiers locaux | Object storage, CDN (futur) |

## 💡 Pourquoi Pas de `.gwf` ?

Le fichier `.gwf` dans GenEWeb contient :

```plaintext
wizard_passwd=wiz:wiz
friend_passwd=fr:fr
access_by_key=yes
private_years=100
private_years_death=20
hide_private_names=yes
```

**Notre approche moderne** :
- Variables d'environnement (`.env`)
- Base de données (utilisateurs, permissions)
- Configuration centralisée (pas par base)
- JWT pour l'authentification

**Exemple** :
```python
# .env
SECRET_KEY=xxx
DATABASE_PATH=data/
JWT_EXPIRATION=3600
PRIVATE_YEARS=100
```

## 🚀 Exemple Concret : Ajout des Portraits

Quand on décidera d'ajouter les portraits, on fera :

### 1. Structure de Dossiers

```python
# src/backend/services/media_service.py
class MediaService:
    def __init__(self, media_dir: str = "static/media"):
        self.portraits_dir = Path(media_dir) / "portraits"
        self.documents_dir = Path(media_dir) / "documents"
        self.portraits_dir.mkdir(parents=True, exist_ok=True)
```

### 2. API REST

```python
# src/backend/api/routes/media.py
@router.post("/persons/{person_id}/portrait")
async def upload_portrait(
    person_id: str,
    file: UploadFile,
    service: MediaService = Depends(get_media_service)
):
    path = await service.save_portrait(person_id, file)
    return {"path": path}
```

### 3. Frontend React

```tsx
// src/frontend/src/components/person/PortraitUpload.tsx
const PortraitUpload = ({ personId }) => {
  const handleUpload = async (file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    await api.uploadPortrait(personId, formData)
  }
  return <input type="file" onChange={e => handleUpload(e.target.files[0])} />
}
```

**Moderne, simple, testable !**

## 📝 Conclusion

### Pourquoi on n'a pas tout ça maintenant ?

1. **On construit progressivement** : Socle d'abord, fonctionnalités ensuite
2. **On évite la complexité inutile** : Pas de code mort
3. **On modernise** : Pas de réplication du legacy à l'identique
4. **On teste** : Chaque fonctionnalité est testée avant d'ajouter la suivante

### Notre Philosophie

> "Make it work, make it right, make it fast."
> — Kent Beck

Actuellement : **Make it work** ✅
- Le cœur fonctionne
- Les tests passent
- L'API est propre

Prochainement : **Make it right**
- Ajouter les fonctionnalités manquantes
- Améliorer l'UX
- Compléter la couverture de tests

Futur : **Make it fast**
- Optimisations
- Cache
- Scaling

### Mode Reorg : Supprimer ou Garder ?

**Décision : SUPPRIMER pour l'instant**

Raisons :
1. ❌ Pas de fichiers `.gwf`, `etc/`, `lang/`, `images/` actuellement
2. ❌ Ajoute de la complexité sans bénéfice
3. ❌ Embrouille l'utilisateur avec une option qui ne fait rien
4. ✅ On pourra le rajouter plus tard si besoin (quand on aura des médias, config, etc.)

**Si un jour on implémente la compatibilité GenEWeb OCaml**, on reconsidérera le mode reorg.

## 🔗 Pour Aller Plus Loin

Voir :
- `docs/GENEWEB_REORG_MODE.md` - Explication du mode reorg OCaml (pour référence)
- `README.md` - Vision du projet (à créer)
- `CONTRIBUTING.md` - Guide de contribution (à créer)
- `ROADMAP.md` - Feuille de route détaillée (à créer)
