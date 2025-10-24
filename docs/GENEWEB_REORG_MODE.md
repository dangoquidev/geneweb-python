# Mode Reorg dans GenEWeb

## 📋 Qu'est-ce que le Mode Reorg ?

Le **mode reorg** (réorganisé) est un mode d'organisation des fichiers dans GenEWeb qui change complètement la structure de stockage de la base de données et de ses fichiers associés.

## 🗂️ Différences de Structure

### Mode Classic (Legacy)

Structure historique de GenEWeb :

```
bases/
├── ma_base.gwb/          # Fichiers de base
├── ma_base.gwf           # Configuration (racine)
├── etc/
│   └── ma_base/          # Configuration par base
├── lang/
│   └── ma_base/          # Traductions
├── cnt/                  # Compteurs (partagé)
├── images/
│   └── ma_base/          # Portraits
└── src/
    └── ma_base/          # Documents sources
```

### Mode Reorg (Nouvelle organisation)

Tout est regroupé dans un dossier `.gwb` :

```
bases/
└── ma_base.gwb/
    ├── base.*            # Fichiers de base
    ├── config/
    │   ├── ma_base.gwf   # Configuration
    │   └── cnt/          # Compteurs
    ├── etc/              # Configuration
    │   └── lang/         # Traductions
    └── documents/
        ├── portraits/    # Portraits
        ├── images/       # Images
        └── src/          # Documents sources
```

## 🎯 Avantages du Mode Reorg

### 1. **Auto-contenu**
- Toute la base est dans un seul dossier `.gwb`
- Facile à sauvegarder : copier un seul dossier
- Facile à déplacer ou partager

### 2. **Isolation**
- Chaque base est complètement isolée
- Pas de mélange de fichiers entre bases
- Moins de risques de conflits

### 3. **Sécurité**
- Permissions Unix plus simples à gérer
- Backup/restore plus simple
- Meilleure séparation des environnements

### 4. **Déploiement**
- Permet d'héberger plusieurs bases sur le même serveur
- Chaque base peut avoir sa propre configuration
- Migration simplifiée

## 🔍 Détection du Mode

GenEWeb détecte automatiquement le mode en vérifiant si ce fichier existe :

```
bases/ma_base.gwb/config/ma_base.gwf
```

**Si ce fichier existe** → Mode Reorg
**Sinon** → Mode Classic

Code OCaml (`lib/GWPARAM.ml`) :

```ocaml
let is_reorg_base bname =
  let bname = Filename.remove_extension bname in
  Sys.file_exists
    (String.concat Filename.dir_sep
       [ Secure.base_dir (); bname ^ ".gwb"; "config"; bname ^ ".gwf" ])
```

## 📂 Correspondance des Chemins

| Fichier/Dossier | Mode Classic | Mode Reorg |
|----------------|--------------|------------|
| **Configuration** | `bases/ma_base.gwf` | `bases/ma_base.gwb/config/ma_base.gwf` |
| **Compteurs** | `bases/cnt/` | `bases/ma_base.gwb/config/cnt/` |
| **Portraits** | `bases/images/ma_base/` | `bases/ma_base.gwb/documents/portraits/` |
| **Sources** | `bases/src/ma_base/` | `bases/ma_base.gwb/documents/src/` |
| **Config locale** | `bases/etc/ma_base/` | `bases/ma_base.gwb/etc/` |
| **Langues** | `bases/lang/ma_base/` | `bases/ma_base.gwb/etc/lang/` |
| **Images** | `bases/src/ma_base/images/` | `bases/ma_base.gwb/documents/images/` |

## 🛠️ Utilisation

### Création d'une base en mode Reorg

```bash
# Avec gwc (compilation)
gwc -o ma_base -reorg source.gw

# Avec ged2gwb (import GEDCOM)
ged2gwb -o ma_base -reorg famille.ged
```

### Création d'une base en mode Classic

```bash
# Sans l'option -reorg
gwc -o ma_base source.gw
ged2gwb -o ma_base famille.ged
```

### Dans le serveur gwd

Le serveur détecte automatiquement le mode :

```bash
gwd -bd /path/to/bases
# Charge automatiquement en mode reorg ou classic selon la structure
```

## 🔄 Migration Classic → Reorg

Il n'y a pas d'outil automatique de migration. Pour convertir :

1. **Créer la structure reorg** :
```bash
mkdir -p ma_base.gwb/config
mkdir -p ma_base.gwb/documents/{portraits,images,src}
mkdir -p ma_base.gwb/etc/lang
```

2. **Déplacer les fichiers** :
```bash
# Configuration
mv ma_base.gwf ma_base.gwb/config/

# Base de données
mv ma_base.gwb/*.* ma_base.gwb/  # fichiers base.*

# Portraits
mv images/ma_base/* ma_base.gwb/documents/portraits/

# Sources
mv src/ma_base/* ma_base.gwb/documents/src/

# Config locale
mv etc/ma_base/* ma_base.gwb/etc/

# Langues
mv lang/ma_base/* ma_base.gwb/etc/lang/
```

3. **Vérifier** :
```bash
# Le fichier config doit exister ici
ls ma_base.gwb/config/ma_base.gwf
```

## ⚙️ Dans le Code OCaml

### Modules

Deux modules définissent les chemins :

- **`Default`** : Mode Reorg (nouveau)
- **`Legacy`** : Mode Classic (ancien)

### Initialisation

```ocaml
(* Détection automatique *)
let init bname =
  reorg := !reorg || is_reorg_base bname;
  if !reorg then (
    config := Default.config;
    cnt_d := Default.cnt_d;
    (* ... autres chemins Default ... *)
  ) else (
    config := Legacy.config;
    cnt_d := Legacy.cnt_d;
    (* ... autres chemins Legacy ... *)
  )
```

### Forcer le Mode

```ocaml
(* Dans gwc.ml, gwb2ged.ml, etc. *)
("-reorg", Arg.Set Geneweb.GWPARAM.reorg, " Mode reorg")
```

## 🐍 Implémentation Python

### ⚠️ Note : Mode Reorg NON implémenté

**Décision** : Le mode reorg n'est **pas implémenté** dans notre version Python pour les raisons suivantes :

1. **Simplicité actuelle** : Notre architecture stocke uniquement des fichiers `.pickle` dans `data/`
   - Pas de fichiers de configuration `.gwf`
   - Pas de portraits/images
   - Pas de documents sources
   - Pas de fichiers etc/lang/

2. **Pas de bénéfice** : Le mode reorg résout un problème qu'on n'a pas
   - Pas de dispersion de fichiers
   - Structure déjà simple et moderne
   - Un fichier = une base

3. **Overhead inutile** : L'implémenter ajouterait :
   - Complexité sans valeur ajoutée
   - Structure de dossiers vides
   - Code de maintenance supplémentaire

4. **YAGNI Principle** : "You Aren't Gonna Need It"
   - On n'implémente que ce qui est nécessaire
   - Si un jour on ajoute des portraits/config, on réévaluera

**Conclusion** : Pour une version moderne de GenEWeb en Python, une structure simple suffit :
```
data/
├── base1.pickle
├── base2.pickle
└── base3.pickle
```

Si dans le futur on ajoute des fichiers annexes (portraits, config), on pourra reconsidérer.

---

### 📚 Documentation Technique (pour référence)

Si on devait l'implémenter plus tard, voici comment faire :

### Structure Proposée

```python
from enum import Enum
from pathlib import Path

class DatabaseMode(Enum):
    CLASSIC = "classic"
    REORG = "reorg"

class DatabasePaths:
    """Gère les chemins selon le mode classic ou reorg."""

    def __init__(self, base_dir: str, db_name: str, mode: DatabaseMode):
        self.base_dir = Path(base_dir)
        self.db_name = db_name
        self.mode = mode

    @staticmethod
    def detect_mode(base_dir: str, db_name: str) -> DatabaseMode:
        """Détecte automatiquement le mode (comme GenEWeb OCaml)."""
        config_reorg = Path(base_dir) / f"{db_name}.gwb" / "config" / f"{db_name}.gwf"
        return DatabaseMode.REORG if config_reorg.exists() else DatabaseMode.CLASSIC

    @property
    def db_path(self) -> Path:
        """Chemin vers le dossier de la base."""
        return self.base_dir / f"{self.db_name}.gwb"

    @property
    def config_file(self) -> Path:
        """Chemin vers le fichier de configuration .gwf."""
        if self.mode == DatabaseMode.REORG:
            return self.db_path / "config" / f"{self.db_name}.gwf"
        else:
            return self.base_dir / f"{self.db_name}.gwf"

    @property
    def portraits_dir(self) -> Path:
        """Chemin vers le dossier portraits."""
        if self.mode == DatabaseMode.REORG:
            return self.db_path / "documents" / "portraits"
        else:
            return self.base_dir / "images" / self.db_name

    @property
    def config_dir(self) -> Path:
        """Chemin vers le dossier de configuration."""
        if self.mode == DatabaseMode.REORG:
            return self.db_path / "config"
        else:
            return self.base_dir

    def create_structure(self) -> None:
        """Crée la structure de dossiers selon le mode."""
        if self.mode == DatabaseMode.REORG:
            (self.db_path / "config").mkdir(parents=True, exist_ok=True)
            (self.db_path / "config" / "cnt").mkdir(exist_ok=True)
            (self.db_path / "documents" / "portraits").mkdir(parents=True, exist_ok=True)
            (self.db_path / "documents" / "images").mkdir(parents=True, exist_ok=True)
            (self.db_path / "documents" / "src").mkdir(parents=True, exist_ok=True)
            (self.db_path / "etc" / "lang").mkdir(parents=True, exist_ok=True)
        else:
            self.base_dir.mkdir(parents=True, exist_ok=True)
            (self.base_dir / "etc" / self.db_name).mkdir(parents=True, exist_ok=True)
            (self.base_dir / "images" / self.db_name).mkdir(parents=True, exist_ok=True)
            (self.base_dir / "src" / self.db_name).mkdir(parents=True, exist_ok=True)
            (self.base_dir / "cnt").mkdir(exist_ok=True)
```

### Utilisation

```python
# Détection automatique
mode = DatabasePaths.detect_mode("data", "ma_famille")
paths = DatabasePaths("data", "ma_famille", mode)

# Création avec mode reorg
paths_reorg = DatabasePaths("data", "ma_nouvelle_base", DatabaseMode.REORG)
paths_reorg.create_structure()

# Accès aux chemins
print(paths.config_file)     # Adapté au mode
print(paths.portraits_dir)   # Adapté au mode
```

## 📝 Recommandation

Pour une nouvelle implémentation Python :

1. **Par défaut : Mode REORG** (plus moderne, plus propre)
2. **Support du mode Classic** pour compatibilité avec bases existantes
3. **Détection automatique** du mode à l'ouverture
4. **Option explicite** lors de la création (`--reorg` / `--classic`)

## 🔗 Références

- **Code Source** : `legacy/ocaml-old-project/lib/GWPARAM.ml`
- **Options** : `gwc -reorg`, `ged2gwb -reorg`
- **Détection** : Présence de `<base>.gwb/config/<base>.gwf`
