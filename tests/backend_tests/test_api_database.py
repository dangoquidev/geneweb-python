"""
Tests for Database API endpoints.

Validates database creation, listing, info, and deletion.
"""

import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.api.app import create_app


@pytest.fixture
def test_db_dir(tmp_path: Path) -> Path:
    """Create temporary database directory."""
    db_dir = tmp_path / "test_databases"
    db_dir.mkdir(parents=True, exist_ok=True)
    return db_dir


@pytest.fixture
def client(test_db_dir: Path):
    """Create test client with temporary database directory."""
    os.environ["GENEWEB_DATABASE_PATH"] = str(test_db_dir)
    app = create_app(database_path=str(test_db_dir), debug=True)
    with TestClient(app) as test_client:
        yield test_client
    # Cleanup
    del os.environ["GENEWEB_DATABASE_PATH"]


class TestDatabaseListEndpoint:
    """Tests for GET /api/databases endpoint."""

    def test_list_databases_empty(self, client: TestClient):
        """Test listing databases when none exist."""
        response = client.get("/api/databases")
        assert response.status_code == 200
        data = response.json()
        assert "databases" in data
        assert "count" in data
        assert data["databases"] == []
        assert data["count"] == 0

    def test_list_databases_with_existing(self, client: TestClient, test_db_dir: Path):
        """Test listing databases when some exist."""
        # Create some test database files
        (test_db_dir / "test1.pickle").touch()
        (test_db_dir / "test2.pickle").touch()
        (test_db_dir / "ignored.txt").touch()  # Should be ignored

        response = client.get("/api/databases")
        assert response.status_code == 200
        data = response.json()
        assert len(data["databases"]) == 2
        assert "test1" in data["databases"]
        assert "test2" in data["databases"]
        assert data["count"] == 2


class TestDatabaseCreateEndpoint:
    """Tests for POST /api/databases endpoint."""

    def test_create_database_success(self, client: TestClient, test_db_dir: Path):
        """Test successful database creation."""
        response = client.post(
            "/api/databases",
            json={"name": "my-family", "db_type": "pickle"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["database_name"] == "my-family"
        assert "my-family.pickle" in data["path"]
        assert "created successfully" in data["message"]

        # Verify file was created
        assert (test_db_dir / "my-family.pickle").exists()

    def test_create_database_default_type(self, client: TestClient, test_db_dir: Path):
        """Test database creation with default type."""
        response = client.post(
            "/api/databases",
            json={"name": "test-default"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert (test_db_dir / "test-default.pickle").exists()

    def test_create_database_invalid_name_special_chars(self, client: TestClient):
        """Test creation with invalid characters in name."""
        response = client.post(
            "/api/databases",
            json={"name": "invalid/name", "db_type": "pickle"},
        )
        assert response.status_code == 422  # Validation error

    def test_create_database_invalid_name_spaces(self, client: TestClient):
        """Test creation with spaces in name."""
        response = client.post(
            "/api/databases",
            json={"name": "  spaced  ", "db_type": "pickle"},
        )
        assert response.status_code == 422

    def test_create_database_invalid_name_reserved(self, client: TestClient):
        """Test creation with reserved name."""
        response = client.post(
            "/api/databases",
            json={"name": "con", "db_type": "pickle"},
        )
        assert response.status_code == 422

    def test_create_database_already_exists(self, client: TestClient, test_db_dir: Path):
        """Test creation when database already exists."""
        # Create first database
        response1 = client.post(
            "/api/databases",
            json={"name": "duplicate", "db_type": "pickle"},
        )
        assert response1.status_code == 201

        # Try to create again
        response2 = client.post(
            "/api/databases",
            json={"name": "duplicate", "db_type": "pickle"},
        )
        assert response2.status_code == 400  # Bad request
        data = response2.json()
        assert "already exists" in data["detail"].lower()

    def test_create_database_missing_name(self, client: TestClient):
        """Test creation without name."""
        response = client.post(
            "/api/databases",
            json={"db_type": "pickle"},
        )
        assert response.status_code == 422  # Validation error

    def test_create_database_empty_name(self, client: TestClient):
        """Test creation with empty name."""
        response = client.post(
            "/api/databases",
            json={"name": "", "db_type": "pickle"},
        )
        assert response.status_code == 422

    def test_create_database_valid_names(self, client: TestClient, test_db_dir: Path):
        """Test creation with various valid names (GenEWeb OCaml rules: alphanumerics + hyphen only)."""
        valid_names = [
            "simple",
            "with-hyphen",
            "MixedCase123",
            "test2024",
            "my-family-tree",
        ]

        for name in valid_names:
            response = client.post(
                "/api/databases",
                json={"name": name, "db_type": "pickle"},
            )
            assert response.status_code == 201, f"Failed for name: {name}"
            assert (test_db_dir / f"{name}.pickle").exists()


class TestDatabaseInfoEndpoint:
    """Tests for GET /api/databases/{name} endpoint."""

    def test_get_database_info_success(self, client: TestClient):
        """Test getting info for existing database."""
        # Create database first
        create_response = client.post(
            "/api/databases",
            json={"name": "info-test", "db_type": "pickle"},
        )
        assert create_response.status_code == 201

        # Get info
        response = client.get("/api/databases/info-test")
        assert response.status_code == 200
        data = response.json()
        assert data["base_name"] == "info-test"
        assert "persons" in data
        assert "families" in data
        assert data["persons"] == 0  # Empty database
        assert data["families"] == 0
        assert "path" in data
        assert "version" in data

    def test_get_database_info_not_found(self, client: TestClient):
        """Test getting info for non-existent database."""
        response = client.get("/api/databases/nonexistent")
        assert response.status_code == 404


class TestDatabaseDeleteEndpoint:
    """Tests for DELETE /api/databases/{name} endpoint."""

    def test_delete_database_success(self, client: TestClient, test_db_dir: Path):
        """Test successful database deletion."""
        # Create database first
        create_response = client.post(
            "/api/databases",
            json={"name": "to-delete", "db_type": "pickle"},
        )
        assert create_response.status_code == 201
        assert (test_db_dir / "to-delete.pickle").exists()

        # Delete database
        response = client.delete("/api/databases/to-delete")
        assert response.status_code == 204
        assert not (test_db_dir / "to-delete.pickle").exists()

    def test_delete_database_not_found(self, client: TestClient):
        """Test deleting non-existent database."""
        response = client.delete("/api/databases/nonexistent")
        assert response.status_code == 404


class TestDatabaseWorkflow:
    """Integration tests for complete database workflow."""

    def test_full_lifecycle(self, client: TestClient, test_db_dir: Path):
        """Test create → list → info → delete workflow."""
        # 1. Initially no databases
        list_response = client.get("/api/databases")
        assert list_response.json()["count"] == 0

        # 2. Create database
        create_response = client.post(
            "/api/databases",
            json={"name": "lifecycle-test", "db_type": "pickle"},
        )
        assert create_response.status_code == 201

        # 3. List should show new database
        list_response = client.get("/api/databases")
        data = list_response.json()
        assert data["count"] == 1
        assert "lifecycle-test" in data["databases"]

        # 4. Get info
        info_response = client.get("/api/databases/lifecycle-test")
        assert info_response.status_code == 200
        assert info_response.json()["base_name"] == "lifecycle-test"

        # 5. Delete database
        delete_response = client.delete("/api/databases/lifecycle-test")
        assert delete_response.status_code == 204

        # 6. List should be empty again
        list_response = client.get("/api/databases")
        assert list_response.json()["count"] == 0

    def test_create_multiple_databases(self, client: TestClient):
        """Test creating multiple databases."""
        databases = ["db1", "db2", "db3"]

        for db_name in databases:
            response = client.post(
                "/api/databases",
                json={"name": db_name, "db_type": "pickle"},
            )
            assert response.status_code == 201

        # Verify all exist
        list_response = client.get("/api/databases")
        data = list_response.json()
        assert data["count"] == 3
        for db_name in databases:
            assert db_name in data["databases"]
