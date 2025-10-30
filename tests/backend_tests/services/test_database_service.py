"""
Tests for database service.

Focus on database name validation (GenEWeb OCaml compatibility)
and database lifecycle operations.
"""

from pathlib import Path

import pytest

from backend.core.exceptions import ValidationError
from backend.services.database_service import DatabaseService


class TestDatabaseNameValidation:
    """
    Test database name validation according to GenEWeb OCaml rules.

    GenEWeb OCaml only allows: a-z, A-Z, 0-9, and hyphen (-)
    Reference: legacy/ocaml-old-project/lib/util/mutil.ml (good_name function)
    """

    def test_validate_empty_name_raises_error(self):
        """Empty database name should raise ValidationError."""
        # Arrange / Act / Assert
        with pytest.raises(ValidationError, match="Database name cannot be empty"):
            DatabaseService.validate_database_name("")

    def test_validate_whitespace_name_raises_error(self):
        """Whitespace-only database name should raise ValidationError."""
        # Arrange / Act / Assert
        # Whitespace is treated as invalid character (not empty), which is correct
        with pytest.raises(ValidationError, match="invalid character"):
            DatabaseService.validate_database_name("   ")

    # Valid names (alphanumerics + hyphen)
    @pytest.mark.parametrize(
        "valid_name",
        [
            "famille",
            "FAMILLE",
            "Famille",
            "famille-dupont",
            "ma-famille",
            "test123",
            "base2024",
            "a",
            "A",
            "1",
            "abc-123-xyz",
            "MyFamily",
            "my-family-tree-2024",
        ],
    )
    def test_validate_valid_names_pass(self, valid_name: str):
        """Valid database names should not raise any error."""
        # Arrange / Act / Assert (no exception expected)
        DatabaseService.validate_database_name(valid_name)

    # Invalid names (containing forbidden characters)
    @pytest.mark.parametrize(
        "invalid_name,forbidden_char",
        [
            ("ma famille", " "),  # Space
            ("ma_famille", "_"),  # Underscore
            ("famille.db", "."),  # Dot
            ("famille/test", "/"),  # Slash
            ("famille\\test", "\\"),  # Backslash
            ("famille@2024", "@"),  # At sign
            ("famille#1", "#"),  # Hash
            ("famille$", "$"),  # Dollar
            ("famille%", "%"),  # Percent
            ("famille&co", "&"),  # Ampersand
            ("famille*", "*"),  # Asterisk
            ("famille(test)", "("),  # Parenthesis (first occurrence)
            ("famille+plus", "+"),  # Plus
            ("famille=equal", "="),  # Equal
            ("famille[1]", "["),  # Bracket
            ("famille{1}", "{"),  # Brace
            ("famille:test", ":"),  # Colon
            ("famille;test", ";"),  # Semicolon
            ("famille'test", "'"),  # Single quote
            ('famille"test', '"'),  # Double quote
            ("famille,test", ","),  # Comma
            ("famille<test", "<"),  # Less than
            ("famille>test", ">"),  # Greater than
            ("famille?", "?"),  # Question mark
            ("famille|test", "|"),  # Pipe
            ("famille~test", "~"),  # Tilde
            ("famille`test", "`"),  # Backtick
            ("famille\ntest", "\n"),  # Newline
            ("famille\ttest", "\t"),  # Tab
            ("famille€", "€"),  # Euro
            ("famille_ñ", "ñ"),  # Accented character
            ("famille_é", "é"),  # Accented character
        ],
    )
    def test_validate_invalid_names_raise_error(self, invalid_name: str, forbidden_char: str):
        """
        Invalid database names should raise ValidationError.

        Error message should indicate:
        - The database name
        - The invalid character
        - Position of the character
        - Allowed characters
        """
        # Arrange / Act / Assert
        with pytest.raises(ValidationError) as exc_info:
            DatabaseService.validate_database_name(invalid_name)

        error_message = str(exc_info.value)

        # Verify error message contains all required information
        assert invalid_name in error_message, "Error should mention the database name"
        assert forbidden_char in error_message, "Error should mention the invalid character"
        assert "position" in error_message.lower(), "Error should mention position"
        assert "alphanumeric" in error_message.lower(), "Error should mention allowed chars"

    def test_validate_multiple_invalid_chars_reports_first(self):
        """
        Database name with multiple invalid characters should report the first one.

        GenEWeb OCaml stops at first invalid character.
        """
        # Arrange
        name_with_multiple_invalid = "ma famille_test.db"  # space at position 2

        # Act / Assert
        with pytest.raises(ValidationError) as exc_info:
            DatabaseService.validate_database_name(name_with_multiple_invalid)

        error_message = str(exc_info.value)
        assert " " in error_message  # Space should be reported
        assert "position 2" in error_message

    def test_validate_hyphen_allowed(self):
        """Hyphen should be explicitly allowed (GenEWeb OCaml compatibility)."""
        # Arrange
        names_with_hyphens = [
            "a-b",
            "my-family",
            "test-123-abc",
            "-leading",
            "trailing-",
            "multiple---hyphens",
        ]

        # Act / Assert (no exceptions expected)
        for name in names_with_hyphens:
            DatabaseService.validate_database_name(name)


class TestDatabaseServiceLifecycle:
    """
    Test database creation, listing, deletion operations.

    These tests require a temporary directory for isolation.
    """

    @pytest.fixture
    def temp_db_service(self, tmp_path: Path) -> DatabaseService:
        """Create a DatabaseService instance with temporary directory."""
        return DatabaseService(str(tmp_path / "test_databases"))

    def test_create_database_with_valid_name_succeeds(self, temp_db_service: DatabaseService):
        """Creating database with valid name should succeed."""
        # Arrange
        name = "test-famille"

        # Act
        success, db_path, error = temp_db_service.create_database(name)

        # Assert
        assert success is True
        assert error == ""
        assert db_path.endswith("test-famille.pickle")
        assert temp_db_service.database_exists(name)

    def test_create_database_with_invalid_name_raises_error(self, temp_db_service: DatabaseService):
        """Creating database with invalid name should raise ValidationError."""
        # Arrange
        invalid_name = "ma famille"  # Contains space

        # Act / Assert
        with pytest.raises(ValidationError, match="invalid character"):
            temp_db_service.create_database(invalid_name)

        # Verify database was not created
        assert not temp_db_service.database_exists("ma")
        assert not temp_db_service.database_exists("famille")

    def test_create_existing_database_raises_error(self, temp_db_service: DatabaseService):
        """Creating database that already exists should raise ValidationError."""
        # Arrange
        name = "existing-db"
        temp_db_service.create_database(name)

        # Act / Assert
        with pytest.raises(ValidationError, match="already exists"):
            temp_db_service.create_database(name)

    def test_list_databases_returns_sorted_names(self, temp_db_service: DatabaseService):
        """List databases should return sorted database names without extension."""
        # Arrange
        databases = ["zebra", "alpha", "beta-test", "gamma2024"]
        for db in databases:
            temp_db_service.create_database(db)

        # Act
        result = temp_db_service.list_databases()

        # Assert
        expected = sorted(databases)
        assert result == expected

    def test_list_databases_empty_returns_empty_list(self, temp_db_service: DatabaseService):
        """List databases in empty directory should return empty list."""
        # Arrange / Act
        result = temp_db_service.list_databases()

        # Assert
        assert result == []

    def test_database_exists_returns_true_for_existing(self, temp_db_service: DatabaseService):
        """database_exists should return True for existing database."""
        # Arrange
        name = "existing"
        temp_db_service.create_database(name)

        # Act / Assert
        assert temp_db_service.database_exists(name) is True

    def test_database_exists_returns_false_for_nonexistent(self, temp_db_service: DatabaseService):
        """database_exists should return False for non-existent database."""
        # Arrange / Act / Assert
        assert temp_db_service.database_exists("nonexistent") is False

    def test_delete_database_succeeds(self, temp_db_service: DatabaseService):
        """Deleting existing database should succeed."""
        # Arrange
        name = "to-delete"
        temp_db_service.create_database(name)
        assert temp_db_service.database_exists(name)

        # Act
        result = temp_db_service.delete_database(name)

        # Assert
        assert result is True
        assert not temp_db_service.database_exists(name)

    def test_delete_nonexistent_database_raises_error(self, temp_db_service: DatabaseService):
        """Deleting non-existent database should raise ValidationError."""
        # Arrange / Act / Assert
        with pytest.raises(ValidationError, match="not found"):
            temp_db_service.delete_database("nonexistent")

    def test_get_database_path_returns_correct_path(self, temp_db_service: DatabaseService):
        """get_database_path should return full path to database file."""
        # Arrange
        name = "test-db"
        temp_db_service.create_database(name)

        # Act
        path = temp_db_service.get_database_path(name)

        # Assert
        assert path.endswith("test-db.pickle")
        assert Path(path).exists()

    def test_get_database_path_nonexistent_raises_error(self, temp_db_service: DatabaseService):
        """get_database_path for non-existent database should raise ValidationError."""
        # Arrange / Act / Assert
        with pytest.raises(ValidationError, match="not found"):
            temp_db_service.get_database_path("nonexistent")


class TestDatabaseServiceEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.fixture
    def temp_db_service(self, tmp_path: Path) -> DatabaseService:
        """Create a DatabaseService instance with temporary directory."""
        return DatabaseService(str(tmp_path / "test_databases"))

    def test_create_database_unsupported_type_raises_error(self, temp_db_service: DatabaseService):
        """Creating database with unsupported type should raise ValidationError."""
        # Arrange / Act / Assert
        with pytest.raises(ValidationError, match="not yet supported"):
            temp_db_service.create_database("test", db_type="sqlite")

    def test_very_long_valid_name_succeeds(self, temp_db_service: DatabaseService):
        """Very long database name (but valid) should succeed."""
        # Arrange
        # Linux filename limit is 255 bytes, minus ".pickle" (7) = 248 max
        long_name = "a" * 100 + "-" + "b" * 100  # 201 characters (safe)

        # Act
        success, _, _ = temp_db_service.create_database(long_name)

        # Assert
        assert success is True
        assert temp_db_service.database_exists(long_name)

    def test_name_with_unicode_digits_allowed(self, temp_db_service: DatabaseService):
        """Database name with regular ASCII digits should be allowed."""
        # Arrange
        name = "test0123456789"

        # Act
        success, _, _ = temp_db_service.create_database(name)

        # Assert
        assert success is True
