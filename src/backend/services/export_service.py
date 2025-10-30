"""
Export Service for GenEWeb.

Exports database contents to various genealogy formats (GEDCOM, GeneWeb).
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Union

from backend.core.exceptions import DatabaseError
from backend.core.models import Family, Person
from backend.database.pickle_driver import PickleDriver
from backend.exporters.gedcom_exporter import GedcomExporter
from backend.exporters.geneweb_exporter import GeneWebExporter

logger = logging.getLogger(__name__)


class ExportService:
    """
    Service for exporting GenEWeb databases.

    Handles:
    - Loading database
    - Filtering persons/families (if needed)
    - Export to various formats
    - File generation

    Usage:
        service = ExportService(database_dir="data")
        service.export_to_gedcom(
            database_name="my-family",
            output_file="export.ged"
        )
    """

    def __init__(self, database_dir: str = "data"):
        """
        Initialize export service.

        Args:
            database_dir: Directory where databases are stored.
        """
        self.database_dir = Path(database_dir)

    def export_to_gedcom(
        self,
        database_name: str,
        output_file: Optional[Union[str, Path]] = None,
        person_ids: Optional[List[str]] = None,
        family_ids: Optional[List[str]] = None,
        include_notes: bool = True,
        include_images: bool = True,
    ) -> Path:
        """
        Export database to GEDCOM format.

        Args:
            database_name: Name of database to export.
            output_file: Path to output file (optional, auto-generated if not provided).
            person_ids: List of person IDs to export (optional, all if not provided).
            family_ids: List of family IDs to export (optional, all if not provided).
            include_notes: Include notes and comments in export (default: True).
            include_images: Include image references in export (default: True).

        Returns:
            Path to generated GEDCOM file.

        Raises:
            FileNotFoundError: If database doesn't exist.
            DatabaseError: If database loading fails.

        Examples:
            >>> service = ExportService()
            >>> output = service.export_to_gedcom("my-family")
            >>> print(f"Exported to {output}")
        """
        logger.info(f"Exporting database '{database_name}' to GEDCOM")

        # Load database
        persons, families = self._load_database(database_name)

        # Filter if needed
        if person_ids:
            persons = {pid: p for pid, p in persons.items() if pid in person_ids}
            logger.info(f"Filtered to {len(persons)} persons")

        if family_ids:
            families = {fid: f for fid, f in families.items() if fid in family_ids}
            logger.info(f"Filtered to {len(families)} families")

        persons_count = len(persons)
        families_count = len(families)

        # Determine output file
        if not output_file:
            output_file = self.database_dir / f"{database_name}.ged"
        else:
            output_file = Path(output_file)

        # Export with options
        exporter = GedcomExporter(
            include_notes=include_notes,
            include_images=include_images,
        )
        exporter.export(
            persons=persons,
            families=families,
            output_file=output_file,
            database_name=database_name,
        )

        logger.info(f"✅ Exported {persons_count} persons, {families_count} families to GEDCOM")

        return output_file

    def export_to_geneweb(
        self,
        database_name: str,
        output_file: Union[str, Path, None] = None,
        include_notes: bool = True,
    ) -> Path:
        """
        Export database to GeneWeb .gw format.

        Args:
            database_name: Name of database to export.
            output_file: Optional output file path. If None, uses data/{database_name}.gw
            include_notes: Include notes and comments in export (default: True).

        Returns:
            Path to generated GeneWeb file.

        Raises:
            DatabaseError: If database cannot be loaded.
            GenEWebError: If export fails.

        Examples:
            >>> service = ExportService()
            >>> output = service.export_to_geneweb("martin_family")
            >>> print(output)
            PosixPath('data/martin_family.gw')
        """
        logger.info(f"Exporting database '{database_name}' to GeneWeb format")

        # Load database
        persons, families = self._load_database(database_name)
        persons_count = len(persons)
        families_count = len(families)

        # Default output file
        if output_file is None:
            output_file = self.database_dir / f"{database_name}.gw"
        else:
            output_file = Path(output_file)

        # Ensure parent directory exists
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Export to GeneWeb with options
        exporter = GeneWebExporter(include_notes=include_notes)
        exporter.export(
            persons=persons,
            families=families,
            output_file=output_file,
            database_name=database_name,
        )

        logger.info(f"✅ Exported {persons_count} persons, {families_count} families to GeneWeb")

        return output_file

    def export_to_geneweb_string(self, database_name: str, include_notes: bool = True) -> str:
        """
        Export database to GeneWeb .gw format as string.

        Args:
            database_name: Name of database to export.
            include_notes: Include notes and comments in export (default: True).

        Returns:
            GeneWeb .gw content as string.

        Raises:
            DatabaseError: If database cannot be loaded.
            GenEWebError: If export fails.

        Examples:
            >>> service = ExportService()
            >>> gw_content = service.export_to_geneweb_string("martin_family")
            >>> print(gw_content[:50])
            encoding: utf-8
            gwplus
        """
        logger.info(f"Exporting database '{database_name}' to GeneWeb string")

        # Load database
        persons, families = self._load_database(database_name)

        # Export to string with options
        exporter = GeneWebExporter(include_notes=include_notes)
        content = exporter.export_to_string(
            persons=persons,
            families=families,
            database_name=database_name,
        )

        return str(content)

    def export_to_gedcom_string(
        self,
        database_name: str,
        person_ids: Optional[List[str]] = None,
        family_ids: Optional[List[str]] = None,
        include_notes: bool = True,
        include_images: bool = True,
    ) -> str:
        """
        Export database to GEDCOM string (for download/API response).

        Args:
            database_name: Name of database to export.
            person_ids: List of person IDs to export (optional, all if not provided).
            family_ids: List of family IDs to export (optional, all if not provided).
            include_notes: Include notes and comments in export (default: True).
            include_images: Include image references in export (default: True).

        Returns:
            GEDCOM content as string.

        Examples:
            >>> service = ExportService()
            >>> gedcom = service.export_to_gedcom_string("my-family")
            >>> print(gedcom[:100])
        """
        logger.info(f"Exporting database '{database_name}' to GEDCOM string")

        # Load database
        persons, families = self._load_database(database_name)

        # Filter if needed
        if person_ids:
            persons = {pid: p for pid, p in persons.items() if pid in person_ids}

        if family_ids:
            families = {fid: f for fid, f in families.items() if fid in family_ids}

        # Export to string with options
        exporter = GedcomExporter(
            include_notes=include_notes,
            include_images=include_images,
        )
        gedcom_content = exporter.export_to_string(
            persons=persons,
            families=families,
            database_name=database_name,
        )

        logger.info(f"✅ Exported {len(persons)} persons, {len(families)} families to string")

        return str(gedcom_content)

    def get_database_statistics(self, database_name: str) -> Dict:
        """
        Get statistics about database (for export preview).

        Args:
            database_name: Name of database.

        Returns:
            Dictionary with statistics.

        Examples:
            >>> service = ExportService()
            >>> stats = service.get_database_statistics("my-family")
            >>> print(f"{stats['persons_count']} persons")
        """
        logger.info(f"Getting statistics for database '{database_name}'")

        persons, families = self._load_database(database_name)

        return {
            "database_name": database_name,
            "persons_count": len(persons),
            "families_count": len(families),
            "estimated_gedcom_size_kb": self._estimate_gedcom_size(persons, families),
        }

    def _load_database(self, database_name: str) -> tuple:
        """
        Load database and return persons and families.

        Args:
            database_name: Name of database.

        Returns:
            Tuple of (persons_dict, families_dict).

        Raises:
            FileNotFoundError: If database doesn't exist.
            DatabaseError: If database loading fails.
        """
        db_path = self.database_dir / f"{database_name}.pickle"

        if not db_path.exists():
            raise FileNotFoundError(f"Database '{database_name}' not found at {db_path}")

        logger.info(f"Loading database: {db_path}")

        driver = PickleDriver(str(db_path))
        data = driver.load()

        if not data:
            raise DatabaseError(f"Failed to load database: {db_path}")

        persons = data.get("persons", {})
        families = data.get("families", {})

        logger.info(f"Loaded {len(persons)} persons, {len(families)} families")

        return persons, families

    def _estimate_gedcom_size(self, persons: Dict[str, Person], families: Dict[str, Family]) -> int:
        """
        Estimate GEDCOM file size in KB.

        Args:
            persons: Dictionary of Person objects.
            families: Dictionary of Family objects.

        Returns:
            Estimated size in KB.
        """
        # Rough estimate: ~200 bytes per person, ~100 bytes per family, + 1KB header
        estimated_bytes = len(persons) * 200 + len(families) * 100 + 1024
        return estimated_bytes // 1024
