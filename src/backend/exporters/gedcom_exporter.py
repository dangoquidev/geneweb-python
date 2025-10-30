"""
GEDCOM 5.5.1 Exporter.

Exports GenEWeb Person and Family models to GEDCOM 5.5.1 format.

References:
    - GEDCOM 5.5.1 Specification: https://gedcom.io/specifications/FamilySearchGEDCOMv5.pdf
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, TextIO, Union

from backend.core.models import Date, Family, Person, Sex

logger = logging.getLogger(__name__)


class GedcomExporter:
    """
    Export GenEWeb data to GEDCOM 5.5.1 format.

    Converts Person and Family models to GEDCOM records following
    the GEDCOM 5.5.1 specification.

    Usage:
        exporter = GedcomExporter()
        exporter.export(
            persons=persons_dict,
            families=families_dict,
            output_file="family.ged"
        )
    """

    def __init__(
        self,
        encoding: str = "UTF-8",
        include_notes: bool = True,
        include_images: bool = True,
    ):
        """
        Initialize GEDCOM exporter.

        Args:
            encoding: Character encoding for output (default: UTF-8).
            include_notes: Include notes and comments in export (default: True).
            include_images: Include image references in export (default: True).
        """
        self.encoding = encoding
        self.include_notes = include_notes
        self.include_images = include_images
        self.person_counter = 0
        self.family_counter = 0
        self.person_id_map: Dict[str, str] = {}  # GenEWeb ID -> GEDCOM XREF
        self.family_id_map: Dict[str, str] = {}  # GenEWeb ID -> GEDCOM XREF

    def export(
        self,
        persons: Dict[str, Person],
        families: Dict[str, Family],
        output_file: Union[str, Path],
        database_name: str = "GenEWeb",
    ) -> None:
        """
        Export persons and families to GEDCOM file.

        Args:
            persons: Dictionary of Person objects (ID -> Person).
            families: Dictionary of Family objects (ID -> Family).
            output_file: Path to output GEDCOM file.
            database_name: Name of source database.

        Examples:
            >>> exporter = GedcomExporter()
            >>> exporter.export(persons, families, "family.ged", "MyFamily")
        """
        output_file = Path(output_file)

        logger.info(f"Exporting {len(persons)} persons, {len(families)} families to {output_file}")

        # Build ID maps
        self._build_id_maps(persons, families)

        # Write GEDCOM file
        with open(output_file, "w", encoding=self.encoding) as f:
            self._write_header(f, database_name)
            self._write_persons(f, persons)
            self._write_families(f, families)
            self._write_trailer(f)

        logger.info(f"✅ Exported to {output_file}")

    def export_to_string(
        self,
        persons: Dict[str, Person],
        families: Dict[str, Family],
        database_name: str = "GenEWeb",
    ) -> str:
        """
        Export persons and families to GEDCOM string.

        Args:
            persons: Dictionary of Person objects.
            families: Dictionary of Family objects.
            database_name: Name of source database.

        Returns:
            GEDCOM content as string.
        """
        from io import StringIO

        # Build ID maps
        self._build_id_maps(persons, families)

        output = StringIO()
        self._write_header(output, database_name)
        self._write_persons(output, persons)
        self._write_families(output, families)
        self._write_trailer(output)

        return output.getvalue()

    def _build_id_maps(self, persons: Dict[str, Person], families: Dict[str, Family]) -> None:
        """
        Build mappings from GenEWeb IDs to GEDCOM XREFs.

        Args:
            persons: Dictionary of Person objects.
            families: Dictionary of Family objects.
        """
        self.person_counter = 0
        self.family_counter = 0
        self.person_id_map = {}
        self.family_id_map = {}

        # Map persons
        for person_id in sorted(persons.keys()):
            self.person_counter += 1
            self.person_id_map[person_id] = f"@I{self.person_counter}@"

        # Map families
        for family_id in sorted(families.keys()):
            self.family_counter += 1
            self.family_id_map[family_id] = f"@F{self.family_counter}@"

    def _write_header(self, f: TextIO, database_name: str) -> None:
        """
        Write GEDCOM header.

        Args:
            f: Output file stream.
            database_name: Name of source database.
        """
        now = datetime.now()
        date_str = now.strftime("%d %b %Y").upper()
        time_str = now.strftime("%H:%M:%S")

        f.write("0 HEAD\n")
        f.write("1 SOUR GenEWeb\n")
        f.write("2 VERS 1.0\n")
        f.write("2 NAME GenEWeb Python\n")
        f.write("2 CORP GenEWeb Project\n")
        f.write("3 ADDR https://github.com/geneweb\n")
        f.write(f"2 DATA {database_name}\n")
        f.write(f"1 DATE {date_str}\n")
        f.write(f"2 TIME {time_str}\n")
        f.write("1 GEDC\n")
        f.write("2 VERS 5.5.1\n")
        f.write("2 FORM LINEAGE-LINKED\n")
        f.write(f"1 CHAR {self.encoding}\n")
        f.write("1 LANG French\n")

    def _write_persons(self, f: TextIO, persons: Dict[str, Person]) -> None:
        """
        Write all person records.

        Args:
            f: Output file stream.
            persons: Dictionary of Person objects.
        """
        for person_id in sorted(persons.keys()):
            person = persons[person_id]
            xref = self.person_id_map[person_id]
            self._write_person(f, person, xref)

    def _write_person(self, f: TextIO, person: Person, xref: str) -> None:
        """
        Write a single person (INDI) record.

        Args:
            f: Output file stream.
            person: Person object.
            xref: GEDCOM XREF (e.g., @I1@).
        """
        f.write(f"0 {xref} INDI\n")

        # Name
        name = self._format_name(person.first_name, person.surname)
        f.write(f"1 NAME {name}\n")

        if person.first_name:
            f.write(f"2 GIVN {self._escape(person.first_name)}\n")
        if person.surname:
            f.write(f"2 SURN {self._escape(person.surname)}\n")

        # Sex
        sex_value = self._format_sex(person.sex)
        if sex_value:
            f.write(f"1 SEX {sex_value}\n")

        # Birth
        if person.birth_date or person.birth_place:
            f.write("1 BIRT\n")
            if person.birth_date:
                date_str = self._format_date(person.birth_date)
                if date_str:
                    f.write(f"2 DATE {date_str}\n")
            if person.birth_place:
                f.write(f"2 PLAC {self._escape(person.birth_place)}\n")

        # Death
        if person.death_date or person.death_place:
            f.write("1 DEAT\n")
            if person.death_date:
                date_str = self._format_date(person.death_date)
                if date_str:
                    f.write(f"2 DATE {date_str}\n")
            if person.death_place:
                f.write(f"2 PLAC {self._escape(person.death_place)}\n")

        # Occupation
        if person.occupation:
            f.write(f"1 OCCU {self._escape(person.occupation)}\n")

        # Notes (only if include_notes is True)
        if self.include_notes and person.notes:
            self._write_note(f, person.notes, level=1)

        # Family as child (FAMC)
        if person.family_id and person.family_id in self.family_id_map:
            family_xref = self.family_id_map[person.family_id]
            f.write(f"1 FAMC {family_xref}\n")

        # Families as spouse (FAMS)
        if person.family_ids:
            for family_id in person.family_ids:
                if family_id in self.family_id_map:
                    family_xref = self.family_id_map[family_id]
                    f.write(f"1 FAMS {family_xref}\n")

    def _write_families(self, f: TextIO, families: Dict[str, Family]) -> None:
        """
        Write all family records.

        Args:
            f: Output file stream.
            families: Dictionary of Family objects.
        """
        for family_id in sorted(families.keys()):
            family = families[family_id]
            xref = self.family_id_map[family_id]
            self._write_family(f, family, xref)

    def _write_family(self, f: TextIO, family: Family, xref: str) -> None:
        """
        Write a single family (FAM) record.

        Args:
            f: Output file stream.
            family: Family object.
            xref: GEDCOM XREF (e.g., @F1@).
        """
        f.write(f"0 {xref} FAM\n")

        # Husband (father)
        if family.father_id and family.father_id in self.person_id_map:
            husband_xref = self.person_id_map[family.father_id]
            f.write(f"1 HUSB {husband_xref}\n")

        # Wife (mother)
        if family.mother_id and family.mother_id in self.person_id_map:
            wife_xref = self.person_id_map[family.mother_id]
            f.write(f"1 WIFE {wife_xref}\n")

        # Children
        for child_id in family.children_ids:
            if child_id in self.person_id_map:
                child_xref = self.person_id_map[child_id]
                f.write(f"1 CHIL {child_xref}\n")

        # Marriage
        if family.marriage_date or family.marriage_place:
            f.write("1 MARR\n")
            if family.marriage_date:
                date_str = self._format_date(family.marriage_date)
                if date_str:
                    f.write(f"2 DATE {date_str}\n")
            if family.marriage_place:
                f.write(f"2 PLAC {self._escape(family.marriage_place)}\n")

        # Divorce
        if family.divorce_date:
            f.write("1 DIV\n")
            date_str = self._format_date(family.divorce_date)
            if date_str:
                f.write(f"2 DATE {date_str}\n")

        # Notes (only if include_notes is True)
        if self.include_notes and family.notes:
            self._write_note(f, family.notes, level=1)

    def _write_trailer(self, f: TextIO) -> None:
        """
        Write GEDCOM trailer.

        Args:
            f: Output file stream.
        """
        f.write("0 TRLR\n")

    def _write_note(self, f: TextIO, note: str, level: int = 1) -> None:
        """
        Write NOTE record with proper line wrapping.

        GEDCOM limits lines to ~255 characters. Long notes are split
        using CONT (continuation) tags.

        Args:
            f: Output file stream.
            note: Note text.
            level: GEDCOM level (default: 1).
        """
        # Split into lines
        lines = note.split("\n")

        if not lines:
            return

        # Write first line as NOTE
        first_line = self._escape(lines[0])
        if len(first_line) > 248:  # Leave room for level + " NOTE "
            # Split long first line
            f.write(f"{level} NOTE {first_line[:248]}\n")
            remainder = first_line[248:]
            while remainder:
                chunk = remainder[:248]
                f.write(f"{level + 1} CONC {chunk}\n")
                remainder = remainder[248:]
        else:
            f.write(f"{level} NOTE {first_line}\n")

        # Write remaining lines as CONT
        for line in lines[1:]:
            escaped = self._escape(line)
            if len(escaped) > 248:
                # Split long line
                f.write(f"{level + 1} CONT {escaped[:248]}\n")
                remainder = escaped[248:]
                while remainder:
                    chunk = remainder[:248]
                    f.write(f"{level + 1} CONC {chunk}\n")
                    remainder = remainder[248:]
            else:
                f.write(f"{level + 1} CONT {escaped}\n")

    def _format_name(self, first_name: str, surname: str) -> str:
        """
        Format name in GEDCOM format: FirstName /Surname/.

        Args:
            first_name: First name(s).
            surname: Surname.

        Returns:
            Formatted name string.
        """
        first = self._escape(first_name) if first_name else ""
        last = self._escape(surname) if surname else ""

        if first and last:
            return f"{first} /{last}/"
        elif first:
            return first
        elif last:
            return f"/{last}/"
        else:
            return "?"

    def _format_sex(self, sex: Sex) -> str:
        """
        Format sex for GEDCOM.

        Args:
            sex: Sex enum value.

        Returns:
            GEDCOM sex code (M, F, or U).
        """
        if sex == Sex.MALE:
            return "M"
        elif sex == Sex.FEMALE:
            return "F"
        else:
            return "U"

    def _format_date(self, date: Optional[Date]) -> str:
        """
        Format date in GEDCOM format.

        GEDCOM date format: DD MMM YYYY (e.g., "25 DEC 1950")

        Args:
            date: Date object.

        Returns:
            Formatted date string or empty string.
        """
        if not date:
            return ""

        parts = []

        # Day
        if date.day:
            parts.append(f"{date.day:02d}")

        # Month
        if date.month:
            months = ["", "JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
            if 1 <= date.month <= 12:
                parts.append(months[date.month])

        # Year
        if date.year:
            parts.append(str(date.year))

        return " ".join(parts) if parts else ""

    def _escape(self, text: str) -> str:
        """
        Escape special characters for GEDCOM.

        GEDCOM uses @ as special character for XREFs.

        Args:
            text: Text to escape.

        Returns:
            Escaped text.
        """
        if not text:
            return ""

        # Replace @ with @@ (GEDCOM escape)
        text = text.replace("@", "@@")

        # Remove or replace control characters
        text = "".join(c if ord(c) >= 32 or c in "\n\r\t" else " " for c in text)

        return text.strip()
