"""
Tests for legacy database migration.

These tests verify that the system can load and migrate
legacy pickle databases with dict-based data to modern
Person/Family objects.
"""

from pathlib import Path

import pytest

from backend.core.models import Family, Person, Sex
from backend.database.pickle_driver import PickleDriver, _migrate_dict_to_family, _migrate_dict_to_person
from backend.database.repository import Repository


class TestLegacyMigration:
    """Test migration from legacy dict format to modern objects."""

    def test_migrate_dict_to_person_simple(self):
        """Test migration of simple person dict."""
        legacy_data = {
            "key_index": "P001",
            "first_name": "John",
            "surname": "Doe",
            "sex": "Male",
            "birth_date": {"year": 1990, "month": 5, "day": 15},
            "birth_place": "Paris",
        }

        person = _migrate_dict_to_person(legacy_data)

        assert isinstance(person, Person)
        assert person.id == "P001"
        assert person.first_name == "John"
        assert person.surname == "Doe"
        assert person.sex == Sex.MALE
        assert person.birth_date.year == 1990
        assert person.birth_place == "Paris"

    def test_migrate_dict_to_person_complex_id(self):
        """Test migration of person with complex ID dict."""
        legacy_data = {
            "key_index": {"id": "P1", "name_key": "John Doe 1990"},
            "first_name": "John",
            "surname": "Doe",
        }

        person = _migrate_dict_to_person(legacy_data)

        assert isinstance(person, Person)
        assert person.id == "P1"  # Should extract 'id' from dict
        assert person.first_name == "John"

    def test_migrate_dict_to_person_complex_sex(self):
        """Test migration of person with complex sex dict."""
        legacy_data = {
            "key_index": "P001",
            "first_name": "Jane",
            "surname": "Smith",
            "sex": {"value": "Female", "pronouns": "she/her"},
        }

        person = _migrate_dict_to_person(legacy_data)

        assert isinstance(person, Person)
        assert person.sex == Sex.FEMALE  # Should extract 'value' and map to enum

    def test_migrate_dict_to_family_simple(self):
        """Test migration of simple family dict."""
        legacy_data = {
            "key_index": "F001",
            "father_id": "P001",
            "mother_id": "P002",
            "children_ids": ["P003", "P004"],
            "marriage_date": {"year": 2010, "month": 6, "day": 15},
        }

        family = _migrate_dict_to_family(legacy_data)

        assert isinstance(family, Family)
        assert family.id == "F001"
        assert family.father_id == "P001"
        assert family.mother_id == "P002"
        assert len(family.children_ids) == 2

    def test_load_real_showcase_database(self):
        """Test loading the actual showcase.pickle database."""
        db_path = Path("data/showcase.pickle")

        if not db_path.exists():
            pytest.skip("showcase.pickle not found")

        # This should not raise an exception
        driver = PickleDriver(db_path)
        data = driver.load()

        assert "persons" in data
        assert "families" in data

        # Verify all persons are Person objects, not dicts
        for person_id, person in data["persons"].items():
            assert isinstance(person, Person), f"Person {person_id} is not a Person object: {type(person)}"
            assert isinstance(person.id, str), f"Person ID should be string, got {type(person.id)}"

            # Verify sex is an enum, not a dict
            if person.sex is not None:
                assert isinstance(person.sex, Sex), f"Sex should be Sex enum, got {type(person.sex)}"

        # Verify all families are Family objects
        for family_id, family in data["families"].items():
            assert isinstance(family, Family), f"Family {family_id} is not a Family object: {type(family)}"

    def test_repository_with_legacy_database(self):
        """Test that Repository can work with migrated legacy data."""
        db_path = Path("data/showcase.pickle")

        if not db_path.exists():
            pytest.skip("showcase.pickle not found")

        # Should load without errors
        repository = Repository(PickleDriver(db_path))

        # Should be able to get all persons
        persons = repository.get_all_persons()
        assert len(persons) > 0

        # All persons should be Person objects
        for person_id, person in persons.items():
            assert isinstance(person, Person)
            assert hasattr(person, "full_name")

            # Should be able to call methods
            full_name = person.full_name()
            assert isinstance(full_name, str)


class TestMigrationEdgeCases:
    """Test edge cases in migration."""

    def test_migrate_person_with_none_values(self):
        """Test migration with None/missing values."""
        legacy_data = {
            "key_index": "P001",
            "first_name": "John",
            "surname": "Doe",
            # No sex, no dates
        }

        person = _migrate_dict_to_person(legacy_data)

        assert person.id == "P001"
        assert person.sex == Sex.UNKNOWN  # Sex defaults to UNKNOWN when not provided
        assert person.birth_date is None

    def test_migrate_person_with_incomplete_date(self):
        """Test migration with incomplete date (year only)."""
        legacy_data = {
            "key_index": "P001",
            "first_name": "John",
            "surname": "Doe",
            "birth_date": {"year": 1990},  # No month/day
        }

        person = _migrate_dict_to_person(legacy_data)

        assert person.birth_date.year == 1990
        assert person.birth_date.month is None
        assert person.birth_date.day is None

    def test_migrate_family_with_complex_id(self):
        """Test migration of family with complex ID dict."""
        legacy_data = {"key_index": {"id": "F1", "name_key": "Doe Family"}, "father_id": "P001", "children_ids": []}

        family = _migrate_dict_to_family(legacy_data)

        assert family.id == "F1"
