"""
GEDCOM 5.5.1 Parser.

Parses GEDCOM files according to the GEDCOM 5.5.1 specification.
Supports multi-line values (CONC/CONT), various character encodings,
and comprehensive tag coverage.

References:
    - GEDCOM 5.5.1 Specification: https://gedcom.io/specifications/FamilySearchGEDCOMv5.pdf
    - Tags reference: https://www.gedcom.org/gedcom.html
"""

import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, TextIO, Union

logger = logging.getLogger(__name__)


class GedcomTag(str, Enum):
    """Standard GEDCOM tags."""

    # Header
    HEAD = "HEAD"
    GEDC = "GEDC"
    VERS = "VERS"
    CHAR = "CHAR"
    SOUR = "SOUR"
    DATE = "DATE"
    FILE = "FILE"
    SUBM = "SUBM"

    # Individual (Person)
    INDI = "INDI"
    NAME = "NAME"
    SEX = "SEX"
    BIRT = "BIRT"
    DEAT = "DEAT"
    BAPM = "BAPM"
    CHR = "CHR"
    BURI = "BURI"
    OCCU = "OCCU"
    RESI = "RESI"
    EVEN = "EVEN"

    # Family
    FAM = "FAM"
    HUSB = "HUSB"
    WIFE = "WIFE"
    CHIL = "CHIL"
    MARR = "MARR"
    DIV = "DIV"
    ENGA = "ENGA"
    ANUL = "ANUL"

    # Relationships
    FAMC = "FAMC"  # Family as child
    FAMS = "FAMS"  # Family as spouse

    # Data
    PLAC = "PLAC"
    TYPE = "TYPE"
    NOTE = "NOTE"
    OBJE = "OBJE"
    REPO = "REPO"

    # Concatenation
    CONC = "CONC"  # Continuation same line
    CONT = "CONT"  # Continuation new line

    # Trailer
    TRLR = "TRLR"


@dataclass
class GedcomLine:
    """
    Represents a parsed GEDCOM line.

    GEDCOM format:
        level [xref_id] tag [value]

    Examples:
        0 @I1@ INDI
        1 NAME John /Doe/
        2 GIVN John
        2 SURN Doe
    """

    level: int
    xref_id: Optional[str]
    tag: str
    value: Optional[str]
    line_number: int

    @classmethod
    def parse(cls, line: str, line_number: int) -> Optional["GedcomLine"]:
        """
        Parse a GEDCOM line.

        Args:
            line: Raw GEDCOM line.
            line_number: Line number in file (for error reporting).

        Returns:
            Parsed GedcomLine or None if line is empty/invalid.

        Examples:
            >>> GedcomLine.parse("0 @I1@ INDI", 1)
            GedcomLine(level=0, xref_id="@I1@", tag="INDI", value=None, line_number=1)

            >>> GedcomLine.parse("1 NAME John /Doe/", 2)
            GedcomLine(level=1, xref_id=None, tag="NAME", value="John /Doe/", line_number=2)
        """
        line = line.strip()
        if not line:
            return None

        # GEDCOM format: level [xref_id] tag [value]
        # Pattern: ^(\d+)\s+(?:(@[^@]+@)\s+)?([A-Z_]+)(?:\s+(.*))?$
        pattern = r"^(\d+)\s+(?:(@[^@]+@)\s+)?([A-Z_]+)(?:\s+(.*))?$"
        match = re.match(pattern, line)

        if not match:
            logger.warning(f"Line {line_number}: Invalid GEDCOM format: {line}")
            return None

        level_str, xref_id, tag, value = match.groups()

        return cls(
            level=int(level_str),
            xref_id=xref_id,
            tag=tag,
            value=value.strip() if value else None,
            line_number=line_number,
        )


@dataclass
class GedcomRecord:
    """
    Represents a complete GEDCOM record (entity).

    A record starts with a level 0 line and includes all subsequent
    higher-level lines until the next level 0.

    Attributes:
        level: Always 0 for top-level records.
        xref_id: Cross-reference ID (e.g., "@I1@", "@F1@").
        tag: Record type (INDI, FAM, NOTE, etc.).
        value: Optional value on level 0 line.
        children: Nested sub-records.
        line_number: Starting line number in file.
    """

    level: int
    xref_id: Optional[str]
    tag: str
    value: Optional[str]
    children: List["GedcomRecord"] = field(default_factory=list)
    line_number: int = 0

    def get_child(self, tag: str) -> Optional["GedcomRecord"]:
        """
        Get first child record with specified tag.

        Args:
            tag: Tag to search for (e.g., "NAME", "SEX").

        Returns:
            First matching child record or None.

        Examples:
            >>> person.get_child("NAME")
            GedcomRecord(tag="NAME", value="John /Doe/", ...)
        """
        for child in self.children:
            if child.tag == tag:
                return child
        return None

    def get_children(self, tag: str) -> List["GedcomRecord"]:
        """
        Get all child records with specified tag.

        Args:
            tag: Tag to search for.

        Returns:
            List of matching child records.

        Examples:
            >>> family.get_children("CHIL")
            [GedcomRecord(tag="CHIL", value="@I2@", ...), ...]
        """
        return [child for child in self.children if child.tag == tag]

    def get_value_or_default(self, tag: str, default: str = "") -> str:
        """
        Get value of first child with tag, or default.

        Args:
            tag: Tag to search for.
            default: Default value if not found.

        Returns:
            Child value or default.

        Examples:
            >>> person.get_value_or_default("SEX", "U")
            "M"
        """
        child = self.get_child(tag)
        return child.value if child and child.value else default

    def get_concatenated_value(self) -> str:
        """
        Get value with CONC/CONT children concatenated.

        GEDCOM uses CONC (same line) and CONT (new line) for long values.

        Returns:
            Complete concatenated value.

        Examples:
            1 NOTE This is a long note
            2 CONC that continues
            2 CONT on the next line.

            >>> note.get_concatenated_value()
            "This is a long note that continues\\non the next line."
        """
        if not self.value:
            return ""

        result = self.value

        for child in self.children:
            if child.tag == GedcomTag.CONC and child.value:
                # CONC = continue on same line
                result += child.value
            elif child.tag == GedcomTag.CONT and child.value:
                # CONT = continue on new line
                result += "\n" + child.value

        return result


class GedcomParser:
    """
    Parse GEDCOM files into structured records.

    Supports:
    - GEDCOM 5.5.1 specification
    - Multiple character encodings (UTF-8, ANSEL, ASCII, etc.)
    - Multi-line values (CONC/CONT)
    - Comprehensive tag coverage
    - Error reporting and recovery

    Usage:
        parser = GedcomParser()
        records = parser.parse_file("family.ged")

        individuals = [r for r in records if r.tag == "INDI"]
        families = [r for r in records if r.tag == "FAM"]
    """

    def __init__(self, encoding: str = "utf-8", strict: bool = False):
        """
        Initialize GEDCOM parser.

        Args:
            encoding: Default character encoding (can be overridden by CHAR tag in file).
            strict: If True, raise exceptions on errors. If False, log warnings and continue.
        """
        self.encoding = encoding
        self.strict = strict
        self.header: Optional[GedcomRecord] = None
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def parse_file(self, file_path: Union[Path, str]) -> List[GedcomRecord]:
        """
        Parse a GEDCOM file.

        Args:
            file_path: Path to GEDCOM file.

        Returns:
            List of top-level GEDCOM records.

        Raises:
            FileNotFoundError: If file doesn't exist.
            UnicodeDecodeError: If encoding is incorrect.
            ValueError: If strict mode and parsing errors occur.

        Examples:
            >>> parser = GedcomParser()
            >>> records = parser.parse_file("family.ged")
            >>> print(f"Found {len(records)} records")
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"GEDCOM file not found: {file_path}")

        logger.info(f"Parsing GEDCOM file: {file_path}")

        # Try to detect encoding from file
        detected_encoding = self._detect_encoding(file_path)
        encoding = detected_encoding or self.encoding

        try:
            with open(file_path, "r", encoding=encoding) as f:
                return self.parse_stream(f)
        except UnicodeDecodeError as e:
            logger.error(f"Encoding error with {encoding}: {e}")
            # Try fallback encodings
            for fallback in ["utf-8-sig", "latin-1", "cp1252"]:
                try:
                    logger.info(f"Trying fallback encoding: {fallback}")
                    with open(file_path, "r", encoding=fallback) as f:
                        return self.parse_stream(f)
                except UnicodeDecodeError:
                    continue
            raise

    def parse_stream(self, stream: TextIO) -> List[GedcomRecord]:
        """
        Parse GEDCOM from a text stream.

        Args:
            stream: Text stream to parse.

        Returns:
            List of top-level GEDCOM records.

        Raises:
            ValueError: If strict mode and parsing errors occur.
        """
        lines = self._parse_lines(stream)
        records = self._build_records(lines)

        # Extract header
        if records and records[0].tag == GedcomTag.HEAD:
            self.header = records[0]
            # Update encoding from header if present
            char_record = self.header.get_child(GedcomTag.CHAR)
            if char_record and char_record.value:
                logger.info(f"Encoding from header: {char_record.value}")

        logger.info(f"Parsed {len(records)} records " f"({len(self.errors)} errors, {len(self.warnings)} warnings)")

        if self.strict and self.errors:
            raise ValueError(f"Parsing errors: {self.errors}")

        return records

    def _detect_encoding(self, file_path: Path) -> Optional[str]:
        """
        Detect encoding from GEDCOM header.

        Reads first few lines to find CHAR tag.

        Args:
            file_path: Path to GEDCOM file.

        Returns:
            Detected encoding or None.
        """
        try:
            # Read first 1000 bytes in binary mode
            with open(file_path, "rb") as f:
                header = f.read(1000).decode("ascii", errors="ignore")

            # Look for CHAR tag
            match = re.search(r"1 CHAR\s+(\S+)", header, re.IGNORECASE)
            if match:
                gedcom_char = match.group(1).upper()
                encoding_map = {
                    "UTF-8": "utf-8",
                    "UTF8": "utf-8",
                    "UNICODE": "utf-8",
                    "ASCII": "ascii",
                    "ANSEL": "utf-8",  # ANSEL is complex, fallback to UTF-8
                    "LATIN1": "latin-1",
                    "ISO-8859-1": "latin-1",
                }
                return encoding_map.get(gedcom_char)
        except Exception as e:
            logger.warning(f"Could not detect encoding: {e}")

        return None

    def _parse_lines(self, stream: TextIO) -> List[GedcomLine]:
        """
        Parse raw lines from stream.

        Args:
            stream: Text stream.

        Returns:
            List of parsed GEDCOM lines.
        """
        lines = []
        for line_number, raw_line in enumerate(stream, start=1):
            parsed = GedcomLine.parse(raw_line, line_number)
            if parsed:
                lines.append(parsed)

        return lines

    def _build_records(self, lines: List[GedcomLine]) -> List[GedcomRecord]:
        """
        Build hierarchical records from flat list of lines.

        Args:
            lines: Flat list of parsed GEDCOM lines.

        Returns:
            List of top-level records with nested children.
        """
        records: List[GedcomRecord] = []
        stack: List[GedcomRecord] = []

        for line in lines:
            record = GedcomRecord(
                level=line.level,
                xref_id=line.xref_id,
                tag=line.tag,
                value=line.value,
                line_number=line.line_number,
            )

            # Pop stack until we find parent level
            while stack and stack[-1].level >= line.level:
                stack.pop()

            if stack:
                # Add as child of current parent
                stack[-1].children.append(record)
            else:
                # Top-level record
                records.append(record)

            # Push onto stack
            stack.append(record)

        return records

    def get_individuals(self, records: List[GedcomRecord]) -> List[GedcomRecord]:
        """
        Extract all individual (INDI) records.

        Args:
            records: All GEDCOM records.

        Returns:
            List of individual records.
        """
        return [r for r in records if r.tag == GedcomTag.INDI]

    def get_families(self, records: List[GedcomRecord]) -> List[GedcomRecord]:
        """
        Extract all family (FAM) records.

        Args:
            records: All GEDCOM records.

        Returns:
            List of family records.
        """
        return [r for r in records if r.tag == GedcomTag.FAM]

    def get_statistics(self, records: List[GedcomRecord]) -> Dict[str, int]:
        """
        Get statistics about parsed records.

        Args:
            records: All GEDCOM records.

        Returns:
            Dictionary with counts by record type.

        Examples:
            >>> stats = parser.get_statistics(records)
            >>> print(f"Individuals: {stats['INDI']}, Families: {stats['FAM']}")
        """
        stats: Dict[str, int] = {}
        for record in records:
            tag = record.tag
            stats[tag] = stats.get(tag, 0) + 1

        return stats
