"""
GeneWeb import service.

Orchestrates the full GeneWeb .gw file import process:
1. Validate file
2. Parse GeneWeb format
3. Convert to models
4. Save to database
5. Generate import report
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Union

from backend.core.exceptions import ValidationError
from backend.core.models import Family, Person
from backend.database.pickle_driver import PickleDriver
from backend.parsers.geneweb_converter import GeneWebConverter
from backend.parsers.geneweb_parser import GeneWebParser

logger = logging.getLogger(__name__)


@dataclass
class ImportReport:
    """
    Report of GeneWeb import operation.

    Contains statistics, warnings, and errors from the import process.
    """

    success: bool
    database_name: str
    database_path: str
    persons_count: int = 0
    families_count: int = 0
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    duration_seconds: float = 0.0

    @property
    def summary(self) -> str:
        """Get human-readable summary of import."""
        if self.success:
            return (
                f"✅ Import réussi : {self.persons_count} personnes, "
                f"{self.families_count} familles importées dans '{self.database_name}'"
            )
        else:
            return f"❌ Import échoué : {len(self.errors)} erreur(s)"

    def to_dict(self) -> Dict:
        """Convert report to dictionary for API response."""
        return {
            "success": self.success,
            "database_name": self.database_name,
            "database_path": self.database_path,
            "persons_count": self.persons_count,
            "families_count": self.families_count,
            "warnings": self.warnings,
            "errors": self.errors,
            "duration_seconds": round(self.duration_seconds, 2),
            "summary": self.summary,
        }


class GeneWebImportService:
    """
    Service for importing GeneWeb .gw files.

    Handles the complete workflow:
    - File validation
    - Parsing
    - Conversion
    - Database creation/update
    - Error reporting

    Usage:
        service = GeneWebImportService(database_dir="data")
        report = service.import_geneweb(
            geneweb_file_path="family.gw",
            output_database_name="my-family"
        )
        print(report.summary)
    """

    def __init__(self, database_dir: str = "data"):
        """
        Initialize GeneWeb import service.

        Args:
            database_dir: Directory where databases are stored.
        """
        self.database_dir = Path(database_dir)
        self.database_dir.mkdir(parents=True, exist_ok=True)

    def import_geneweb(
        self,
        geneweb_file_path: Union[Path, str],
        output_database_name: str,
        lenient: bool = True,
        overwrite: bool = False,
    ) -> ImportReport:
        """
        Import a GeneWeb .gw file into a GenEWeb database.

        Args:
            geneweb_file_path: Path to GeneWeb .gw file.
            output_database_name: Name for the output database.
            lenient: If True, ignore non-critical errors. If False, fail on any error.
            overwrite: If True, overwrite existing database. If False, fail if exists.

        Returns:
            ImportReport with statistics and status.

        Raises:
            FileNotFoundError: If GeneWeb file doesn't exist.
            ValidationError: If database name is invalid or database already exists.
            DatabaseError: If database creation fails.

        Examples:
            >>> service = GeneWebImportService()
            >>> report = service.import_geneweb("family.gw", "my-family")
            >>> print(f"{report.persons_count} persons imported")
        """
        import time

        start_time = time.time()

        geneweb_file_path = Path(geneweb_file_path)

        # Validate inputs
        if not geneweb_file_path.exists():
            raise FileNotFoundError(f"GeneWeb file not found: {geneweb_file_path}")

        if not output_database_name:
            raise ValidationError("Output database name cannot be empty")

        # Validate database name (GenEWeb rules: alphanumerics + hyphen only)
        self._validate_database_name(output_database_name)

        # Check if database already exists
        db_path = self.database_dir / f"{output_database_name}.pickle"
        if db_path.exists() and not overwrite:
            raise ValidationError(
                f"Database '{output_database_name}' already exists. " f"Use overwrite=True to replace it."
            )

        logger.info(f"Starting GeneWeb import: {geneweb_file_path} → {output_database_name}")

        report = ImportReport(
            success=False,
            database_name=output_database_name,
            database_path=str(db_path),
        )

        try:
            # Step 1: Parse GeneWeb file
            logger.info("Step 1/3: Parsing GeneWeb file...")
            parser = GeneWebParser(strict=not lenient)
            geneweb_record = parser.parse_file(geneweb_file_path)

            # Step 2: Convert to GenEWeb models
            logger.info("Step 2/3: Converting to GenEWeb models...")
            converter = GeneWebConverter()
            persons, families = converter.convert(geneweb_record)

            report.persons_count = len(persons)
            report.families_count = len(families)

            logger.info(f"Converted {len(persons)} persons, {len(families)} families")

            # Step 3: Save to database
            logger.info("Step 3/3: Saving to database...")
            self._save_to_database(
                db_path=db_path,
                persons=persons,
                families=families,
                overwrite=overwrite,
            )

            # Success
            report.success = True
            report.duration_seconds = time.time() - start_time

            logger.info(f"✅ {report.summary}")

        except Exception as e:
            report.success = False
            report.errors.append(str(e))
            report.duration_seconds = time.time() - start_time

            logger.error(f"❌ Import failed: {e}", exc_info=True)

            # Re-raise in strict mode
            if not lenient:
                raise

        return report

    def get_import_statistics(self, geneweb_file_path: Union[Path, str]) -> Dict:
        """
        Get statistics about a GeneWeb file without importing.

        Args:
            geneweb_file_path: Path to GeneWeb file.

        Returns:
            Dictionary with file statistics.

        Examples:
            >>> service = GeneWebImportService()
            >>> stats = service.get_import_statistics("family.gw")
            >>> print(f"{stats['persons']} persons, {stats['families']} families")
        """
        geneweb_file_path = Path(geneweb_file_path)

        if not geneweb_file_path.exists():
            raise FileNotFoundError(f"GeneWeb file not found: {geneweb_file_path}")

        # Parse file
        parser = GeneWebParser(strict=False)
        record = parser.parse_file(geneweb_file_path)

        # Count persons and families
        persons_set = set()

        for family in record.families:
            if family.father:
                persons_set.add(family.father.key)
            if family.mother:
                persons_set.add(family.mother.key)
            for child in family.children:
                if not child.surname and family.father:
                    child.surname = family.father.surname
                persons_set.add(child.key)

        return {
            "file_path": str(geneweb_file_path),
            "file_size_bytes": geneweb_file_path.stat().st_size,
            "families": len(record.families),
            "persons": len(persons_set),
            "notes_count": len(record.person_notes),
            "events_count": len(record.person_events),
            "total_records": len(record.families) + len(persons_set),
            "encoding": record.encoding,
            "gwplus": record.gwplus,
            "warnings_count": 0,
            "errors_count": 0,
        }

    def _validate_database_name(self, name: str) -> None:
        """
        Validate database name according to GenEWeb rules.

        Args:
            name: Database name to validate.

        Raises:
            ValidationError: If name is invalid.
        """
        if not name:
            raise ValidationError("Database name cannot be empty")

        # Only alphanumerics and hyphens allowed
        if not all(c.isalnum() or c == "-" for c in name):
            invalid_chars = [c for c in name if not (c.isalnum() or c == "-")]
            raise ValidationError(
                f"Invalid database name '{name}'. "
                f"Only alphanumeric characters (a-z, A-Z, 0-9) and hyphens (-) are allowed. "
                f"Invalid characters: {', '.join(repr(c) for c in invalid_chars)}"
            )

        # Additional checks
        if name.startswith("-") or name.endswith("-"):
            raise ValidationError("Database name cannot start or end with a hyphen")

        if len(name) > 255:
            raise ValidationError("Database name is too long (max 255 characters)")

    def _save_to_database(
        self,
        db_path: Path,
        persons: List[Person],
        families: List[Family],
        overwrite: bool,
    ) -> None:
        """
        Save persons and families to database.

        Args:
            db_path: Path to database file.
            persons: List of Person models.
            families: List of Family models.
            overwrite: Whether to overwrite existing database.

        Raises:
            DatabaseError: If database creation fails.
        """
        # Remove existing database if overwrite
        if overwrite and db_path.exists():
            logger.info(f"Removing existing database: {db_path}")
            db_path.unlink()

        # Create persons and families dictionaries with proper IDs
        persons_dict = {person.id: person for person in persons}
        families_dict = {family.id: family for family in families}

        # Create database driver and save
        logger.info(f"Saving {len(persons)} persons and {len(families)} families...")
        driver = PickleDriver(str(db_path))
        driver.save(persons=persons_dict, families=families_dict, create_backup=False)

        logger.info(f"✅ Database saved: {db_path}")
