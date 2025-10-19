"""
Integration tests for API endpoints.

Tests all REST API endpoints using FastAPI TestClient.
"""

import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.api.app import create_app
from backend.core.models import Date, Family, MaritalStatus, Person, Sex
from backend.database.pickle_driver import PickleDriver
from backend.database.repository import Repository


@pytest.fixture
def temp_db():
    """Create temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".pickle", delete=False) as f:
        db_path = Path(f.name)

    # Delete the empty file - let the driver create it properly
    db_path.unlink()

    # Initialize database with test data
    driver = PickleDriver(str(db_path))
    repository = Repository(driver)

    # Create test persons
    person1 = Person(
        id="TEST_P001",
        first_name="John",
        surname="Doe",
        sex=Sex.MALE,
        birth_date=Date(year=1990, month=5, day=15),
        birth_place="Paris, France",
    )
    person2 = Person(
        id="TEST_P002",
        first_name="Jane",
        surname="Smith",
        sex=Sex.FEMALE,
        birth_date=Date(year=1992, month=8, day=20),
        birth_place="London, UK",
    )
    person3 = Person(
        id="TEST_P003",
        first_name="Jimmy",
        surname="Doe",
        sex=Sex.MALE,
        birth_date=Date(year=2015, month=3, day=10),
    )

    repository.add_person(person1)
    repository.add_person(person2)
    repository.add_person(person3)

    # Create test family
    family = Family(
        id="TEST_F001",
        father_id="TEST_P001",
        mother_id="TEST_P002",
        children_ids=["TEST_P003"],
        marital_status=MaritalStatus.MARRIED,
        marriage_date=Date(year=2014, month=6, day=15),
    )
    repository.add_family(family)

    # Link persons to family (update them to have family_id)
    from dataclasses import replace

    person1_updated = replace(person1, family_ids=[family.id])
    person2_updated = replace(person2, family_ids=[family.id])
    person3_updated = replace(person3, family_id=family.id)

    repository.update_person(person1_updated)
    repository.update_person(person2_updated)
    repository.update_person(person3_updated)

    # CRITICAL: Save to disk so the API can read it
    repository.save(create_backup=False)

    yield str(db_path)

    # Cleanup
    if db_path.exists():
        db_path.unlink()


@pytest.fixture
def client(temp_db):
    """Create FastAPI test client."""
    from backend.api.dependencies import get_repository
    from backend.database.pickle_driver import PickleDriver
    from backend.database.repository import Repository

    # Create app
    app = create_app(database_path=temp_db, debug=True)

    # Override the get_repository dependency to use our test database
    def override_get_repository():
        driver = PickleDriver(temp_db)
        repository = Repository(driver)
        try:
            yield repository
        finally:
            pass

    app.dependency_overrides[get_repository] = override_get_repository

    # Create test client
    test_client = TestClient(app)

    yield test_client

    # Clean up
    app.dependency_overrides.clear()


# ============================================================================
# Health Check Tests
# ============================================================================


class TestHealthEndpoints:
    """Test health check endpoints."""

    def test_health_check(self, client):
        """Test basic health check."""
        response = client.get("/api/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] in ["healthy", "degraded"]
        assert "timestamp" in data
        assert "version" in data
        assert "database_accessible" in data

    def test_status_check(self, client):
        """Test detailed status check."""
        response = client.get("/api/status")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] in ["healthy", "unhealthy"]
        assert "database" in data
        assert data["database"]["accessible"] is True
        assert data["database"]["persons_count"] == 3
        assert data["database"]["families_count"] == 1


# ============================================================================
# Person API Tests
# ============================================================================


class TestPersonAPI:
    """Test person CRUD endpoints."""

    def test_list_persons(self, client):
        """Test listing all persons."""
        response = client.get("/api/persons")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 3

    def test_get_person(self, client):
        """Test getting a specific person."""
        response = client.get("/api/persons/TEST_P001")
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == "TEST_P001"
        assert data["first_name"] == "John"
        assert data["surname"] == "Doe"
        assert data["sex"] == "M"

    def test_get_person_not_found(self, client):
        """Test getting non-existent person."""
        response = client.get("/api/persons/NONEXISTENT")
        assert response.status_code == 404

        data = response.json()
        assert data["error"] == "person_not_found"

    def test_create_person_requires_auth(self, client):
        """Test creating person requires authentication."""
        person_data = {
            "first_name": "Test",
            "surname": "Person",
            "sex": "M",
        }
        response = client.post("/api/persons", json=person_data)
        assert response.status_code == 401

    def test_get_person_statistics(self, client):
        """Test getting person statistics."""
        response = client.get("/api/persons/TEST_P001/statistics")
        assert response.status_code == 200

        data = response.json()
        assert data["person_id"] == "TEST_P001"
        assert data["full_name"] == "John Doe"
        assert "age" in data
        assert "events_count" in data


# ============================================================================
# Family API Tests
# ============================================================================


class TestFamilyAPI:
    """Test family CRUD endpoints."""

    def test_list_families(self, client):
        """Test listing all families."""
        response = client.get("/api/families")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1

    def test_get_family(self, client):
        """Test getting a specific family."""
        response = client.get("/api/families/TEST_F001")
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == "TEST_F001"
        assert data["father_id"] == "TEST_P001"
        assert data["mother_id"] == "TEST_P002"
        assert len(data["children_ids"]) == 1

    def test_get_family_not_found(self, client):
        """Test getting non-existent family."""
        response = client.get("/api/families/NONEXISTENT")
        assert response.status_code == 404

        data = response.json()
        assert data["error"] == "family_not_found"

    def test_get_family_statistics(self, client):
        """Test getting family statistics."""
        response = client.get("/api/families/TEST_F001/statistics")
        assert response.status_code == 200

        data = response.json()
        assert data["family_id"] == "TEST_F001"
        assert data["father_name"] == "John Doe"
        assert data["mother_name"] == "Jane Smith"
        assert data["children_count"] == 1
        assert data["is_married"] is True


# ============================================================================
# Search API Tests
# ============================================================================


class TestSearchAPI:
    """Test search and genealogy endpoints."""

    def test_search_persons_get(self, client):
        """Test searching persons with GET."""
        response = client.get("/api/search/persons?query=Doe")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2  # John Doe and Jimmy Doe

    def test_search_persons_post(self, client):
        """Test searching persons with POST."""
        search_req = {
            "query": "John",
            "search_in": ["first_name"],
            "fuzzy": False,
        }
        response = client.post("/api/search/persons", json=search_req)
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_get_ancestors(self, client):
        """Test getting ancestors."""
        response = client.get("/api/search/ancestors/TEST_P003?max_generations=2")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        # Jimmy's ancestors are John and Jane
        assert len(data) >= 2

    def test_get_descendants(self, client):
        """Test getting descendants."""
        response = client.get("/api/search/descendants/TEST_P001?max_generations=2")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        # John's descendant is Jimmy
        assert len(data) >= 1

    def test_get_relatives(self, client):
        """Test getting all relatives."""
        response = client.get("/api/search/relatives/TEST_P003")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        # Jimmy's relatives are at least his parents
        assert len(data) >= 2

    def test_find_relationship_path(self, client):
        """Test finding relationship path."""
        response = client.get("/api/search/relationship/TEST_P001/TEST_P003")
        assert response.status_code == 200

        data = response.json()
        assert data["person1_id"] == "TEST_P001"
        assert data["person2_id"] == "TEST_P003"
        assert "path" in data
        assert "relationship_degree" in data

    def test_get_statistics(self, client):
        """Test getting database statistics."""
        response = client.get("/api/search/statistics")
        assert response.status_code == 200

        data = response.json()
        assert data["total_persons"] == 3
        assert data["total_families"] == 1
        assert "avg_children_per_family" in data


# ============================================================================
# OpenAPI Documentation Tests
# ============================================================================


class TestOpenAPI:
    """Test OpenAPI documentation generation."""

    def test_openapi_json(self, client):
        """Test OpenAPI JSON is accessible."""
        response = client.get("/api/openapi.json")
        assert response.status_code == 200

        data = response.json()
        assert "openapi" in data
        assert "info" in data
        assert data["info"]["title"] == "GenEWeb API"

    def test_docs_page(self, client):
        """Test Swagger UI docs page."""
        response = client.get("/api/docs")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_redoc_page(self, client):
        """Test ReDoc documentation page."""
        response = client.get("/api/redoc")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
