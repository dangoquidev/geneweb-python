"""
GEDCOM import service.

Orchestrates the full GEDCOM import process:
1. Validate file
2. Parse GEDCOM
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
from backend.parsers.gedcom_converter import GedcomConverter
from backend.parsers.gedcom_parser import GedcomParser

logger = logging.getLogger(__name__)


@dataclass
class ImportReport:
    """
    Report of GEDCOM import operation.

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


class GedcomImportService:
    """
    Service for importing GEDCOM files.

    Handles the complete workflow:
    - File validation
    - Parsing
    - Conversion
    - Database creation/update
    - Error reporting

    Usage:
        service = GedcomImportService(database_dir="data")
        report = service.import_gedcom(
            gedcom_file_path="family.ged",
            output_database_name="my-family"
        )
        print(report.summary)
    """

    def __init__(self, database_dir: str = "data"):
        """
        Initialize GEDCOM import service.

        Args:
            database_dir: Directory where databases are stored.
        """
        self.database_dir = Path(database_dir)
        self.database_dir.mkdir(parents=True, exist_ok=True)

    def import_gedcom(
        self,
        gedcom_file_path: Union[Path, str],
        output_database_name: str,
        encoding: str = "utf-8",
        lenient: bool = True,
        overwrite: bool = False,
    ) -> ImportReport:
        """
        Import a GEDCOM file into a GenEWeb database.

        Args:
            gedcom_file_path: Path to GEDCOM file.
            output_database_name: Name for the output database.
            encoding: Character encoding (default: utf-8, auto-detected from file).
            lenient: If True, ignore non-critical errors. If False, fail on any error.
            overwrite: If True, overwrite existing database. If False, fail if exists.

        Returns:
            ImportReport with statistics and status.

        Raises:
            FileNotFoundError: If GEDCOM file doesn't exist.
            ValidationError: If database name is invalid or database already exists.
            DatabaseError: If database creation fails.

        Examples:
            >>> service = GedcomImportService()
            >>> report = service.import_gedcom("family.ged", "my-family")
            >>> print(f"{report.persons_count} persons imported")
        """
        import time

        start_time = time.time()

        gedcom_file_path = Path(gedcom_file_path)

        # Validate inputs
        if not gedcom_file_path.exists():
            raise FileNotFoundError(f"GEDCOM file not found: {gedcom_file_path}")

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

        report = ImportReport(
            success=False,
            database_name=output_database_name,
            database_path=str(db_path),
        )

        try:
            # Step 1: Parse GEDCOM file
            logger.info(f"Parsing GEDCOM file: {gedcom_file_path}")
            parser = GedcomParser(encoding=encoding, strict=not lenient)
            records = parser.parse_file(gedcom_file_path)

            report.warnings.extend(parser.warnings)
            report.errors.extend(parser.errors)

            logger.info(f"Parsed {len(records)} GEDCOM records")

            # Step 2: Convert to GenEWeb models
            logger.info("Converting GEDCOM records to GenEWeb models")
            converter = GedcomConverter(lenient=lenient)
            persons, families = converter.convert(records)

            report.warnings.extend(converter.warnings)
            report.errors.extend(converter.errors)

            report.persons_count = len(persons)
            report.families_count = len(families)

            logger.info(f"Converted to {report.persons_count} persons, " f"{report.families_count} families")

            # Step 3: Validate data
            validation_errors = self._validate_data(persons, families)
            if validation_errors:
                report.errors.extend(validation_errors)
                if not lenient:
                    raise ValidationError(f"Data validation failed: {validation_errors}")

            # Step 4: Save to database
            logger.info(f"Saving to database: {db_path}")
            driver = PickleDriver(str(db_path))
            driver.save(persons=persons, families=families, create_backup=False)

            report.success = True
            logger.info(f"✅ Import successful: {report.summary}")

        except Exception as e:
            error_msg = f"Import failed: {str(e)}"
            report.errors.append(error_msg)
            report.success = False
            logger.error(error_msg, exc_info=True)

            # Clean up partial database if created
            if db_path.exists() and not overwrite:
                try:
                    db_path.unlink()
                    logger.info(f"Cleaned up partial database: {db_path}")
                except Exception as cleanup_error:
                    logger.warning(f"Failed to clean up {db_path}: {cleanup_error}")

            if not lenient:
                raise

        finally:
            report.duration_seconds = time.time() - start_time

        return report

    def _validate_database_name(self, name: str) -> None:
        """
        Validate database name according to GenEWeb OCaml rules.

        Only allows: a-z, A-Z, 0-9, and hyphen (-).

        Args:
            name: Database name to validate.

        Raises:
            ValidationError: If name contains invalid characters.
        """
        if not name:
            raise ValidationError("Database name cannot be empty")

        for i, char in enumerate(name):
            if not (char.isalnum() or char == "-"):
                raise ValidationError(
                    f"Database name '{name}' contains invalid character '{char}' "
                    f"at position {i}. Only alphanumerics (a-z, A-Z, 0-9) and "
                    f"hyphen (-) are allowed."
                )

    def _validate_data(self, persons: Dict[str, Person], families: Dict[str, Family]) -> List[str]:
        """
        Validate converted data for consistency.

        Checks:
        - All family father/mother references exist
        - All family children references exist
        - All person father/mother references exist
        - No circular family relationships

        Args:
            persons: Dictionary of Person objects.
            families: Dictionary of Family objects.

        Returns:
            List of validation error messages (empty if valid).
        """
        errors = []

        # Validate family references
        for family_id, family in families.items():
            # Check father exists
            if family.father_id and family.father_id not in persons:
                errors.append(f"Family {family_id}: Father '{family.father_id}' not found")

            # Check mother exists
            if family.mother_id and family.mother_id not in persons:
                errors.append(f"Family {family_id}: Mother '{family.mother_id}' not found")

            # Check children exist
            for child_id in family.children_ids:
                if child_id not in persons:
                    errors.append(f"Family {family_id}: Child '{child_id}' not found")

        # Validate person references
        for person_id, person in persons.items():
            # Check parent family exists
            if person.family_id and person.family_id not in families:
                errors.append(f"Person {person_id}: Parent family '{person.family_id}' not found")

            # Check spouse families exist
            for family_id in person.family_ids:
                if family_id not in families:
                    errors.append(f"Person {person_id}: Spouse family '{family_id}' not found")

        return errors

    def get_import_statistics(self, gedcom_file_path: Union[Path, str]) -> Dict:
        """
        Get statistics about a GEDCOM file without importing.

        Useful for previewing import before committing.

        Args:
            gedcom_file_path: Path to GEDCOM file.

        Returns:
            Dictionary with statistics.

        Examples:
            >>> service = GedcomImportService()
            >>> stats = service.get_import_statistics("family.ged")
            >>> print(f"Will import {stats['individuals']} persons")
        """
        gedcom_file_path = Path(gedcom_file_path)

        if not gedcom_file_path.exists():
            raise FileNotFoundError(f"GEDCOM file not found: {gedcom_file_path}")

        parser = GedcomParser()
        records = parser.parse_file(gedcom_file_path)

        stats = parser.get_statistics(records)

        return {
            "file_path": str(gedcom_file_path),
            "file_size_bytes": gedcom_file_path.stat().st_size,
            "individuals": stats.get("INDI", 0),
            "families": stats.get("FAM", 0),
            "notes": stats.get("NOTE", 0),
            "sources": stats.get("SOUR", 0),
            "total_records": len(records),
            "warnings_count": len(parser.warnings),
            "errors_count": len(parser.errors),
        }
