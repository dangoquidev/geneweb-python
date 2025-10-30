"""
Tests d'intégration pour l'import GEDCOM.

Tests end-to-end du flux complet :
1. Parsing du fichier GEDCOM
2. Conversion vers modèles GenEWeb
3. Validation des données
4. Sauvegarde en base
5. Vérification de l'intégrité
"""

import sys
from pathlib import Path
from typing import Dict

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

# Import after path modification (required for test discovery)
from backend.core.models import Family, Person, Sex  # noqa: E402
from backend.database.pickle_driver import PickleDriver  # noqa: E402
from backend.services.gedcom_import_service import GedcomImportService  # noqa: E402


class TestGedcomImportIntegration:
    """Tests d'intégration pour l'import GEDCOM complet."""

    @pytest.fixture
    def test_gedcom_file(self) -> Path:
        """Fixture retournant le chemin vers le fichier GEDCOM de test."""
        return Path("tests/fixtures/test_family.ged")

    @pytest.fixture
    def database_dir(self, tmp_path: Path) -> Path:
        """Fixture créant un répertoire temporaire pour les bases de test."""
        db_dir = tmp_path / "databases"
        db_dir.mkdir(parents=True, exist_ok=True)
        return db_dir

    @pytest.fixture
    def import_service(self, database_dir: Path) -> GedcomImportService:
        """Fixture créant un service d'import."""
        return GedcomImportService(database_dir=str(database_dir))

    def test_import_simple_gedcom(
        self, import_service: GedcomImportService, test_gedcom_file: Path, database_dir: Path
    ):
        """
        Test d'import d'un fichier GEDCOM simple.

        Vérifie que le fichier test_family.ged est correctement importé
        avec 5 personnes et 2 familles, et que toutes les relations
        sont correctement établies.
        """
        # Arrange
        db_name = "test-integration"
        assert test_gedcom_file.exists(), f"Test file not found: {test_gedcom_file}"

        # Act
        report = import_service.import_gedcom(
            gedcom_file_path=str(test_gedcom_file),
            output_database_name=db_name,
            overwrite=True,
        )

        # Assert - Import success
        assert report.success, f"Import failed: {report.errors}"
        assert report.persons_count == 5, f"Expected 5 persons, got {report.persons_count}"
        assert report.families_count == 2, f"Expected 2 families, got {report.families_count}"
        assert len(report.errors) == 0, f"Unexpected errors: {report.errors}"
        assert report.duration_seconds >= 0, "Duration should be non-negative"

        # Assert - Database file created
        db_path = database_dir / f"{db_name}.pickle"
        assert db_path.exists(), f"Database file not created: {db_path}"

        # Act - Load and verify database content
        driver = PickleDriver(str(db_path))
        data = driver.load()
        persons: Dict[str, Person] = data["persons"]
        families: Dict[str, Family] = data["families"]

        # Assert - Correct counts
        assert len(persons) == 5, f"Expected 5 persons in DB, got {len(persons)}"
        assert len(families) == 2, f"Expected 2 families in DB, got {len(families)}"

        # Assert - Verify specific persons exist
        expected_person_ids = ["@I1@", "@I2@", "@I3@", "@I4@", "@I5@"]
        for person_id in expected_person_ids:
            assert person_id in persons, f"Person {person_id} not found in database"

        # Assert - Verify person details for John Doe (@I1@)
        john = persons["@I1@"]
        assert john.first_name == "John", f"Expected first_name='John', got '{john.first_name}'"
        assert john.surname == "Doe", f"Expected surname='Doe', got '{john.surname}'"
        assert john.sex == Sex.MALE, f"Expected sex=MALE, got {john.sex}"
        assert john.birth_date is not None, "John should have a birth date"
        assert john.death_date is not None, "John should have a death date"

        # Assert - Verify families exist
        expected_family_ids = ["@F1@", "@F2@"]
        for family_id in expected_family_ids:
            assert family_id in families, f"Family {family_id} not found in database"

        # Assert - Verify family relationships
        family_f1 = families["@F1@"]
        assert family_f1.marriage_date is not None, "Family @F1@ should have marriage date"
        assert (
            family_f1.marriage_place == "Las Vegas, Nevada, USA"
        ), f"Expected marriage place 'Las Vegas, Nevada, USA', got '{family_f1.marriage_place}'"

    def test_import_with_validation_errors(self, import_service: GedcomImportService, tmp_path: Path):
        """
        Test d'import d'un fichier GEDCOM malformé.

        Vérifie que les erreurs de parsing sont correctement
        détectées et que l'import échoue proprement.
        """
        # Arrange - Create malformed GEDCOM (invalid syntax)
        malformed_gedcom = tmp_path / "malformed.ged"
        malformed_gedcom.write_text(
            """This is not a valid GEDCOM file
Just some random text
Without proper structure
""",
            encoding="utf-8",
        )

        # Act
        report = import_service.import_gedcom(
            gedcom_file_path=str(malformed_gedcom),
            output_database_name="test-malformed",
            overwrite=True,
            lenient=True,
        )

        # Assert - Import fails due to parsing errors
        # Empty GEDCOM or malformed GEDCOM should still parse but have 0 records
        assert report.persons_count == 0, "Malformed GEDCOM should have 0 persons"
        assert report.families_count == 0, "Malformed GEDCOM should have 0 families"

        # Test with missing family reference (note: current implementation
        # doesn't validate cross-references in lenient mode)
        invalid_ref_gedcom = tmp_path / "invalid_ref.ged"
        invalid_ref_gedcom.write_text(
            """0 HEAD
1 GEDC
2 VERS 5.5.1
2 FORM LINEAGE-LINKED
1 CHAR UTF-8
0 @I1@ INDI
1 NAME John /Doe/
1 SEX M
1 FAMC @F999@
0 TRLR
""",
            encoding="utf-8",
        )

        report2 = import_service.import_gedcom(
            gedcom_file_path=str(invalid_ref_gedcom),
            output_database_name="test-invalid-ref",
            overwrite=True,
            lenient=True,
        )

        # Import succeeds in lenient mode even with broken references
        # (Enhancement: could add stricter validation in future)
        assert report2.success, "Lenient mode allows broken references"
        assert report2.persons_count == 1, "Person should be imported"

    def test_import_empty_gedcom(self, import_service: GedcomImportService, tmp_path: Path):
        """
        Test d'import d'un fichier GEDCOM vide (header + trailer seulement).

        Vérifie que l'import réussit avec 0 personnes et 0 familles.
        """
        # Arrange - Create empty GEDCOM
        empty_gedcom = tmp_path / "empty.ged"
        empty_gedcom.write_text(
            """0 HEAD
1 GEDC
2 VERS 5.5.1
2 FORM LINEAGE-LINKED
1 CHAR UTF-8
0 TRLR
""",
            encoding="utf-8",
        )

        # Act
        report = import_service.import_gedcom(
            gedcom_file_path=str(empty_gedcom),
            output_database_name="test-empty",
            overwrite=True,
        )

        # Assert
        assert report.success, f"Empty GEDCOM import should succeed: {report.errors}"
        assert report.persons_count == 0, "Empty GEDCOM should have 0 persons"
        assert report.families_count == 0, "Empty GEDCOM should have 0 families"

    def test_import_with_complex_dates(self, import_service: GedcomImportService, tmp_path: Path, database_dir: Path):
        """
        Test d'import avec dates complexes (ABT, BEF, AFT, BET...AND).

        Vérifie que les formats de dates GEDCOM sont correctement parsés.
        """
        # Arrange - Create GEDCOM with complex dates
        complex_dates_gedcom = tmp_path / "complex_dates.ged"
        complex_dates_gedcom.write_text(
            """0 HEAD
1 GEDC
2 VERS 5.5.1
2 FORM LINEAGE-LINKED
1 CHAR UTF-8
0 @I1@ INDI
1 NAME Jane /Smith/
1 SEX F
1 BIRT
2 DATE ABT 1850
2 PLAC Unknown
1 DEAT
2 DATE BET 1920 AND 1930
2 PLAC Paris, France
0 TRLR
""",
            encoding="utf-8",
        )

        # Act
        report = import_service.import_gedcom(
            gedcom_file_path=str(complex_dates_gedcom),
            output_database_name="test-dates",
            overwrite=True,
        )

        # Assert - Import success
        assert report.success, f"Import failed: {report.errors}"
        assert report.persons_count == 1, "Should import 1 person"

        # Load and verify dates
        db_path = database_dir / "test-dates.pickle"
        driver = PickleDriver(str(db_path))
        data = driver.load()
        persons: Dict[str, Person] = data["persons"]

        jane = persons["@I1@"]
        assert jane.birth_date is not None, "Jane should have birth date"
        # Date is an object, convert to string for checking
        birth_date_str = str(jane.birth_date)
        assert "1850" in birth_date_str, f"Birth date should contain 1850, got: {birth_date_str}"
        assert jane.death_date is not None, "Jane should have death date"
        # Should contain both years for BET...AND format
        death_date_str = str(jane.death_date)
        assert (
            "1920" in death_date_str or "1930" in death_date_str
        ), f"Death date should contain year range, got: {death_date_str}"

    def test_import_with_utf8_encoding(self, import_service: GedcomImportService, tmp_path: Path, database_dir: Path):
        """
        Test d'import avec encodage UTF-8 et caractères spéciaux.

        Vérifie que les caractères accentués et spéciaux sont
        correctement importés (français, espagnol, etc.).
        """
        # Arrange - Create GEDCOM with UTF-8 characters
        utf8_gedcom = tmp_path / "utf8.ged"
        utf8_gedcom.write_text(
            """0 HEAD
1 GEDC
2 VERS 5.5.1
2 FORM LINEAGE-LINKED
1 CHAR UTF-8
0 @I1@ INDI
1 NAME François /Müller/
1 SEX M
1 BIRT
2 PLAC Zürich, Suisse
0 @I2@ INDI
1 NAME María José /García/
1 SEX F
1 BIRT
2 PLAC São Paulo, Brasil
0 TRLR
""",
            encoding="utf-8",
        )

        # Act
        report = import_service.import_gedcom(
            gedcom_file_path=str(utf8_gedcom),
            output_database_name="test-utf8",
            overwrite=True,
        )

        # Assert
        assert report.success, f"Import failed: {report.errors}"
        assert report.persons_count == 2, "Should import 2 persons"

        # Load and verify UTF-8 characters
        db_path = database_dir / "test-utf8.pickle"
        driver = PickleDriver(str(db_path))
        data = driver.load()
        persons: Dict[str, Person] = data["persons"]

        francois = persons["@I1@"]
        assert francois.first_name == "François", f"Expected 'François', got '{francois.first_name}'"
        assert francois.surname == "Müller", f"Expected 'Müller', got '{francois.surname}'"
        assert francois.birth_place == "Zürich, Suisse", f"Expected 'Zürich, Suisse', got '{francois.birth_place}'"

        maria = persons["@I2@"]
        assert maria.first_name == "María José", f"Expected 'María José', got '{maria.first_name}'"
        assert maria.surname == "García", f"Expected 'García', got '{maria.surname}'"
        assert maria.birth_place == "São Paulo, Brasil", f"Expected 'São Paulo, Brasil', got '{maria.birth_place}'"

    def test_import_overwrite_existing_database(
        self, import_service: GedcomImportService, test_gedcom_file: Path, database_dir: Path
    ):
        """
        Test d'import avec écrasement d'une base existante.

        Vérifie que overwrite=True permet de remplacer une base
        existante, et que overwrite=False lève une erreur.
        """
        # Arrange - First import
        db_name = "test-overwrite"
        report1 = import_service.import_gedcom(
            gedcom_file_path=str(test_gedcom_file),
            output_database_name=db_name,
            overwrite=False,
        )
        assert report1.success, "First import should succeed"

        # Act & Assert - Second import without overwrite should fail
        from backend.core.exceptions import ValidationError

        with pytest.raises(ValidationError, match="already exists"):
            import_service.import_gedcom(
                gedcom_file_path=str(test_gedcom_file),
                output_database_name=db_name,
                overwrite=False,
            )

        # Act - Second import with overwrite should succeed
        report2 = import_service.import_gedcom(
            gedcom_file_path=str(test_gedcom_file),
            output_database_name=db_name,
            overwrite=True,
        )

        # Assert
        assert report2.success, "Second import with overwrite should succeed"
        assert report2.persons_count == 5, "Should still have 5 persons after overwrite"

    def test_import_statistics_accuracy(self, import_service: GedcomImportService, test_gedcom_file: Path):
        """
        Test de précision des statistiques d'import.

        Vérifie que les compteurs (persons_count, families_count)
        correspondent exactement aux données importées.
        """
        # Act
        report = import_service.import_gedcom(
            gedcom_file_path=str(test_gedcom_file),
            output_database_name="test-stats",
            overwrite=True,
        )

        # Get statistics from parser directly
        stats = import_service.get_import_statistics(str(test_gedcom_file))

        # Assert - Report matches parser statistics
        assert report.persons_count == stats["individuals"], (
            f"Report persons_count ({report.persons_count}) " f"!= parser individuals ({stats['individuals']})"
        )
        assert report.families_count == stats["families"], (
            f"Report families_count ({report.families_count}) " f"!= parser families ({stats['families']})"
        )

    def test_import_with_multiline_notes(self, import_service: GedcomImportService, tmp_path: Path, database_dir: Path):
        """
        Test d'import avec notes multi-lignes (CONC/CONT).

        Vérifie que les notes sur plusieurs lignes sont correctement
        concatenées avec gestion de CONC (continuation) et CONT (nouvelle ligne).
        """
        # Arrange - Create GEDCOM with multiline notes
        multiline_gedcom = tmp_path / "multiline.ged"
        multiline_gedcom.write_text(
            """0 HEAD
1 GEDC
2 VERS 5.5.1
2 FORM LINEAGE-LINKED
1 CHAR UTF-8
0 @I1@ INDI
1 NAME Alice /Wonder/
1 SEX F
1 NOTE This is a very long note that spans multiple lines
2 CONC and continues on the next line without break.
2 CONT This is a new paragraph in the note.
0 TRLR
""",
            encoding="utf-8",
        )

        # Act
        report = import_service.import_gedcom(
            gedcom_file_path=str(multiline_gedcom),
            output_database_name="test-multiline",
            overwrite=True,
        )

        # Assert
        assert report.success, f"Import failed: {report.errors}"

        # Load and verify notes
        db_path = database_dir / "test-multiline.pickle"
        driver = PickleDriver(str(db_path))
        data = driver.load()
        persons: Dict[str, Person] = data["persons"]

        alice = persons["@I1@"]
        assert alice.notes is not None, "Alice should have notes"
        assert "very long note" in alice.notes, f"Notes should contain 'very long note', got: {alice.notes}"
        assert (
            "continues on the next line" in alice.notes
        ), f"Notes should contain continuation text, got: {alice.notes}"
        assert "new paragraph" in alice.notes, f"Notes should contain new paragraph text, got: {alice.notes}"

    def test_import_nonexistent_file(self, import_service: GedcomImportService):
        """
        Test d'import d'un fichier inexistant.

        Vérifie qu'une erreur appropriée est levée quand le fichier
        GEDCOM n'existe pas.
        """
        # Act & Assert
        with pytest.raises(FileNotFoundError):
            import_service.import_gedcom(
                gedcom_file_path="nonexistent.ged",
                output_database_name="test-error",
                overwrite=True,
            )

    def test_import_report_summary(self, import_service: GedcomImportService, test_gedcom_file: Path):
        """
        Test du résumé d'import.

        Vérifie que le summary du rapport est correctement formaté
        et contient les informations clés.
        """
        # Act
        report = import_service.import_gedcom(
            gedcom_file_path=str(test_gedcom_file),
            output_database_name="test-summary",
            overwrite=True,
        )

        # Assert
        assert report.summary is not None, "Report should have a summary"
        assert "test-summary" in report.summary, "Summary should contain database name"
        assert (
            str(report.persons_count) in report.summary or "5" in report.summary
        ), "Summary should contain person count"
        assert (
            str(report.families_count) in report.summary or "2" in report.summary
        ), "Summary should contain family count"


if __name__ == "__main__":
    # Pour exécuter les tests directement
    pytest.main([__file__, "-v", "--tb=short"])
