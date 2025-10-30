"""
Tests for GEDCOM parser.

Tests parsing of GEDCOM files according to GEDCOM 5.5.1 specification.
"""

from pathlib import Path

import pytest

from backend.parsers.gedcom_parser import GedcomLine, GedcomParser, GedcomRecord


class TestGedcomLine:
    """Test GEDCOM line parsing."""

    def test_parse_level_zero_with_xref(self):
        """Test parsing level 0 line with cross-reference ID."""
        # Arrange
        line = "0 @I1@ INDI"

        # Act
        parsed = GedcomLine.parse(line, line_number=1)

        # Assert
        assert parsed is not None
        assert parsed.level == 0
        assert parsed.xref_id == "@I1@"
        assert parsed.tag == "INDI"
        assert parsed.value is None

    def test_parse_level_one_with_value(self):
        """Test parsing level 1 line with value."""
        # Arrange
        line = "1 NAME John /Doe/"

        # Act
        parsed = GedcomLine.parse(line, line_number=2)

        # Assert
        assert parsed is not None
        assert parsed.level == 1
        assert parsed.xref_id is None
        assert parsed.tag == "NAME"
        assert parsed.value == "John /Doe/"

    def test_parse_level_two_no_value(self):
        """Test parsing level 2 line without value."""
        # Arrange
        line = "2 GIVN"

        # Act
        parsed = GedcomLine.parse(line, line_number=3)

        # Assert
        assert parsed is not None
        assert parsed.level == 2
        assert parsed.tag == "GIVN"
        assert parsed.value is None

    def test_parse_empty_line_returns_none(self):
        """Test that empty lines return None."""
        # Arrange / Act / Assert
        assert GedcomLine.parse("", line_number=1) is None
        assert GedcomLine.parse("   ", line_number=2) is None

    def test_parse_date_with_spaces(self):
        """Test parsing date value with multiple spaces."""
        # Arrange
        line = "2 DATE 15 JAN 1950"

        # Act
        parsed = GedcomLine.parse(line, line_number=1)

        # Assert
        assert parsed is not None
        assert parsed.value == "15 JAN 1950"

    def test_parse_note_with_long_value(self):
        """Test parsing NOTE with long multi-word value."""
        # Arrange
        line = "1 NOTE This is a long note with many words and spaces."

        # Act
        parsed = GedcomLine.parse(line, line_number=1)

        # Assert
        assert parsed is not None
        assert parsed.tag == "NOTE"
        assert parsed.value == "This is a long note with many words and spaces."


class TestGedcomRecord:
    """Test GEDCOM record structure."""

    def test_get_child_returns_first_match(self):
        """Test get_child returns first child with matching tag."""
        # Arrange
        parent = GedcomRecord(level=0, xref_id="@I1@", tag="INDI", value=None)
        child1 = GedcomRecord(level=1, xref_id=None, tag="NAME", value="John")
        child2 = GedcomRecord(level=1, xref_id=None, tag="SEX", value="M")
        child3 = GedcomRecord(level=1, xref_id=None, tag="NAME", value="Jane")  # duplicate
        parent.children = [child1, child2, child3]

        # Act
        name = parent.get_child("NAME")

        # Assert
        assert name is not None
        assert name.value == "John"  # First one

    def test_get_child_returns_none_if_not_found(self):
        """Test get_child returns None if tag not found."""
        # Arrange
        parent = GedcomRecord(level=0, xref_id="@I1@", tag="INDI", value=None)

        # Act
        result = parent.get_child("NAME")

        # Assert
        assert result is None

    def test_get_children_returns_all_matches(self):
        """Test get_children returns all children with matching tag."""
        # Arrange
        parent = GedcomRecord(level=0, xref_id="@F1@", tag="FAM", value=None)
        child1 = GedcomRecord(level=1, xref_id=None, tag="CHIL", value="@I1@")
        child2 = GedcomRecord(level=1, xref_id=None, tag="HUSB", value="@I2@")
        child3 = GedcomRecord(level=1, xref_id=None, tag="CHIL", value="@I3@")
        parent.children = [child1, child2, child3]

        # Act
        children = parent.get_children("CHIL")

        # Assert
        assert len(children) == 2
        assert children[0].value == "@I1@"
        assert children[1].value == "@I3@"

    def test_get_value_or_default_returns_value(self):
        """Test get_value_or_default returns child value if exists."""
        # Arrange
        parent = GedcomRecord(level=0, xref_id="@I1@", tag="INDI", value=None)
        child = GedcomRecord(level=1, xref_id=None, tag="SEX", value="M")
        parent.children = [child]

        # Act
        sex = parent.get_value_or_default("SEX", "U")

        # Assert
        assert sex == "M"

    def test_get_value_or_default_returns_default_if_not_found(self):
        """Test get_value_or_default returns default if child not found."""
        # Arrange
        parent = GedcomRecord(level=0, xref_id="@I1@", tag="INDI", value=None)

        # Act
        sex = parent.get_value_or_default("SEX", "U")

        # Assert
        assert sex == "U"

    def test_get_concatenated_value_simple(self):
        """Test get_concatenated_value returns simple value."""
        # Arrange
        record = GedcomRecord(level=1, xref_id=None, tag="NAME", value="John Doe")

        # Act
        result = record.get_concatenated_value()

        # Assert
        assert result == "John Doe"

    def test_get_concatenated_value_with_conc(self):
        """Test get_concatenated_value concatenates CONC children (same line)."""
        # Arrange
        parent = GedcomRecord(level=1, xref_id=None, tag="NOTE", value="This is a long note")
        conc1 = GedcomRecord(level=2, xref_id=None, tag="CONC", value=" that continues")
        conc2 = GedcomRecord(level=2, xref_id=None, tag="CONC", value=" on the same line.")
        parent.children = [conc1, conc2]

        # Act
        result = parent.get_concatenated_value()

        # Assert
        assert result == "This is a long note that continues on the same line."

    def test_get_concatenated_value_with_cont(self):
        """Test get_concatenated_value concatenates CONT children (new lines)."""
        # Arrange
        parent = GedcomRecord(level=1, xref_id=None, tag="NOTE", value="First line")
        cont1 = GedcomRecord(level=2, xref_id=None, tag="CONT", value="Second line")
        cont2 = GedcomRecord(level=2, xref_id=None, tag="CONT", value="Third line")
        parent.children = [cont1, cont2]

        # Act
        result = parent.get_concatenated_value()

        # Assert
        assert result == "First line\nSecond line\nThird line"

    def test_get_concatenated_value_mixed_conc_cont(self):
        """Test get_concatenated_value with both CONC and CONT."""
        # Arrange
        parent = GedcomRecord(level=1, xref_id=None, tag="NOTE", value="Line 1")
        conc1 = GedcomRecord(level=2, xref_id=None, tag="CONC", value=" continued")
        cont1 = GedcomRecord(level=2, xref_id=None, tag="CONT", value="Line 2")
        parent.children = [conc1, cont1]

        # Act
        result = parent.get_concatenated_value()

        # Assert
        assert result == "Line 1 continued\nLine 2"


class TestGedcomParser:
    """Test GEDCOM file parsing."""

    @pytest.fixture
    def sample_gedcom_file(self, tmp_path: Path) -> Path:
        """Create a sample GEDCOM file for testing."""
        gedcom_content = """0 HEAD
1 SOUR TestApp
1 CHAR UTF-8
0 @I1@ INDI
1 NAME John /Doe/
1 SEX M
1 BIRT
2 DATE 15 JAN 1950
2 PLAC New York
0 @F1@ FAM
1 HUSB @I1@
0 TRLR
"""
        file_path = tmp_path / "test.ged"
        file_path.write_text(gedcom_content, encoding="utf-8")
        return file_path

    def test_parse_file_success(self, sample_gedcom_file: Path):
        """Test successfully parsing a GEDCOM file."""
        # Arrange
        parser = GedcomParser()

        # Act
        records = parser.parse_file(sample_gedcom_file)

        # Assert
        assert len(records) > 0
        assert records[0].tag == "HEAD"
        assert any(r.tag == "INDI" for r in records)
        assert any(r.tag == "FAM" for r in records)

    def test_parse_file_not_found_raises_error(self):
        """Test parsing non-existent file raises FileNotFoundError."""
        # Arrange
        parser = GedcomParser()
        nonexistent_file = Path("/nonexistent/file.ged")

        # Act / Assert
        with pytest.raises(FileNotFoundError):
            parser.parse_file(nonexistent_file)

    def test_get_individuals(self, sample_gedcom_file: Path):
        """Test extracting individual records."""
        # Arrange
        parser = GedcomParser()
        records = parser.parse_file(sample_gedcom_file)

        # Act
        individuals = parser.get_individuals(records)

        # Assert
        assert len(individuals) == 1
        assert individuals[0].tag == "INDI"
        assert individuals[0].xref_id == "@I1@"

    def test_get_families(self, sample_gedcom_file: Path):
        """Test extracting family records."""
        # Arrange
        parser = GedcomParser()
        records = parser.parse_file(sample_gedcom_file)

        # Act
        families = parser.get_families(records)

        # Assert
        assert len(families) == 1
        assert families[0].tag == "FAM"
        assert families[0].xref_id == "@F1@"

    def test_get_statistics(self, sample_gedcom_file: Path):
        """Test getting statistics about parsed records."""
        # Arrange
        parser = GedcomParser()
        records = parser.parse_file(sample_gedcom_file)

        # Act
        stats = parser.get_statistics(records)

        # Assert
        assert "INDI" in stats
        assert "FAM" in stats
        assert "HEAD" in stats
        assert stats["INDI"] == 1
        assert stats["FAM"] == 1

    def test_parse_test_family_file(self):
        """Test parsing the test family GEDCOM file."""
        # Arrange
        test_file = Path("tests/fixtures/test_family.ged")
        if not test_file.exists():
            pytest.skip("Test file not found")

        parser = GedcomParser()

        # Act
        records = parser.parse_file(test_file)

        # Assert
        assert len(records) > 0

        # Get statistics
        stats = parser.get_statistics(records)
        assert stats["INDI"] == 5  # John, Jane, Mary, Robert, Margaret
        assert stats["FAM"] == 2  # F1, F2

        # Check individuals
        individuals = parser.get_individuals(records)
        assert len(individuals) == 5

        # Check families
        families = parser.get_families(records)
        assert len(families) == 2
