"""Tests for FamilyService."""

import tempfile
from pathlib import Path

import pytest

from backend.core.exceptions import DatabaseError, FamilyNotFoundError, PersonNotFoundError, ValidationError
from backend.core.models import Date, MaritalStatus, Sex
from backend.database.pickle_driver import PickleDriver
from backend.database.repository import Repository
from backend.services.family_service import FamilyService
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
    """Create family service."""
    return FamilyService(repository)


@pytest.fixture
def person_service(repository):
    """Create person service."""
    return PersonService(repository)


@pytest.fixture
def father(person_service):
    """Create father."""
    return person_service.create_person(
        first_name="John",
        surname="Doe",
        sex=Sex.MALE,
        check_duplicates=False,
    )


@pytest.fixture
def mother(person_service):
    """Create mother."""
    return person_service.create_person(
        first_name="Jane",
        surname="Smith",
        sex=Sex.FEMALE,
        check_duplicates=False,
    )


@pytest.fixture
def child(person_service):
    """Create child."""
    return person_service.create_person(
        first_name="Jimmy",
        surname="Doe",
        sex=Sex.MALE,
        check_duplicates=False,
    )


class TestFamilyServiceCreate:
    """Test family creation."""

    def test_create_family_with_parents(self, service, father, mother):
        """Test creating family with both parents."""
        family = service.create_family(
            father_id=father.id,
            mother_id=mother.id,
            marital_status=MaritalStatus.MARRIED,
        )

        assert family.father_id == father.id
        assert family.mother_id == mother.id
        assert family.marital_status == MaritalStatus.MARRIED

    def test_create_family_father_only(self, service, father):
        """Test creating family with father only."""
        family = service.create_family(father_id=father.id)

        assert family.father_id == father.id
        assert family.mother_id is None

    def test_create_family_mother_only(self, service, mother):
        """Test creating family with mother only."""
        family = service.create_family(mother_id=mother.id)

        assert family.father_id is None
        assert family.mother_id == mother.id

    def test_create_family_no_parents(self, service):
        """Test creating family without parents fails."""
        with pytest.raises(ValidationError) as exc:
            service.create_family()
        assert "parent" in str(exc.value).lower()

    def test_create_family_with_children(self, service, father, mother, child):
        """Test creating family with children."""
        family = service.create_family(
            father_id=father.id,
            mother_id=mother.id,
            children_ids=[child.id],
        )

        assert len(family.children_ids) == 1
        assert child.id in family.children_ids

    def test_create_family_wrong_father_sex(self, service, mother):
        """Test creating family with female father fails."""
        with pytest.raises(ValidationError) as exc:
            service.create_family(
                father_id=mother.id,  # Mother marked as father
                validate_parents=True,
            )
        assert "female" in str(exc.value).lower()

    def test_create_family_wrong_mother_sex(self, service, father):
        """Test creating family with male mother fails."""
        with pytest.raises(ValidationError) as exc:
            service.create_family(
                mother_id=father.id,  # Father marked as mother
                validate_parents=True,
            )
        assert "male" in str(exc.value).lower()

    def test_create_family_skip_sex_validation(self, service, father):
        """Test creating family without sex validation."""
        family = service.create_family(
            mother_id=father.id,  # Wrong sex but validation disabled
            validate_parents=False,
        )

        assert family.mother_id == father.id

    def test_create_family_with_marriage(self, service, father, mother):
        """Test creating family with marriage details."""
        marriage_date = Date(year=2000, month=6, day=15)

        family = service.create_family(
            father_id=father.id,
            mother_id=mother.id,
            marital_status=MaritalStatus.MARRIED,
            marriage_date=marriage_date,
            marriage_place="Paris",
        )

        assert family.marriage_date == marriage_date
        assert family.marriage_place == "Paris"

    def test_create_family_invalid_date_sequence(self, service, father, mother):
        """Test creating family with divorce before marriage fails."""
        with pytest.raises(ValidationError):
            service.create_family(
                father_id=father.id,
                mother_id=mother.id,
                marriage_date=Date(year=2000),
                divorce_date=Date(year=1999),
            )


class TestFamilyServiceUpdate:
    """Test family update."""

    def test_update_family_marital_status(self, service, father, mother):
        """Test updating family marital status."""
        family = service.create_family(
            father_id=father.id,
            mother_id=mother.id,
            marital_status=MaritalStatus.MARRIED,
        )

        updated = service.update_family(
            family.id,
            marital_status=MaritalStatus.DIVORCED,
            divorce_date=Date(year=2010),
        )

        assert updated.marital_status == MaritalStatus.DIVORCED
        assert updated.divorce_date.year == 2010

    def test_update_family_change_father(self, service, father, mother, person_service):
        """Test changing family father."""
        family = service.create_family(
            father_id=father.id,
            mother_id=mother.id,
        )

        new_father = person_service.create_person(
            first_name="Bob",
            surname="Johnson",
            sex=Sex.MALE,
            check_duplicates=False,
        )

        updated = service.update_family(
            family.id,
            father_id=new_father.id,
        )

        assert updated.father_id == new_father.id

    def test_update_family_not_found(self, service):
        """Test updating non-existent family fails."""
        with pytest.raises((DatabaseError, FamilyNotFoundError)):
            service.update_family("nonexistent", marital_status=MaritalStatus.MARRIED)


class TestFamilyServiceDelete:
    """Test family deletion."""

    def test_delete_family(self, service, repository, father, mother):
        """Test deleting family."""
        family = service.create_family(
            father_id=father.id,
            mother_id=mother.id,
        )

        service.delete_family(family.id, update_members=False)

        with pytest.raises((DatabaseError, FamilyNotFoundError)):
            repository.get_family(family.id)


class TestFamilyServiceChildren:
    """Test child management."""

    def test_add_child(self, service, father, mother, child):
        """Test adding child to family."""
        family = service.create_family(
            father_id=father.id,
            mother_id=mother.id,
        )

        updated = service.add_child(family.id, child.id)

        assert len(updated.children_ids) == 1
        assert child.id in updated.children_ids

    def test_add_child_duplicate(self, service, father, mother, child):
        """Test adding same child twice doesn't duplicate."""
        family = service.create_family(
            father_id=father.id,
            mother_id=mother.id,
            children_ids=[child.id],
        )

        updated = service.add_child(family.id, child.id)

        assert len(updated.children_ids) == 1

    def test_remove_child(self, service, father, mother, child):
        """Test removing child from family."""
        family = service.create_family(
            father_id=father.id,
            mother_id=mother.id,
            children_ids=[child.id],
        )

        updated = service.remove_child(family.id, child.id)

        assert len(updated.children_ids) == 0
        assert child.id not in updated.children_ids

    def test_add_child_not_found(self, service, father):
        """Test adding non-existent child fails."""
        family = service.create_family(father_id=father.id)

        with pytest.raises((DatabaseError, PersonNotFoundError)):
            service.add_child(family.id, "nonexistent")


class TestFamilyServiceStatistics:
    """Test family statistics."""

    def test_get_statistics(self, service, father, mother, child):
        """Test getting family statistics."""
        family = service.create_family(
            father_id=father.id,
            mother_id=mother.id,
            children_ids=[child.id],
            marital_status=MaritalStatus.MARRIED,
        )

        stats = service.get_family_statistics(family.id)

        assert stats["family_id"] == family.id
        assert stats["father_name"] == "John Doe"
        assert stats["mother_name"] == "Jane Smith"
        assert stats["children_count"] == 1
        assert stats["is_married"]
        assert stats["marital_status"] == "MARRIED"
