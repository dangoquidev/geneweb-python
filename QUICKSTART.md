# 🚀 Guide de démarrage rapide GenEWeb

## Options de lancement

### 1. **API seule** (backend seulement)
```bash
make run
```
- ✅ Le plus simple
- 📚 Documentation: http://127.0.0.1:8000/api/docs
- 🎯 Idéal pour: Tests API, développement backend

### 2. **API + Frontend** (2 terminaux manuels)
```bash
# Terminal 1: Backend
make run

# Terminal 2: Frontend (dans un autre terminal)
cd src/frontend && pnpm dev
```
- ✅ Contrôle total
- 🎯 Idéal pour: Développement avec logs visibles

### 3. **Full-Stack avec tmux** (automatique)
```bash
make run-fullstack-tmux
```
- ✅ Tout en un seul command
- 🔄 Backend + Frontend démarrés automatiquement
- 📋 Gestion via tmux sessions

**Accès:**
- API: http://127.0.0.1:8000/api/docs
- Frontend: http://localhost:5173 (Vite) ou http://localhost:3000 (CRA)

**Gestion tmux:**
```bash
# Voir les logs API
tmux attach -t geneweb-api

# Voir les logs Frontend
tmux attach -t geneweb-frontend

# Arrêter tout
make stop-fullstack
```

### 4. **Mode développement** (avec auto-reload)
```bash
make run-dev
```
- 🔄 Auto-reload sur changements de code
- 🎯 Idéal pour: Développement actif

## 🛑 Arrêter les serveurs

```bash
# Arrêter les sessions tmux
make stop-fullstack

# Ou manuellement
pkill -f "run_api.py"
pkill -f "vite"
```

## 🔧 Dépannage

### Port 8000 déjà utilisé
```bash
# Trouver le processus
lsof -ti:8000

# Le tuer
kill -9 $(lsof -ti:8000)

# Relancer
make run
```

### Frontend ne démarre pas
```bash
# Installer les dépendances
cd src/frontend
pnpm install

# Vérifier la configuration
cat package.json
```

### Tmux ne fonctionne pas
```bash
# Installer tmux
sudo apt install tmux   # Ubuntu/Debian
sudo yum install tmux   # RedHat/CentOS
brew install tmux       # macOS

# Ou utiliser l'option manuelle (2 terminaux)
make run-fullstack
```

## 📊 Commandes de développement

```bash
# Tests
make test              # Tous les tests (295 tests)
make test-api          # Tests API uniquement

# Qualité du code
make format            # Formater le code
make check             # Vérifier la qualité
make all               # Format + Check + Test

# Base de données
make list-db           # Lister les bases disponibles
```

## 🆚 Comparaison des options

| Commande | Backend | Frontend | Terminals | Auto-reload | Recommandé pour |
|----------|---------|----------|-----------|-------------|-----------------|
| `make run` | ✅ | ❌ | 1 | ❌ | Tests API, backend dev |
| `make run-dev` | ✅ | ❌ | 1 | ✅ | Développement backend actif |
| `make run-fullstack` | ✅ | ⚠️ manuel | 2 | ❌ | Contrôle total, debug |
| `make run-fullstack-tmux` | ✅ | ✅ | 1 | ❌ | Production locale, démo |

## 💡 Workflow recommandé

### Développement backend
```bash
make run-dev          # Terminal 1: API avec auto-reload
# Développer dans votre éditeur
# L'API redémarre automatiquement
```

### Développement full-stack
```bash
make run              # Terminal 1: API
cd src/frontend       # Terminal 2: Frontend
pnpm dev              # Auto-reload Vite
```

### Démo/Présentation
```bash
make run-fullstack-tmux   # Tout démarre automatiquement
# Ouvrir http://localhost:5173
```

## 🐛 Debug

### Voir les logs API
```bash
# Si lancé avec tmux
tmux attach -t geneweb-api

# Si lancé directement
# Les logs s'affichent dans le terminal
```

### Voir les logs Frontend
```bash
# Si lancé avec tmux
tmux attach -t geneweb-frontend

# Si lancé directement
cd src/frontend && pnpm dev
```

### Mode verbose
```bash
# API avec logs détaillés
python run_api.py --port 8000 --db data/showcase.pickle --debug

# Frontend avec logs détaillés
cd src/frontend && pnpm dev --debug
```

## 📚 Prochaines étapes

1. **Première fois**: `make setup` pour installer les dépendances
2. **Tests**: `make test` pour vérifier que tout fonctionne
3. **Lancement**: `make run` pour démarrer l'API
4. **Documentation**: Visiter http://127.0.0.1:8000/api/docs
5. **Frontend**: Si besoin, lancer le frontend dans un autre terminal

## 🔗 Liens utiles

- API Documentation: http://127.0.0.1:8000/api/docs (Swagger)
- API Documentation (alt): http://127.0.0.1:8000/api/redoc (ReDoc)
- OpenAPI Schema: http://127.0.0.1:8000/api/openapi.json
- Frontend: http://localhost:5173 (Vite) ou http://localhost:3000 (CRA)

---

**Besoin d'aide ?** Consultez [API.md](API.md) pour la documentation complète de l'API.
