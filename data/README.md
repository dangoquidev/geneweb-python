# GenEWeb Data Directory

Ce répertoire contient les fichiers de bases de données GenEWeb au format pickle.

## Fichiers

- `showcase.pickle` - Base de données de démonstration (minimal pour Docker)
- `*.pickle` - Autres bases de données créées par l'utilisateur

## Format

Les fichiers `.pickle` contiennent des données sérialisées Python représentant :
- Une liste de personnes (persons)
- Une liste de familles (families)
- Des métadonnées sur la base

## Utilisation

```bash
# Lister les bases disponibles
make list-db

# Démarrer avec une base spécifique
python run_api.py --db data/ma_base.pickle

# Docker
docker run -v ./data:/app/data geneweb-python
```

## Sécurité

⚠️ **Important** : Les fichiers pickle peuvent exécuter du code arbitraire lors du chargement.
Ne chargez que des fichiers de sources fiables.
