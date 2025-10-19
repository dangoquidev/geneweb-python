"""
Database service.

Business logic for database management operations.
"""

import logging
from pathlib import Path
from typing import Tuple

from backend.core.exceptions import DatabaseError, ValidationError
from backend.core.models import Family, Person
from backend.database.pickle_driver import PickleDriver

logger = logging.getLogger(__name__)


class DatabaseService:
    """
    Service for managing database operations.

    Handles database creation, listing, and information retrieval.
    """

    def __init__(self, database_dir: str):
        """
        Initialize database service.

        Args:
            database_dir: Directory containing databases.
        """
        self.database_dir = Path(database_dir)
        self.database_dir.mkdir(parents=True, exist_ok=True)

    def list_databases(self) -> list[str]:
        """
        List all available databases.

        Returns:
            List of database names (without .pickle extension).

        Raises:
            DatabaseError: If database directory cannot be read.
        """
        try:
            databases = []
            for file in self.database_dir.iterdir():
                if file.suffix == ".pickle" and file.is_file():
                    databases.append(file.stem)
            return sorted(databases)
        except OSError as e:
            logger.error(f"Error reading database directory: {e}")
            raise DatabaseError(f"Cannot read database directory: {e}")

    def database_exists(self, name: str) -> bool:
        """
        Check if database exists.

        Args:
            name: Database name.

        Returns:
            True if database exists, False otherwise.
        """
        db_path = self.database_dir / f"{name}.pickle"
        return db_path.exists()

    def create_database(self, name: str, db_type: str = "pickle") -> Tuple[bool, str, str]:
        """
        Create a new database.

        Args:
            name: Database name.
            db_type: Database type ('pickle' or 'sqlite').

        Returns:
            Tuple of (success, database_path, error_message).

        Raises:
            ValidationError: If database name is invalid or already exists.
            DatabaseError: If database creation fails.
        """
        # Validate database doesn't already exist
        if self.database_exists(name):
            raise ValidationError(f"Database '{name}' already exists")

        # Only pickle supported for now
        if db_type != "pickle":
            raise ValidationError(f"Database type '{db_type}' not yet supported")

        db_path = self.database_dir / f"{name}.pickle"

        try:
            # Create empty database using PickleDriver
            driver = PickleDriver(str(db_path))

            # Initialize with empty data structure and save
            empty_persons: dict[str, Person] = {}
            empty_families: dict[str, Family] = {}
            driver.save(persons=empty_persons, families=empty_families, create_backup=False)

            logger.info(f"Created database '{name}' at {db_path}")
            return True, str(db_path), ""

        except Exception as e:
            logger.error(f"Error creating database '{name}': {e}")
            # Clean up partial file if it exists
            if db_path.exists():
                try:
                    db_path.unlink()
                except Exception as cleanup_error:
                    logger.warning(f"Failed to clean up {db_path}: {cleanup_error}")
            raise DatabaseError(f"Failed to create database: {e}")

    def get_database_path(self, name: str) -> str:
        """
        Get full path to database file.

        Args:
            name: Database name.

        Returns:
            Full path to database file.

        Raises:
            ValidationError: If database doesn't exist.
        """
        if not self.database_exists(name):
            raise ValidationError(f"Database '{name}' not found")
        return str(self.database_dir / f"{name}.pickle")

    def delete_database(self, name: str) -> bool:
        """
        Delete a database.

        Args:
            name: Database name.

        Returns:
            True if deletion succeeded.

        Raises:
            ValidationError: If database doesn't exist.
            DatabaseError: If deletion fails.
        """
        if not self.database_exists(name):
            raise ValidationError(f"Database '{name}' not found")

        db_path = self.database_dir / f"{name}.pickle"
        try:
            db_path.unlink()
            logger.info(f"Deleted database '{name}'")
            return True
        except OSError as e:
            logger.error(f"Error deleting database '{name}': {e}")
            raise DatabaseError(f"Failed to delete database: {e}")
