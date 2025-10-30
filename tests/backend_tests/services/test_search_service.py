"""Tests for SearchService."""

import tempfile
from pathlib import Path

import pytest

from backend.core.exceptions import ValidationError
from backend.core.models import Date, Sex
from backend.database.pickle_driver import PickleDriver
from backend.database.repository import Repository
from backend.services.family_service import FamilyService
from backend.services.person_service import PersonService
from backend.services.search_service import SearchFilters, SearchService


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
    """Create search service."""
    return SearchService(repository)


@pytest.fixture
def person_service(repository):
    """Create person service."""
    return PersonService(repository)


@pytest.fixture
def family_service(repository):
    """Create family service."""
    return FamilyService(repository)


@pytest.fixture
def sample_persons(person_service):
    """Create sample persons for testing."""
    persons = []

    # Create diverse set of persons
    persons.append(
        person_service.create_person(
            first_name="John",
            surname="Smith",
            sex=Sex.MALE,
            birth_date=Date(year=1980),
            birth_place="New York",
            check_duplicates=False,
        )
    )

    persons.append(
        person_service.create_person(
            first_name="Jane",
            surname="Smith",
            sex=Sex.FEMALE,
            birth_date=Date(year=1982),
            birth_place="Boston",
            check_duplicates=False,
        )
    )

    persons.append(
        person_service.create_person(
            first_name="Bob",
            surname="Johnson",
            sex=Sex.MALE,
            birth_date=Date(year=1950),
            death_date=Date(year=2020),
            check_duplicates=False,
        )
    )

    persons.append(
        person_service.create_person(
            first_name="Alice",
            surname="Williams",
            sex=Sex.FEMALE,
            birth_date=Date(year=2000),
            check_duplicates=False,
        )
    )

    return persons


class TestSearchServiceBasic:
    """Test basic search functionality."""

    def test_search_all(self, service, sample_persons):
        """Test searching without filters returns all persons."""
        result = service.search_persons(
            filters=SearchFilters(),
            page=1,
            page_size=50,
        )

        assert result.total_count == 4
        assert len(result.persons) == 4

    def test_search_by_last_name(self, service, sample_persons):
        """Test searching by last name."""
        result = service.search_persons(
            filters=SearchFilters(last_name="Smith"),
            page=1,
            page_size=50,
        )

        assert result.total_count == 2
        assert all(p.surname == "Smith" for p in result.persons)

    def test_search_by_first_name(self, service, sample_persons):
        """Test searching by first name."""
        result = service.search_persons(
            filters=SearchFilters(first_name="John"),
            page=1,
            page_size=50,
        )

        assert result.total_count == 1
        assert result.persons[0].first_name == "John"

    def test_search_by_sex(self, service, sample_persons):
        """Test searching by sex."""
        result = service.search_persons(
            filters=SearchFilters(sex=Sex.FEMALE),
            page=1,
            page_size=50,
        )

        assert result.total_count == 2
        assert all(p.sex == Sex.FEMALE for p in result.persons)

    def test_search_by_birth_year_range(self, service, sample_persons):
        """Test searching by birth year range."""
        result = service.search_persons(
            filters=SearchFilters(birth_year_min=1980, birth_year_max=1990),
            page=1,
            page_size=50,
        )

        assert result.total_count == 2
        for person in result.persons:
            assert 1980 <= person.birth_date.year <= 1990

    def test_search_by_birth_place(self, service, sample_persons):
        """Test searching by birth place."""
        result = service.search_persons(
            filters=SearchFilters(birth_place="New York"),
            page=1,
            page_size=50,
        )

        assert result.total_count == 1
        assert "New York" in result.persons[0].birth_place

    def test_search_alive_only(self, service, sample_persons):
        """Test searching for living persons."""
        result = service.search_persons(
            filters=SearchFilters(is_alive=True),
            page=1,
            page_size=50,
        )

        assert result.total_count == 3
        assert all(p.death_date is None for p in result.persons)

    def test_search_deceased_only(self, service, sample_persons):
        """Test searching for deceased persons."""
        result = service.search_persons(
            filters=SearchFilters(is_alive=False),
            page=1,
            page_size=50,
        )

        assert result.total_count == 1
        assert all(p.death_date is not None for p in result.persons)

    def test_search_combined_filters(self, service, sample_persons):
        """Test searching with multiple filters."""
        result = service.search_persons(
            filters=SearchFilters(
                last_name="Smith",
                sex=Sex.FEMALE,
            ),
            page=1,
            page_size=50,
        )

        assert result.total_count == 1
        assert result.persons[0].first_name == "Jane"


class TestSearchServicePagination:
    """Test pagination."""

    def test_pagination_first_page(self, service, sample_persons):
        """Test first page of results."""
        result = service.search_persons(
            filters=SearchFilters(),
            page=1,
            page_size=2,
        )

        assert result.total_count == 4
        assert len(result.persons) == 2
        assert result.page == 1
        assert result.total_pages == 2

    def test_pagination_second_page(self, service, sample_persons):
        """Test second page of results."""
        result = service.search_persons(
            filters=SearchFilters(),
            page=2,
            page_size=2,
        )

        assert result.total_count == 4
        assert len(result.persons) == 2
        assert result.page == 2

    def test_pagination_invalid_page(self, service, sample_persons):
        """Test invalid page number."""
        with pytest.raises(ValidationError):
            service.search_persons(
                filters=SearchFilters(),
                page=0,
                page_size=10,
            )

    def test_pagination_invalid_page_size(self, service, sample_persons):
        """Test invalid page size."""
        with pytest.raises(ValidationError):
            service.search_persons(
                filters=SearchFilters(),
                page=1,
                page_size=2000,
            )


class TestSearchServiceSorting:
    """Test sorting."""

    def test_sort_by_surname(self, service, sample_persons):
        """Test sorting by surname."""
        result = service.search_persons(
            filters=SearchFilters(),
            sort_by="surname",
            page=1,
            page_size=50,
        )

        surnames = [p.surname for p in result.persons]
        assert surnames == sorted(surnames)

    def test_sort_by_first_name(self, service, sample_persons):
        """Test sorting by first name."""
        result = service.search_persons(
            filters=SearchFilters(),
            sort_by="first_name",
            page=1,
            page_size=50,
        )

        first_names = [p.first_name for p in result.persons]
        assert first_names == sorted(first_names)

    def test_sort_descending(self, service, sample_persons):
        """Test descending sort."""
        result = service.search_persons(
            filters=SearchFilters(),
            sort_by="birth_date",
            sort_desc=True,
            page=1,
            page_size=50,
        )

        birth_years = [p.birth_date.year for p in result.persons if p.birth_date]
        assert birth_years == sorted(birth_years, reverse=True)


class TestSearchServiceGenealogy:
    """Test genealogy tree traversal."""

    def test_get_ancestors(self, service, person_service, family_service, sample_persons):
        """Test getting ancestors."""
        # Create family structure: grandparent -> parent -> child
        grandparent = sample_persons[2]  # Bob
        parent = sample_persons[0]  # John
        child = sample_persons[3]  # Alice

        # Create family: grandparent -> parent
        family_service.create_family(
            father_id=grandparent.id,
            children_ids=[parent.id],
        )

        # Create family: parent -> child
        family_service.create_family(
            father_id=parent.id,
            children_ids=[child.id],
        )

        # Get ancestors of child
        ancestors = service.get_ancestors(child.id)

        assert len(ancestors) >= 2
        ancestor_ids = [a.id for a in ancestors]
        assert parent.id in ancestor_ids
        assert grandparent.id in ancestor_ids

    def test_get_descendants(self, service, person_service, family_service, sample_persons):
        """Test getting descendants."""
        # Create family structure
        parent = sample_persons[0]
        child1 = sample_persons[2]
        child2 = sample_persons[3]

        family_service.create_family(
            father_id=parent.id,
            children_ids=[child1.id, child2.id],
        )

        # Get descendants of parent
        descendants = service.get_descendants(parent.id)

        assert len(descendants) == 2
        descendant_ids = [d.id for d in descendants]
        assert child1.id in descendant_ids
        assert child2.id in descendant_ids

    def test_get_ancestors_max_generations(self, service, person_service, family_service, sample_persons):
        """Test limiting ancestor generations."""
        grandparent = sample_persons[2]
        parent = sample_persons[0]
        child = sample_persons[3]

        family_service.create_family(
            father_id=grandparent.id,
            children_ids=[parent.id],
        )

        family_service.create_family(
            father_id=parent.id,
            children_ids=[child.id],
        )

        # Get only immediate parents
        ancestors = service.get_ancestors(child.id, max_generations=1)

        assert len(ancestors) == 1
        assert ancestors[0].id == parent.id

    def test_find_relationship_path(self, service, person_service, family_service, sample_persons):
        """Test finding relationship path."""
        person1 = sample_persons[0]
        person2 = sample_persons[1]

        # Create family with both as spouses
        family_service.create_family(
            father_id=person1.id,
            mother_id=person2.id,
        )

        # Find path
        path = service.find_relationship_path(person1.id, person2.id)

        assert path is not None
        assert len(path) >= 2
        assert path[0].id == person1.id
        assert path[-1].id == person2.id

    def test_find_relationship_path_no_connection(self, service, person_service, sample_persons):
        """Test finding path between unrelated persons."""
        person1 = sample_persons[0]
        person2 = sample_persons[2]

        # No family connections
        path = service.find_relationship_path(person1.id, person2.id, max_depth=2)

        assert path is None


class TestSearchServiceStatistics:
    """Test statistics."""

    def test_get_statistics(self, service, sample_persons):
        """Test getting overall statistics."""
        stats = service.get_statistics()

        assert stats["total_persons"] == 4
        assert stats["male_count"] == 2
        assert stats["female_count"] == 2
        assert stats["living_count"] == 3
        assert stats["deceased_count"] == 1
