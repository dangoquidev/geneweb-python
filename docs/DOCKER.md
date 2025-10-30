# 🐳 GenEWeb Docker Setup

Ce guide vous permet de lancer GenEWeb avec Docker facilement, sans avoir à installer Python, Node.js ou les dépendances localement.

## 🚀 Démarrage rapide

### Prérequis
- Docker et Docker Compose installés
- 4 Go de RAM disponible
- Ports 8000, 5173, 2316, 2317 libres

### 1. Construction de l'image
```bash
# Méthode 1: Avec le script helper (recommandé)
./docker-run.sh build

# Méthode 2: Avec Docker directement
docker build -t geneweb-python:latest .

# Méthode 3: Avec Make
make docker-build
```

### 2. Lancement des services

#### API seulement (production)
```bash
./docker-run.sh start
# ou
make docker-start
```
→ **API**: http://localhost:8000/api/docs

#### Développement complet (API + Frontend)
```bash
./docker-run.sh dev
# ou
make docker-dev
```
→ **API**: http://localhost:8000/api/docs
→ **Frontend**: http://localhost:5173

#### Fullstack avec tmux (équivalent `make run-fullstack-tmux`)
```bash
./docker-run.sh fullstack
# ou
make docker-fullstack
```
→ **API**: http://localhost:8001/api/docs
→ **Frontend**: http://localhost:5174

#### Avec admin panel legacy
```bash
./docker-run.sh admin
```
→ **API**: http://localhost:8000/api/docs
→ **Admin**: http://localhost:2316

## 📋 Commandes disponibles

### Via script helper `./docker-run.sh`
```bash
./docker-run.sh build           # Construire l'image
./docker-run.sh start           # API seulement
./docker-run.sh dev             # Mode développement
./docker-run.sh fullstack       # Fullstack tmux
./docker-run.sh admin           # Avec admin panel
./docker-run.sh stop            # Arrêter tous les services
./docker-run.sh restart         # Redémarrer
./docker-run.sh logs            # Voir les logs
./docker-run.sh logs --follow   # Suivre les logs en temps réel
./docker-run.sh shell           # Shell dans le conteneur
./docker-run.sh status          # Statut des conteneurs
./docker-run.sh clean           # Nettoyer tout
./docker-run.sh help            # Aide complète
```

### Via Make
```bash
make docker-build      # Construire l'image
make docker-start      # Démarrer (API seulement)
make docker-dev        # Mode développement
make docker-fullstack  # Fullstack avec tmux
make docker-stop       # Arrêter les services
make docker-logs       # Voir les logs
make docker-shell      # Shell dans le conteneur
make docker-status     # Statut
make docker-clean      # Nettoyer
```

### Via Docker Compose directement
```bash
# Services de base
docker-compose up -d                    # API seulement
docker-compose --profile dev up -d      # Mode développement
docker-compose --profile admin up -d    # Avec admin panel
docker-compose --profile fullstack up -d # Fullstack tmux

# Gestion
docker-compose down                     # Arrêter
docker-compose logs -f                  # Logs temps réel
docker-compose ps                       # Statut
```

## 🔧 Configuration

### Variables d'environnement
```bash
# Dans docker-compose.yml ou .env
GENEWEB_DATABASE_PATH=/app/data/showcase.pickle  # Base de données
GENEWEB_DEBUG=true                               # Mode debug
PYTHONPATH=/app/src                              # Path Python
```

### Volumes persistants
- `./data:/app/data:rw` - Données des bases (persistant)
- `./logs:/app/logs:rw` - Logs de l'application (persistant)
- `./src:/app/src:ro` - Code source (lecture seule, dev)

### Ports exposés
- **8000** - API FastAPI principale
- **5173** - Frontend Vite dev server
- **2316** - Admin panel legacy
- **2317** - Admin panel legacy (fullstack)
- **8001** - API FastAPI (mode fullstack)
- **5174** - Frontend dev server (mode fullstack)

## 🛠️ Développement

### Shell dans le conteneur
```bash
./docker-run.sh shell
# Dans le conteneur:
python --version
make status
make test
```

### Logs en temps réel
```bash
./docker-run.sh logs --follow
# ou
docker-compose logs -f
```

### Reconstruire après des changements
```bash
./docker-run.sh start --build
# ou
./docker-run.sh dev --build
```

### Développement avec volumes
Le mode développement monte `./src` en lecture seule pour voir les changements sans rebuild.

## 📊 Health checks

L'API expose un endpoint de santé pour Docker :
- **Health check**: http://localhost:8000/api/health
- **Status détaillé**: http://localhost:8000/api/status

Docker vérifie automatiquement la santé du conteneur.

## 🗄️ Bases de données

Les bases de données sont dans `./data/` :
- `showcase.pickle` - Base de démonstration (par défaut)
- `ma_famille.pickle` - Base famille exemple
- `ged.pickle` - Base importée depuis GEDCOM

Pour utiliser une autre base :
```bash
# Modifier GENEWEB_DATABASE_PATH dans docker-compose.yml
GENEWEB_DATABASE_PATH=/app/data/ma_famille.pickle
```

## 🚨 Dépannage

### Le conteneur ne démarre pas
```bash
./docker-run.sh logs          # Voir les erreurs
./docker-run.sh status        # Statut des conteneurs
docker system prune           # Nettoyer Docker
```

### Port déjà utilisé
```bash
# Vérifier les ports en cours d'utilisation
netstat -tulpn | grep :8000
# ou
lsof -i :8000

# Arrêter les services conflictuels
./docker-run.sh stop
```

### Problèmes de build
```bash
# Nettoyer et reconstruire
./docker-run.sh clean
./docker-run.sh build
```

### Accès aux logs
```bash
# Logs de tous les services
docker-compose logs

# Logs d'un service spécifique
docker-compose logs geneweb-app
docker-compose logs geneweb-frontend-dev

# Logs temps réel
docker-compose logs -f geneweb-app
```

## 🔄 Migration depuis le développement local

Si vous développiez localement sans Docker :

1. **Sauvegarder vos données** :
   ```bash
   cp -r data/ data-backup/
   ```

2. **Arrêter les services locaux** :
   ```bash
   make stop-fullstack  # Si vous utilisiez tmux
   # ou Ctrl+C sur vos serveurs
   ```

3. **Lancer avec Docker** :
   ```bash
   ./docker-run.sh build
   ./docker-run.sh dev
   ```

4. **Vérifier** que vos données sont bien accessibles dans le conteneur.

## 📈 Performance

### Ressources recommandées
- **RAM**: 2-4 Go minimum
- **CPU**: 2 cores minimum
- **Disque**: 5 Go d'espace libre

### Optimisations
- Le build multi-stage optimise la taille de l'image
- Les volumes nommés accélèrent les accès aux `node_modules`
- Le cache Docker réutilise les layers pour des builds plus rapides

## 🆘 Support

- **Logs détaillés** : `./docker-run.sh logs --follow`
- **Shell debug** : `./docker-run.sh shell`
- **Status complet** : `./docker-run.sh status`
- **Aide complète** : `./docker-run.sh help`

Pour plus d'informations sur GenEWeb, voir [README.md](README.md) et [CONTRIBUTING.md](CONTRIBUTING.md).
