"""Tests for PersonService."""

import tempfile
from pathlib import Path

import pytest

from backend.core.exceptions import DatabaseError, PersonNotFoundError, ValidationError
from backend.core.models import Date, Event, EventType, Sex
from backend.database.pickle_driver import PickleDriver
from backend.database.repository import Repository
from backend.services.person_service import PersonService


@pytest.fixture
def temp_db():
    """Create temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".pickle", delete=False) as f:
        db_path = Path(f.name)

    # Delete the empty file - let the driver create it properly
    db_path.unlink()

    yield db_path

    if db_path.exists():
        db_path.unlink()
    backup_path = db_path.with_suffix(db_path.suffix + ".backup")
    if backup_path.exists():
        backup_path.unlink()


@pytest.fixture
def driver(temp_db):
    """Create database driver."""
    return PickleDriver(temp_db)


@pytest.fixture
def repository(driver):
    """Create repository."""
    return Repository(driver)


@pytest.fixture
def service(repository):
    """Create person service."""
    return PersonService(repository)


class TestPersonServiceCreate:
    """Test person creation."""

    def test_create_person_minimal(self, service):
        """Test creating person with minimal data."""
        person = service.create_person(
            first_name="John",
            surname="Doe",
            check_duplicates=False,
        )

        assert person.first_name == "John"
        assert person.surname == "Doe"
        assert person.sex == Sex.UNKNOWN
        assert person.id is not None

    def test_create_person_full(self, service):
        """Test creating person with full data."""
        birth_date = Date(year=1980, month=5, day=15)
        death_date = Date(year=2050, month=12, day=31)

        person = service.create_person(
            first_name="Marie",
            surname="Curie",
            sex=Sex.FEMALE,
            birth_date=birth_date,
            birth_place="Warsaw, Poland",
            death_date=death_date,
            death_place="Paris, France",
            check_duplicates=False,
        )

        assert person.first_name == "Marie"
        assert person.surname == "Curie"
        assert person.sex == Sex.FEMALE
        assert person.birth_date == birth_date
        assert person.birth_place == "Warsaw, Poland"
        assert person.death_date == death_date
        assert person.death_place == "Paris, France"

    def test_create_person_empty_first_name(self, service):
        """Test creating person with empty first name fails."""
        with pytest.raises(ValidationError) as exc:
            service.create_person(
                first_name="",
                surname="Doe",
            )
        assert "first_name" in str(exc.value).lower()

    def test_create_person_empty_surname(self, service):
        """Test creating person with empty surname fails."""
        with pytest.raises(ValidationError) as exc:
            service.create_person(
                first_name="John",
                surname="",
            )
        assert "surname" in str(exc.value).lower()

    def test_create_person_capitalizes_names(self, service):
        """Test that names are properly capitalized."""
        person = service.create_person(
            first_name="jean-paul",
            surname="de la fontaine",
            check_duplicates=False,
        )

        assert person.first_name == "Jean-Paul"
        # French particles like "la" stay lowercase
        assert person.surname == "De la Fontaine"

    def test_create_person_invalid_date_sequence(self, service):
        """Test creating person with death before birth fails."""
        with pytest.raises(ValidationError) as exc:
            service.create_person(
                first_name="John",
                surname="Doe",
                birth_date=Date(year=2000),
                death_date=Date(year=1999),
                check_duplicates=False,
            )
        assert "death" in str(exc.value).lower()

    def test_create_person_duplicate_detection(self, service):
        """Test duplicate detection."""
        # Create first person
        service.create_person(
            first_name="John",
            surname="Smith",
            birth_date=Date(year=1980),
            check_duplicates=False,
        )

        # Try to create duplicate
        with pytest.raises(ValidationError) as exc:
            service.create_person(
                first_name="John",
                surname="Smith",
                birth_date=Date(year=1980),
                check_duplicates=True,
            )
        assert "duplicate" in str(exc.value).lower()

    def test_create_person_skip_duplicate_check(self, service):
        """Test skipping duplicate check."""
        # Create first person
        service.create_person(
            first_name="John",
            surname="Smith",
            check_duplicates=False,
        )

        # Create duplicate with check disabled
        person2 = service.create_person(
            first_name="John",
            surname="Smith",
            check_duplicates=False,
        )

        assert person2.first_name == "John"
        assert person2.surname == "Smith"


class TestPersonServiceUpdate:
    """Test person update."""

    def test_update_person_names(self, service):
        """Test updating person names."""
        person = service.create_person(
            first_name="John",
            surname="Doe",
            check_duplicates=False,
        )

        updated = service.update_person(
            person.id,
            first_name="Jane",
            surname="Smith",
        )

        assert updated.first_name == "Jane"
        assert updated.surname == "Smith"

    def test_update_person_dates(self, service):
        """Test updating person dates."""
        person = service.create_person(
            first_name="John",
            surname="Doe",
            check_duplicates=False,
        )

        birth_date = Date(year=1980, month=5, day=15)
        updated = service.update_person(
            person.id,
            birth_date=birth_date,
            birth_place="New York",
        )

        assert updated.birth_date == birth_date
        assert updated.birth_place == "New York"

    def test_update_person_empty_first_name(self, service):
        """Test updating with empty first name fails."""
        person = service.create_person(
            first_name="John",
            surname="Doe",
            check_duplicates=False,
        )

        with pytest.raises(ValidationError):
            service.update_person(person.id, first_name="")

    def test_update_person_empty_surname(self, service):
        """Test updating with empty surname fails."""
        person = service.create_person(
            first_name="John",
            surname="Doe",
            check_duplicates=False,
        )

        with pytest.raises(ValidationError):
            service.update_person(person.id, surname="")

    def test_update_person_invalid_date_sequence(self, service):
        """Test updating with invalid date sequence fails."""
        person = service.create_person(
            first_name="John",
            surname="Doe",
            birth_date=Date(year=2000),
            check_duplicates=False,
        )

        with pytest.raises(ValidationError):
            service.update_person(
                person.id,
                death_date=Date(year=1999),
            )

    def test_update_person_not_found(self, service):
        """Test updating non-existent person fails."""
        with pytest.raises((DatabaseError, PersonNotFoundError)):
            service.update_person("nonexistent", first_name="Jane")


class TestPersonServiceDelete:
    """Test person deletion."""

    def test_delete_person_simple(self, service, repository):
        """Test deleting person."""
        person = service.create_person(
            first_name="John",
            surname="Doe",
            check_duplicates=False,
        )

        service.delete_person(person.id, remove_from_families=False)

        with pytest.raises((DatabaseError, PersonNotFoundError)):
            repository.get_person(person.id)

    def test_delete_person_not_found(self, service):
        """Test deleting non-existent person fails."""
        with pytest.raises((DatabaseError, PersonNotFoundError)):
            service.delete_person("nonexistent")


class TestPersonServiceDuplicates:
    """Test duplicate detection."""

    def test_find_duplicates_exact_match(self, service):
        """Test finding exact duplicate."""
        service.create_person(
            first_name="John",
            surname="Smith",
            birth_date=Date(year=1980),
            check_duplicates=False,
        )

        duplicates = service.find_potential_duplicates(
            first_name="John",
            surname="Smith",
            birth_date=Date(year=1980),
        )

        assert len(duplicates) == 1
        assert duplicates[0].first_name == "John"
        assert duplicates[0].surname == "Smith"

    def test_find_duplicates_similar_name(self, service):
        """Test finding similar name."""
        service.create_person(
            first_name="Jon",
            surname="Smith",
            birth_date=Date(year=1980),
            check_duplicates=False,
        )

        duplicates = service.find_potential_duplicates(
            first_name="John",
            surname="Smith",
            birth_date=Date(year=1980),
            threshold=0.75,
        )

        assert len(duplicates) >= 1

    def test_find_duplicates_no_match(self, service):
        """Test no duplicates found."""
        service.create_person(
            first_name="John",
            surname="Smith",
            check_duplicates=False,
        )

        duplicates = service.find_potential_duplicates(
            first_name="Jane",
            surname="Doe",
        )

        assert len(duplicates) == 0


class TestPersonServiceEvents:
    """Test event management."""

    def test_add_event(self, service):
        """Test adding event to person."""
        person = service.create_person(
            first_name="John",
            surname="Doe",
            check_duplicates=False,
        )

        event = Event(
            event_type=EventType.BAPTISM,
            date=Date(year=1980, month=6, day=1),
            place="Church",
        )

        updated = service.add_event(person.id, event)

        assert len(updated.events) == 1
        assert updated.events[0].event_type == EventType.BAPTISM


class TestPersonServiceStatistics:
    """Test person statistics."""

    def test_get_statistics(self, service, repository):
        """Test getting person statistics."""
        person = service.create_person(
            first_name="John",
            surname="Doe",
            birth_date=Date(year=1980),
            death_date=Date(year=2050),
            check_duplicates=False,
        )

        stats = service.get_person_statistics(person.id)

        assert stats["person_id"] == person.id
        assert stats["full_name"] == "John Doe"
        assert stats["age"] == 70
        assert stats["is_alive"] is False
        assert stats["families_count"] == 0
        assert stats["children_count"] == 0
