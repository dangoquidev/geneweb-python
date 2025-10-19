"""
Tests pour Repository.

Tests de CRUD, recherche, relations familiales, validation.
"""

import tempfile
from pathlib import Path

import pytest

from backend.core.enums import Sex
from backend.core.exceptions import FamilyNotFoundError, PersonNotFoundError, ValidationError
from backend.core.models import Date, Family, Person
from backend.database.pickle_driver import PickleDriver
from backend.database.repository import Repository


@pytest.fixture
def temp_db():
    """Crée un repository temporaire."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.pickle"
        driver = PickleDriver(db_path)
        repo = Repository(driver)
        yield repo


@pytest.fixture
def populated_repo():
    """Crée un repository avec des données."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.pickle"
        driver = PickleDriver(db_path)
        repo = Repository(driver)

        # Ajouter des personnes
        p1 = Person(id="P1", first_name="Jean", surname="Dupont", sex=Sex.MALE, birth_date=Date(year=1950))
        p2 = Person(id="P2", first_name="Marie", surname="Martin", sex=Sex.FEMALE, birth_date=Date(year=1952))
        p3 = Person(
            id="P3", first_name="Pierre", surname="Dupont", sex=Sex.MALE, birth_date=Date(year=1976), family_id="F1"
        )
        p4 = Person(
            id="P4", first_name="Sophie", surname="Dupont", sex=Sex.FEMALE, birth_date=Date(year=1978), family_id="F1"
        )

        repo.add_person(p1)
        repo.add_person(p2)
        repo.add_person(p3)
        repo.add_person(p4)

        # Ajouter une famille
        f1 = Family(id="F1", father_id="P1", mother_id="P2", marriage_date=Date(year=1975), children_ids=["P3", "P4"])
        repo.add_family(f1)

        yield repo


class TestRepositoryInit:
    """Tests d'initialisation."""

    def test_init_empty_database(self, temp_db):
        """Test initialisation avec base vide."""
        assert not temp_db.is_dirty()
        assert len(temp_db.get_all_persons()) == 0
        assert len(temp_db.get_all_families()) == 0

    def test_init_loads_existing(self):
        """Test initialisation charge une base existante."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.pickle"
            driver = PickleDriver(db_path)

            # Créer et sauvegarder des données
            repo1 = Repository(driver)
            p1 = Person(id="P1", first_name="Jean", surname="Dupont", sex=Sex.MALE)
            repo1.add_person(p1)
            repo1.save()

            # Créer nouveau repository (doit charger les données)
            repo2 = Repository(PickleDriver(db_path))
            assert len(repo2.get_all_persons()) == 1
            assert repo2.get_person("P1").first_name == "Jean"


class TestRepositoryLoadSave:
    """Tests de chargement et sauvegarde."""

    def test_save_and_load(self, temp_db):
        """Test sauvegarder puis recharger."""
        p1 = Person(id="P1", first_name="Jean", surname="Dupont", sex=Sex.MALE)
        temp_db.add_person(p1)

        assert temp_db.is_dirty()
        temp_db.save()
        assert not temp_db.is_dirty()

        # Recharger
        temp_db.load()
        assert len(temp_db.get_all_persons()) == 1

    def test_dirty_flag(self, temp_db):
        """Test le flag dirty."""
        assert not temp_db.is_dirty()

        p1 = Person(id="P1", first_name="Jean", surname="Dupont", sex=Sex.MALE)
        temp_db.add_person(p1)
        assert temp_db.is_dirty()

        temp_db.save()
        assert not temp_db.is_dirty()


class TestRepositoryPersonCRUD:
    """Tests CRUD sur les personnes."""

    def test_add_person(self, temp_db):
        """Test ajouter une personne."""
        p1 = Person(id="P1", first_name="Jean", surname="Dupont", sex=Sex.MALE)
        temp_db.add_person(p1)

        assert len(temp_db.get_all_persons()) == 1
        assert temp_db.get_person("P1").first_name == "Jean"

    def test_add_person_without_id(self, temp_db):
        """Test ajouter une personne sans ID."""
        p1 = Person(id="", first_name="Jean", surname="Dupont", sex=Sex.MALE)
        with pytest.raises(ValidationError) as exc_info:
            temp_db.add_person(p1)
        assert "must have an ID" in str(exc_info.value)

    def test_add_person_duplicate_id(self, temp_db):
        """Test ajouter une personne avec ID existant."""
        p1 = Person(id="P1", first_name="Jean", surname="Dupont", sex=Sex.MALE)
        temp_db.add_person(p1)

        p2 = Person(id="P1", first_name="Pierre", surname="Martin", sex=Sex.MALE)
        with pytest.raises(ValidationError) as exc_info:
            temp_db.add_person(p2)
        assert "already exists" in str(exc_info.value)

    def test_get_person(self, populated_repo):
        """Test récupérer une personne."""
        person = populated_repo.get_person("P1")
        assert person.first_name == "Jean"
        assert person.surname == "Dupont"

    def test_get_person_not_found(self, temp_db):
        """Test récupérer une personne inexistante."""
        with pytest.raises(PersonNotFoundError):
            temp_db.get_person("P999")

    def test_get_all_persons(self, populated_repo):
        """Test récupérer toutes les personnes."""
        persons = populated_repo.get_all_persons()
        assert len(persons) == 4
        assert "P1" in persons
        assert "P2" in persons

    def test_update_person(self, populated_repo):
        """Test mettre à jour une personne."""
        person = populated_repo.get_person("P1")
        person.first_name = "Jacques"
        populated_repo.update_person(person)

        updated = populated_repo.get_person("P1")
        assert updated.first_name == "Jacques"

    def test_update_person_not_found(self, temp_db):
        """Test mettre à jour une personne inexistante."""
        p1 = Person(id="P999", first_name="Jean", surname="Dupont", sex=Sex.MALE)
        with pytest.raises(PersonNotFoundError):
            temp_db.update_person(p1)

    def test_delete_person(self, populated_repo):
        """Test supprimer une personne."""
        populated_repo.delete_person("P1")
        assert len(populated_repo.get_all_persons()) == 3

        with pytest.raises(PersonNotFoundError):
            populated_repo.get_person("P1")

    def test_delete_person_not_found(self, temp_db):
        """Test supprimer une personne inexistante."""
        with pytest.raises(PersonNotFoundError):
            temp_db.delete_person("P999")


class TestRepositoryFamilyCRUD:
    """Tests CRUD sur les familles."""

    def test_add_family(self, temp_db):
        """Test ajouter une famille."""
        f1 = Family(id="F1", father_id="P1", mother_id="P2", children_ids=[])
        temp_db.add_family(f1)

        assert len(temp_db.get_all_families()) == 1
        assert temp_db.get_family("F1").father_id == "P1"

    def test_add_family_without_id(self, temp_db):
        """Test ajouter une famille sans ID."""
        f1 = Family(id="", father_id="P1", mother_id="P2", children_ids=[])
        with pytest.raises(ValidationError) as exc_info:
            temp_db.add_family(f1)
        assert "must have an ID" in str(exc_info.value)

    def test_add_family_duplicate_id(self, temp_db):
        """Test ajouter une famille avec ID existant."""
        f1 = Family(id="F1", father_id="P1", mother_id="P2", children_ids=[])
        temp_db.add_family(f1)

        f2 = Family(id="F1", father_id="P3", mother_id="P4", children_ids=[])
        with pytest.raises(ValidationError) as exc_info:
            temp_db.add_family(f2)
        assert "already exists" in str(exc_info.value)

    def test_get_family(self, populated_repo):
        """Test récupérer une famille."""
        family = populated_repo.get_family("F1")
        assert family.father_id == "P1"
        assert family.mother_id == "P2"

    def test_get_family_not_found(self, temp_db):
        """Test récupérer une famille inexistante."""
        with pytest.raises(FamilyNotFoundError):
            temp_db.get_family("F999")

    def test_get_all_families(self, populated_repo):
        """Test récupérer toutes les familles."""
        families = populated_repo.get_all_families()
        assert len(families) == 1
        assert "F1" in families

    def test_update_family(self, populated_repo):
        """Test mettre à jour une famille."""
        family = populated_repo.get_family("F1")
        family.marriage_date = Date(year=1980)
        populated_repo.update_family(family)

        updated = populated_repo.get_family("F1")
        assert updated.marriage_date.year == 1980

    def test_update_family_not_found(self, temp_db):
        """Test mettre à jour une famille inexistante."""
        f1 = Family(id="F999", father_id="P1", mother_id="P2", children_ids=[])
        with pytest.raises(FamilyNotFoundError):
            temp_db.update_family(f1)

    def test_delete_family(self, populated_repo):
        """Test supprimer une famille."""
        populated_repo.delete_family("F1")
        assert len(populated_repo.get_all_families()) == 0

        with pytest.raises(FamilyNotFoundError):
            populated_repo.get_family("F1")

    def test_delete_family_not_found(self, temp_db):
        """Test supprimer une famille inexistante."""
        with pytest.raises(FamilyNotFoundError):
            temp_db.delete_family("F999")


class TestRepositorySearch:
    """Tests de recherche."""

    def test_search_persons_by_last_name(self, populated_repo):
        """Test rechercher par nom."""
        results = populated_repo.search_persons("Dupont")
        assert len(results) == 3  # Jean, Pierre, Sophie
        assert all(p.surname == "Dupont" for p in results)

    def test_search_persons_by_first_name(self, populated_repo):
        """Test rechercher par prénom."""
        results = populated_repo.search_persons("Marie", search_in=["first_name"])
        assert len(results) == 1
        assert results[0].first_name == "Marie"

    def test_search_persons_fuzzy(self, populated_repo):
        """Test recherche floue."""
        results = populated_repo.search_persons("Dupond", fuzzy=True, threshold=0.7)
        # Devrait trouver "Dupont" avec fuzzy match
        assert len(results) > 0

    def test_search_persons_exact(self, populated_repo):
        """Test recherche exacte."""
        results = populated_repo.search_persons("Dupont", fuzzy=False)
        assert len(results) == 3

    def test_search_persons_no_results(self, populated_repo):
        """Test recherche sans résultats."""
        results = populated_repo.search_persons("Nonexistent")
        assert len(results) == 0

    def test_get_persons_by_name_exact(self, populated_repo):
        """Test recherche par nom exact."""
        results = populated_repo.get_persons_by_name(first_name="Jean", surname="Dupont", exact=True)
        assert len(results) == 1
        assert results[0].id == "P1"

    def test_get_persons_by_name_partial(self, populated_repo):
        """Test recherche par nom partielle."""
        results = populated_repo.get_persons_by_name(surname="Dup", exact=False)
        assert len(results) == 3  # Tous les Dupont

    def test_get_persons_by_name_only_first(self, populated_repo):
        """Test recherche seulement par prénom."""
        results = populated_repo.get_persons_by_name(first_name="Jean")
        assert len(results) == 1
        assert results[0].first_name == "Jean"

    def test_get_persons_by_name_only_last(self, populated_repo):
        """Test recherche seulement par nom."""
        results = populated_repo.get_persons_by_name(surname="Martin")
        assert len(results) == 1
        assert results[0].surname == "Martin"

    def test_get_persons_by_sex(self, populated_repo):
        """Test recherche par sexe."""
        males = populated_repo.get_persons_by_sex(Sex.MALE)
        females = populated_repo.get_persons_by_sex(Sex.FEMALE)

        assert len(males) == 2  # Jean, Pierre
        assert len(females) == 2  # Marie, Sophie


class TestRepositoryRelations:
    """Tests des relations familiales."""

    def test_get_person_families(self, populated_repo):
        """Test récupérer les familles d'une personne (en tant que parent)."""
        families = populated_repo.get_person_families("P1")
        assert len(families) == 1
        assert families[0].id == "F1"

    def test_get_person_families_no_families(self, populated_repo):
        """Test récupérer familles d'une personne sans famille."""
        families = populated_repo.get_person_families("P3")
        assert len(families) == 0

    def test_get_person_parents(self, populated_repo):
        """Test récupérer les parents d'une personne."""
        father, mother = populated_repo.get_person_parents("P3")
        assert father is not None
        assert mother is not None
        assert father.id == "P1"
        assert mother.id == "P2"

    def test_get_person_parents_no_family(self, populated_repo):
        """Test récupérer parents d'une personne sans famille."""
        father, mother = populated_repo.get_person_parents("P1")
        assert father is None
        assert mother is None

    def test_get_person_children(self, populated_repo):
        """Test récupérer les enfants d'une personne."""
        children = populated_repo.get_person_children("P1")
        assert len(children) == 2
        assert any(c.id == "P3" for c in children)
        assert any(c.id == "P4" for c in children)

    def test_get_person_children_no_children(self, populated_repo):
        """Test récupérer enfants d'une personne sans enfant."""
        children = populated_repo.get_person_children("P3")
        assert len(children) == 0

    def test_get_person_siblings(self, populated_repo):
        """Test récupérer les frères et sœurs."""
        siblings = populated_repo.get_person_siblings("P3")
        assert len(siblings) == 1
        assert siblings[0].id == "P4"

    def test_get_person_siblings_no_siblings(self, populated_repo):
        """Test récupérer frères/sœurs d'une personne sans fratrie."""
        siblings = populated_repo.get_person_siblings("P1")
        assert len(siblings) == 0


class TestRepositoryStatistics:
    """Tests de statistiques."""

    def test_get_statistics(self, populated_repo):
        """Test calculer les statistiques."""
        stats = populated_repo.get_statistics()
        assert stats["total_persons"] == 4
        assert stats["total_families"] == 1
        assert stats["male_count"] == 2
        assert stats["female_count"] == 2
        assert stats["unknown_sex_count"] == 0

    def test_get_statistics_empty(self, temp_db):
        """Test statistiques sur base vide."""
        stats = temp_db.get_statistics()
        assert stats["total_persons"] == 0
        assert stats["total_families"] == 0


class TestRepositoryValidation:
    """Tests de validation."""

    def test_validate_valid(self, populated_repo):
        """Test valider une base valide."""
        valid, errors = populated_repo.validate()
        assert valid
        assert len(errors) == 0

    def test_validate_after_save_load(self, populated_repo):
        """Test validation après save/load."""
        populated_repo.save()
        populated_repo.load()

        valid, errors = populated_repo.validate()
        assert valid
        assert len(errors) == 0
