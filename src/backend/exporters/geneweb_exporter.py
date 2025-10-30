"""
GeneWeb .gw Exporter.

Exports GenEWeb Person and Family models to GeneWeb .gw source format.

References:
    - GeneWeb documentation: https://geneweb.tuxfamily.org/wiki/
    - OCaml source: legacy/ocaml-old-project/bin/gwu/gwuLib.ml
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, TextIO, Union

from backend.core.models import Date, Family, Person, Sex

logger = logging.getLogger(__name__)


class GeneWebExporter:
    """
    Export GenEWeb data to GeneWeb .gw source format.

    Converts Person and Family models to GeneWeb .gw format which can be
    reimported without loss of information.

    Usage:
        exporter = GeneWebExporter()
        exporter.export(
            persons=persons_dict,
            families=families_dict,
            output_file="family.gw"
        )
    """

    def __init__(
        self,
        encoding: str = "utf-8",
        include_notes: bool = True,
    ):
        """
        Initialize GeneWeb exporter.

        Args:
            encoding: Character encoding for output (default: utf-8).
            include_notes: Include notes and comments in export (default: True).
        """
        self.encoding = encoding
        self.include_notes = include_notes
        self.person_map: Dict[str, Person] = {}
        self.family_map: Dict[str, Family] = {}

    def export(
        self,
        persons: Dict[str, Person],
        families: Dict[str, Family],
        output_file: Union[str, Path],
        database_name: str = "GenEWeb",
    ) -> None:
        """
        Export persons and families to GeneWeb .gw file.

        Args:
            persons: Dictionary of Person objects (ID -> Person).
            families: Dictionary of Family objects (ID -> Family).
            output_file: Path to output .gw file.
            database_name: Name of source database (for reference).

        Examples:
            >>> exporter = GeneWebExporter()
            >>> exporter.export(persons, families, "family.gw", "MyFamily")
        """
        output_file = Path(output_file)

        logger.info(f"Exporting {len(persons)} persons, {len(families)} families to {output_file}")

        self.person_map = persons
        self.family_map = families

        # Write GeneWeb file
        with open(output_file, "w", encoding=self.encoding) as f:
            self._write_header(f)
            self._write_families(f, families, persons)
            if self.include_notes:
                self._write_notes(f, persons)
            self._write_events(f, persons)

        logger.info(f"✅ Exported to {output_file}")

    def export_to_string(
        self,
        persons: Dict[str, Person],
        families: Dict[str, Family],
        database_name: str = "GenEWeb",
    ) -> str:
        """
        Export persons and families to GeneWeb string.

        Args:
            persons: Dictionary of Person objects.
            families: Dictionary of Family objects.
            database_name: Name of source database.

        Returns:
            GeneWeb .gw content as string.
        """
        from io import StringIO

        self.person_map = persons
        self.family_map = families

        output = StringIO()
        self._write_header(output)
        self._write_families(output, families, persons)
        if self.include_notes:
            self._write_notes(output, persons)
        self._write_events(output, persons)

        return output.getvalue()

    def _write_header(self, f: TextIO) -> None:
        """
        Write GeneWeb file header.

        Args:
            f: Output file stream.
        """
        f.write(f"encoding: {self.encoding}\n")
        f.write("gwplus\n")
        f.write("\n")

    def _write_families(self, f: TextIO, families: Dict[str, Family], persons: Dict[str, Person]) -> None:
        """
        Write all family records.

        Args:
            f: Output file stream.
            families: Dictionary of Family objects.
            persons: Dictionary of Person objects.
        """
        for family_id in sorted(families.keys()):
            family = families[family_id]
            self._write_family(f, family, persons)
            f.write("\n")

    def _write_family(self, f: TextIO, family: Family, persons: Dict[str, Person]) -> None:
        """
        Write a single family record.

        Format:
            fam Surname Father_FirstName [fields] +date + Surname Mother_FirstName [fields] date
            [fevt ... end fevt]
            beg
            - sex Child_FirstName date date
            ...
            end

        Args:
            f: Output file stream.
            family: Family object.
            persons: Dictionary of Person objects.
        """
        # Get father and mother
        father = persons.get(family.father_id) if family.father_id else None
        mother = persons.get(family.mother_id) if family.mother_id else None

        # Start family line
        f.write("fam ")

        # Write father
        if father:
            self._write_person_reference(f, father)
        else:
            f.write("? ? 0")

        # Marriage date
        if family.marriage_date:
            f.write(f" {self._format_date(family.marriage_date)}")

        # Separator
        f.write(" + ")

        # Write mother
        if mother:
            self._write_person_reference(f, mother)
        else:
            f.write("? ? 0")

        f.write("\n")

        # Family events
        if family.marriage_date or family.marriage_place or family.divorce_date:
            f.write("fevt\n")

            if family.marriage_date or family.marriage_place:
                f.write("#marr")
                if family.marriage_date:
                    f.write(f" {self._format_date(family.marriage_date)}")
                if family.marriage_place:
                    f.write(f" #p {self._escape(family.marriage_place)}")
                f.write("\n")

            if family.divorce_date:
                f.write(f"#div {self._format_date(family.divorce_date)}\n")

            f.write("end fevt\n")

        # Family notes (only if include_notes is True)
        if self.include_notes and family.notes:
            for line in family.notes.split("\n"):
                f.write(f"note {line}\n")

        # Children
        children = self._get_children(family, persons)
        if children:
            f.write("beg\n")
            for child in children:
                self._write_child(f, child)
            f.write("end\n")

    def _write_person_reference(self, f: TextIO, person: Person) -> None:
        """
        Write a person reference in family context.

        Format: Surname FirstName [#fields] occurrence [dates]

        Args:
            f: Output file stream.
            person: Person object.
        """
        # Surname
        surname = self._format_name_part(person.surname) or "?"
        f.write(surname)
        f.write(" ")

        # First name
        first_name = self._format_name_part(person.first_name) or "?"
        f.write(first_name)

        # Occupation
        if person.occupation:
            f.write(f" #occu {self._format_name_part(person.occupation)}")

        # Occurrence (always 0 for now)
        f.write(" 0")

        # Birth date
        if person.birth_date:
            f.write(f" {self._format_date(person.birth_date)}")

        # Death marker
        if person.death_date:
            f.write(" od")

    def _write_child(self, f: TextIO, child: Person) -> None:
        """
        Write a child entry in family children list.

        Format: - sex FirstName [dates]

        Args:
            f: Output file stream.
            child: Child Person object.
        """
        f.write("- ")

        # Sex
        if child.sex == Sex.MALE:
            f.write("h ")
        elif child.sex == Sex.FEMALE:
            f.write("f ")
        else:
            f.write("? ")

        # First name
        first_name = self._format_name_part(child.first_name) or "?"
        f.write(first_name)

        # Birth date
        if child.birth_date:
            f.write(f" {self._format_date(child.birth_date)}")

        # Death date/marker
        if child.death_date:
            death_str = self._format_date(child.death_date)
            if death_str:
                f.write(f" {death_str}")
            else:
                f.write(" od")

        f.write("\n")

    def _write_notes(self, f: TextIO, persons: Dict[str, Person]) -> None:
        """
        Write notes blocks for persons.

        Format:
            notes Surname FirstName
            beg
            ... note content ...
            end notes

        Args:
            f: Output file stream.
            persons: Dictionary of Person objects.
        """
        for person_id in sorted(persons.keys()):
            person = persons[person_id]

            if person.notes:
                f.write("\n")
                surname = self._format_name_part(person.surname) or "?"
                first_name = self._format_name_part(person.first_name) or "?"
                f.write(f"notes {surname} {first_name}\n")
                f.write("beg\n")

                # Write note content
                for line in person.notes.split("\n"):
                    f.write(f"{line}\n")

                f.write("end notes\n")

    def _write_events(self, f: TextIO, persons: Dict[str, Person]) -> None:
        """
        Write personal events blocks.

        Format:
            pevt Surname FirstName
            #birt date #p place
            #deat date #p place
            end pevt

        Args:
            f: Output file stream.
            persons: Dictionary of Person objects.
        """
        for person_id in sorted(persons.keys()):
            person = persons[person_id]

            # Check if person has events to write
            has_events = (
                person.birth_date
                or person.birth_place
                or person.death_date
                or person.death_place
                or person.baptism_date
                or person.baptism_place
                or person.burial_date
                or person.burial_place
            )

            if has_events:
                f.write("\n")
                surname = self._format_name_part(person.surname) or "?"
                first_name = self._format_name_part(person.first_name) or "?"
                f.write(f"pevt {surname} {first_name}\n")

                # Birth
                if person.birth_date or person.birth_place:
                    f.write("#birt")
                    if person.birth_date:
                        f.write(f" {self._format_date(person.birth_date)}")
                    if person.birth_place:
                        f.write(f" #p {self._escape(person.birth_place)}")
                    f.write("\n")

                # Baptism
                if person.baptism_date or person.baptism_place:
                    f.write("#bapm")
                    if person.baptism_date:
                        f.write(f" {self._format_date(person.baptism_date)}")
                    if person.baptism_place:
                        f.write(f" #p {self._escape(person.baptism_place)}")
                    f.write("\n")

                # Death
                if person.death_date or person.death_place:
                    f.write("#deat")
                    if person.death_date:
                        f.write(f" {self._format_date(person.death_date)}")
                    if person.death_place:
                        f.write(f" #p {self._escape(person.death_place)}")
                    f.write("\n")

                # Burial
                if person.burial_date or person.burial_place:
                    f.write("#buri")
                    if person.burial_date:
                        f.write(f" {self._format_date(person.burial_date)}")
                    if person.burial_place:
                        f.write(f" #p {self._escape(person.burial_place)}")
                    f.write("\n")

                f.write("end pevt\n")

    def _get_children(self, family: Family, persons: Dict[str, Person]) -> List[Person]:
        """
        Get children of a family, sorted by birth date.

        Args:
            family: Family object.
            persons: Dictionary of Person objects.

        Returns:
            List of child Person objects.
        """
        children = []

        for child_id in family.children_ids:
            if child_id in persons:
                children.append(persons[child_id])

        # Sort by birth date if available
        def birth_sort_key(person: Person) -> tuple:
            if person.birth_date and person.birth_date.year:
                return (person.birth_date.year, person.birth_date.month or 0, person.birth_date.day or 0)
            return (9999, 0, 0)  # Unknown dates last

        children.sort(key=birth_sort_key)

        return children

    def _format_name_part(self, name: str) -> str:
        """
        Format name part for GeneWeb (replace spaces with underscores).

        Args:
            name: Name string.

        Returns:
            Formatted name.
        """
        if not name:
            return ""

        # Replace spaces with underscores
        return name.replace(" ", "_")

    def _format_date(self, date: Optional[Date]) -> str:
        """
        Format date in GeneWeb format.

        GeneWeb date formats:
        - dd/mm/yyyy (exact date)
        - mm/yyyy (month and year)
        - yyyy (year only)
        - <yyyy (before year)
        - >yyyy (after year)
        - ~yyyy (about year)

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
            parts.append(f"{date.day}")

        # Month
        if date.month:
            parts.append(f"{date.month}")

        # Year
        if date.year:
            parts.append(str(date.year))

        if not parts:
            return ""

        date_str = "/".join(parts)

        # Add precision prefix if needed
        from backend.core.enums import DatePrecision

        if date.precision == DatePrecision.BEFORE:
            return f"<{date_str}"
        elif date.precision == DatePrecision.AFTER:
            return f">{date_str}"
        elif date.precision in (DatePrecision.ABOUT, DatePrecision.CIRCA):
            return f"~{date_str}"

        return date_str

    def _escape(self, text: str) -> str:
        """
        Escape special characters for GeneWeb.

        Args:
            text: Text to escape.

        Returns:
            Escaped text.
        """
        if not text:
            return ""

        # Replace spaces with underscores in place names
        text = text.replace(" ", "_")

        # Remove or replace problematic characters
        text = text.replace("\n", " ").replace("\r", "")

        return text.strip()
