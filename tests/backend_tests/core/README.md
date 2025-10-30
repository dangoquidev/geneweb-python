# Tests Backend - Phase 1 (Core Domain)

## ✅ État actuel : **36 tests passés**

### Couverture des tests

#### 📊 Modules testés

| Module | Tests | Couverture | Statut |
|--------|-------|-----------|--------|
| `core/models.py` | 36 | ~85% | ✅ |
| `core/enums.py` | - | - | ⏳ À faire |
| `core/exceptions.py` | - | - | ⏳ À faire |

#### 🧪 Tests implémentés

**Date (10 tests)**
- ✅ Création de dates complètes et incomplètes
- ✅ Représentation textuelle
- ✅ Précisions (exact, about, before, after)
- ✅ Conversion vers/depuis Python date
- ✅ Dates avec texte libre

**Event (2 tests)**
- ✅ Création d'événements
- ✅ Représentation textuelle

**Person (11 tests)**
- ✅ Création minimale et complète
- ✅ Méthodes full_name() et display_name()
- ✅ Calcul d'âge au décès
- ✅ Statut vivant/décédé
- ✅ Gestion des événements

**Family (11 tests)**
- ✅ Création avec/sans parents
- ✅ Gestion des enfants
- ✅ Statut marié/divorcé
- ✅ Détails de mariage

**Note & Source (2 tests)**
- ✅ Création de notes
- ✅ Création de sources

**Intégration (2 tests)**
- ✅ Personne complète avec événements
- ✅ Famille complète avec tous les détails

## 🚀 Exécuter les tests

```bash
# Tous les tests de Phase 1
PYTHONPATH=src pytest tests/backend_tests/core/ -v

# Tests spécifiques
PYTHONPATH=src pytest tests/backend_tests/core/test_models.py -v

# Avec couverture
PYTHONPATH=src pytest tests/backend_tests/core/ --cov=backend.core --cov-report=html
```

## 📋 Prochains tests à implémenter

### Phase 1 (à compléter)
- [ ] `test_enums.py` - Tests des énumérations
- [ ] `test_exceptions.py` - Tests de la hiérarchie d'exceptions

### Phase 2 (Utils)
- [ ] `test_config.py`
- [ ] `test_string_utils.py`
- [ ] `test_date_utils.py`

### Phase 3 (Database)
- [ ] `test_pickle_driver.py`
- [ ] `test_repository.py`

### Phase 4 (Services)
- [ ] `test_person_service.py`
- [ ] `test_family_service.py`
- [ ] `test_search_service.py`

### Phase 5 (API)
- [ ] Tests d'intégration API
- [ ] Tests E2E

## 💡 Conventions de tests

- **Nommage** : `test_<module>_<fonction>_<scenario>`
- **Structure** : Arrange / Act / Assert
- **Isolation** : Chaque test doit être indépendant
- **Documentation** : Docstrings explicites sur chaque test
- **Fixtures** : Utiliser `conftest.py` pour les fixtures partagées

## 🎯 Objectifs de couverture

- **Phase 1** : 80%+ ✅
- **Phase 2-3** : 85%+
- **Phase 4-5** : 90%+

---

**Dernière mise à jour** : Phase 1 complète avec tests de base
