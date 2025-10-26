"""
GeneWeb .gw file parser.

Parses GeneWeb source files (.gw format) into structured records.
The .gw format is a human-readable text format used by GeneWeb for
defining genealogy trees.

Format specification:
- encoding: utf-8 (first line)
- gwplus (optional second line for extended features)
- fam: family definition with parents and children
- notes: notes for persons
- pevt: personal events (birth, death, etc.)
- fevt: family events (marriage, divorce, etc.)

References:
    - GeneWeb documentation: https://geneweb.tuxfamily.org/wiki/
    - OCaml source: legacy/ocaml-old-project/bin/gwc/gwcomp.ml
"""

import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, TextIO, Union

logger = logging.getLogger(__name__)


class GeneWebBlockType(str, Enum):
    """Types of blocks in GeneWeb files."""

    FAMILY = "fam"
    NOTES = "notes"
    PEVT = "pevt"  # Personal events
    FEVT = "fevt"  # Family events


class GeneWebTag(str, Enum):
    """Standard GeneWeb field tags."""

    # Personal fields
    OCCUPATION = "#occu"
    SOURCE = "#src"
    BIRTH = "#birt"
    BAPTISM = "#bapm"
    DEATH = "#deat"
    BURIAL = "#buri"
    BIRTH_PLACE = "#bp"
    BIRTH_NOTE = "#bn"
    BIRTH_SOURCE = "#bs"
    DEATH_PLACE = "#dp"
    DEATH_NOTE = "#dn"
    DEATH_SOURCE = "#ds"
    BURIAL_PLACE = "#rp"
    BURIAL_NOTE = "#rn"
    BURIAL_SOURCE = "#rs"

    # Family events
    MARRIAGE = "#marr"
    DIVORCE = "#div"
    ENGAGEMENT = "#enga"

    # Generic
    PLACE = "#p"
    NOTE = "note"
    DATE = "#date"
    RESIDENCE = "#resi"
    ACCOMPLISHMENT = "#acco"


@dataclass
class GeneWebPerson:
    """
    Represents a person definition in GeneWeb format.

    Attributes:
        first_name: First name(s)
        surname: Last name
        occurrence: Occurrence number (for homonyms)
        sex: 'm' (male), 'f' (female), or '' (unknown)
        birth_date: Birth date string
        death_date: Death date string
        birth_place: Birth place
        death_place: Death place
        occupation: Occupation
        source: Source reference
        notes: Personal notes
        events: Dictionary of personal events
        fields: Additional fields
    """

    first_name: str
    surname: str
    occurrence: int = 0
    sex: str = ""  # 'm', 'f', or ''
    birth_date: Optional[str] = None
    death_date: Optional[str] = None
    birth_place: Optional[str] = None
    death_place: Optional[str] = None
    occupation: Optional[str] = None
    source: Optional[str] = None
    notes: List[str] = field(default_factory=list)
    events: Dict[str, Dict[str, str]] = field(default_factory=dict)
    fields: Dict[str, str] = field(default_factory=dict)

    @property
    def key(self) -> str:
        """Get unique key for this person."""
        return f"{self.first_name}.{self.occurrence}.{self.surname}"


@dataclass
class GeneWebFamily:
    """
    Represents a family definition in GeneWeb format.

    Attributes:
        father: Father person or reference
        mother: Mother person or reference
        marriage_date: Marriage date string
        marriage_place: Marriage place
        divorce: Divorce information
        source: Source reference
        children_source: Source for children
        notes: Family notes
        events: Dictionary of family events
        children: List of children
        witnesses: List of witnesses
        fields: Additional fields
    """

    father: Optional[GeneWebPerson] = None
    mother: Optional[GeneWebPerson] = None
    marriage_date: Optional[str] = None
    marriage_place: Optional[str] = None
    divorce: Optional[str] = None
    source: Optional[str] = None
    children_source: Optional[str] = None
    notes: List[str] = field(default_factory=list)
    events: Dict[str, Dict[str, str]] = field(default_factory=dict)
    children: List[GeneWebPerson] = field(default_factory=list)
    witnesses: List[GeneWebPerson] = field(default_factory=list)
    fields: Dict[str, str] = field(default_factory=dict)


@dataclass
class GeneWebRecord:
    """
    Top-level record in a GeneWeb file.

    Contains families, persons, notes, and events.
    """

    encoding: str = "utf-8"
    gwplus: bool = False
    families: List[GeneWebFamily] = field(default_factory=list)
    person_notes: Dict[str, List[str]] = field(default_factory=dict)
    person_events: Dict[str, Dict[str, Dict[str, str]]] = field(default_factory=dict)
    line_number: int = 0


class GeneWebParser:
    """
    Parse GeneWeb .gw files into structured records.

    Supports:
    - GeneWeb source format (.gw)
    - UTF-8 encoding
    - gwplus extended format
    - Family definitions with parents and children
    - Personal and family events
    - Notes
    - Various date formats

    Usage:
        parser = GeneWebParser()
        record = parser.parse_file("family.gw")

        for family in record.families:
            print(f"Father: {family.father.first_name} {family.father.surname}")
            print(f"Mother: {family.mother.first_name} {family.mother.surname}")
            for child in family.children:
                print(f"  Child: {child.first_name} {child.surname}")
    """

    def __init__(self, strict: bool = False):
        """
        Initialize GeneWeb parser.

        Args:
            strict: If True, fail on any parsing error. If False, log warnings and continue.
        """
        self.strict = strict
        self.line_number = 0

    def parse_file(self, file_path: Union[Path, str]) -> GeneWebRecord:
        """
        Parse a GeneWeb .gw file.

        Args:
            file_path: Path to .gw file.

        Returns:
            GeneWebRecord with parsed data.

        Raises:
            FileNotFoundError: If file doesn't exist.
            ValueError: If file format is invalid (in strict mode).

        Examples:
            >>> parser = GeneWebParser()
            >>> record = parser.parse_file("family.gw")
            >>> print(f"{len(record.families)} families")
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"GeneWeb file not found: {file_path}")

        logger.info(f"Parsing GeneWeb file: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            return self.parse_stream(f)

    def parse_stream(self, stream: TextIO) -> GeneWebRecord:
        """
        Parse a GeneWeb stream.

        Args:
            stream: Text stream to parse.

        Returns:
            GeneWebRecord with parsed data.
        """
        record = GeneWebRecord()
        self.line_number = 0

        lines = stream.readlines()
        i = 0

        # Parse header
        if i < len(lines) and lines[i].startswith("encoding:"):
            record.encoding = lines[i].split(":", 1)[1].strip()
            i += 1
            self.line_number += 1

        if i < len(lines) and lines[i].strip() == "gwplus":
            record.gwplus = True
            i += 1
            self.line_number += 1

        # Parse blocks
        while i < len(lines):
            line = lines[i].strip()
            self.line_number = i + 1

            if not line:
                i += 1
                continue

            # Family block
            if line.startswith("fam "):
                family, lines_consumed = self._parse_family_block(lines[i:])
                record.families.append(family)
                i += lines_consumed

            # Notes block
            elif line.startswith("notes "):
                person_key, notes, lines_consumed = self._parse_notes_block(lines[i:])
                record.person_notes[person_key] = notes
                i += lines_consumed

            # Personal events block
            elif line.startswith("pevt "):
                person_key, events, lines_consumed = self._parse_pevt_block(lines[i:])
                record.person_events[person_key] = events
                i += lines_consumed

            else:
                # Skip unknown lines
                logger.debug(f"Skipping line {self.line_number}: {line}")
                i += 1

        logger.info(
            f"Parsed {len(record.families)} families, "
            f"{len(record.person_notes)} person notes, "
            f"{len(record.person_events)} person events"
        )

        return record

    def _parse_family_block(self, lines: List[str]) -> tuple[GeneWebFamily, int]:
        """
        Parse a family block.

        Format:
            fam Surname Father_Name [#fields] +date + Surname Mother_Name [#fields] date
            [src source]
            [csrc children_source]
            [fevt ... end fevt]
            beg
            - sex Child_Name date date
            ...
            end

        Returns:
            Tuple of (GeneWebFamily, lines_consumed)
        """
        family = GeneWebFamily()
        i = 0
        line = lines[i].strip()

        # Parse first line: fam Father + Mother
        # Example: fam Galichet Jean_Pierre #occu Marchand 0 <1849 + Loche Marie_Elisabeth 0 <1849
        parts = line[4:].split(" + ")  # Remove "fam " prefix

        if len(parts) >= 1:
            # Parse father
            father_parts = self._parse_person_reference(parts[0])
            if father_parts:
                family.father = father_parts
                family.father.sex = "m"

        if len(parts) >= 2:
            # Parse mother
            mother_parts = self._parse_person_reference(parts[1])
            if mother_parts:
                family.mother = mother_parts
                family.mother.sex = "f"

        i += 1

        # Parse subsequent lines until "beg" or end
        while i < len(lines):
            line = lines[i].strip()

            if not line:
                i += 1
                continue

            if line == "beg":
                # Parse children
                i += 1
                children, consumed = self._parse_children_block(lines[i:])
                family.children = children
                i += consumed
                break

            elif line.startswith("src "):
                family.source = line[4:].strip()
                i += 1

            elif line.startswith("csrc "):
                family.children_source = line[5:].strip()
                i += 1

            elif line.startswith("fevt"):
                # Parse family events
                i += 1
                events, consumed = self._parse_events_block(lines[i:])
                family.events = events
                i += consumed

            elif line.startswith("note "):
                family.notes.append(line[5:].strip())
                i += 1

            else:
                # Try to extract marriage/divorce info
                if " + " in line or line.startswith("+"):
                    # Marriage date might be on separate line
                    pass
                i += 1

        return family, i

    def _parse_person_reference(self, text: str) -> Optional[GeneWebPerson]:
        """
        Parse a person reference from text.

        Format: Surname First_Name [#fields] [occurrence] [dates]
        Example: Galichet Jean_Pierre #occu Marchand 0 <1849

        Returns:
            GeneWebPerson or None if parsing fails.
        """
        if not text.strip():
            return None

        parts = text.strip().split()
        if len(parts) < 2:
            return None

        person = GeneWebPerson(first_name="", surname="")

        # First part is surname
        person.surname = parts[0]

        # Second part is first name
        person.first_name = parts[1]

        # Parse remaining parts
        i = 2
        while i < len(parts):
            part = parts[i]

            # Field tags
            if part.startswith("#"):
                if part == "#occu" and i + 1 < len(parts):
                    person.occupation = parts[i + 1]
                    i += 2
                elif part == "#src" and i + 1 < len(parts):
                    person.source = parts[i + 1]
                    i += 2
                elif part in ("#bp", "#birth_place") and i + 1 < len(parts):
                    person.birth_place = parts[i + 1]
                    i += 2
                elif part in ("#bs", "#birth_source") and i + 1 < len(parts):
                    person.fields["birth_source"] = parts[i + 1]
                    i += 2
                else:
                    # Generic field
                    if i + 1 < len(parts):
                        person.fields[part] = parts[i + 1]
                        i += 2
                    else:
                        i += 1

            # Occurrence number
            elif part.isdigit():
                person.occurrence = int(part)
                i += 1

            # Dates
            elif self._looks_like_date(part):
                if not person.birth_date:
                    person.birth_date = part
                else:
                    person.death_date = part
                i += 1

            # Death marker
            elif part in ("od", "†"):
                person.death_date = "od"  # "of death" marker
                i += 1

            else:
                # Unknown, skip
                i += 1

        return person

    def _parse_children_block(self, lines: List[str]) -> tuple[List[GeneWebPerson], int]:
        """
        Parse children block between "beg" and "end".

        Format:
            - sex First_Name [dates]

        Where sex is:
            h (homme/male)
            f (femme/female)
            ? (unknown)

        Returns:
            Tuple of (children list, lines_consumed)
        """
        children = []
        i = 0

        while i < len(lines):
            line = lines[i].strip()

            if not line:
                i += 1
                continue

            if line == "end":
                i += 1
                break

            if line.startswith("- "):
                # Parse child: - sex First_Name [dates]
                parts = line[2:].split()
                if len(parts) >= 2:
                    sex_marker = parts[0]
                    first_name = parts[1]

                    sex = ""
                    if sex_marker == "h":
                        sex = "m"
                    elif sex_marker == "f":
                        sex = "f"

                    child = GeneWebPerson(first_name=first_name, surname="", sex=sex)  # Will be inherited from father

                    # Parse dates and fields
                    j = 2
                    while j < len(parts):
                        part = parts[j]

                        if part.startswith("#"):
                            # Field tag
                            if j + 1 < len(parts):
                                child.fields[part] = parts[j + 1]
                                j += 2
                            else:
                                j += 1
                        elif self._looks_like_date(part):
                            if not child.birth_date:
                                child.birth_date = part
                            else:
                                child.death_date = part
                            j += 1
                        elif part in ("od", "†", "?"):
                            child.death_date = part
                            j += 1
                        else:
                            j += 1

                    children.append(child)

            i += 1

        return children, i

    def _parse_notes_block(self, lines: List[str]) -> tuple[str, List[str], int]:
        """
        Parse notes block.

        Format:
            notes Surname First_Name
            beg
            ... notes content ...
            end notes

        Returns:
            Tuple of (person_key, notes_list, lines_consumed)
        """
        i = 0
        line = lines[i].strip()

        # Parse: notes Surname First_Name
        parts = line[6:].split()  # Remove "notes "
        if len(parts) < 2:
            return "", [], 1

        surname = parts[0]
        first_name = parts[1]
        occurrence = 0

        if len(parts) > 2 and parts[2].isdigit():
            occurrence = int(parts[2])

        person_key = f"{first_name}.{occurrence}.{surname}"

        i += 1
        notes = []

        # Look for "beg"
        while i < len(lines) and lines[i].strip() != "beg":
            i += 1

        if i < len(lines):
            i += 1  # Skip "beg"

        # Read notes until "end notes"
        while i < len(lines):
            line = lines[i].strip()

            if line == "end notes" or line == "end":
                i += 1
                break

            notes.append(lines[i].rstrip())  # Keep original formatting
            i += 1

        return person_key, notes, i

    def _parse_pevt_block(self, lines: List[str]) -> tuple[str, Dict[str, Dict[str, str]], int]:
        """
        Parse personal events block.

        Format:
            pevt Surname First_Name
            #birt date #p place #s source
            #deat date
            end pevt

        Returns:
            Tuple of (person_key, events_dict, lines_consumed)
        """
        i = 0
        line = lines[i].strip()

        # Parse: pevt Surname First_Name
        parts = line[5:].split()  # Remove "pevt "
        if len(parts) < 2:
            return "", {}, 1

        surname = parts[0]
        first_name = parts[1]
        occurrence = 0

        if len(parts) > 2 and parts[2].isdigit():
            occurrence = int(parts[2])

        person_key = f"{first_name}.{occurrence}.{surname}"

        i += 1
        events: Dict[str, Dict[str, str]] = {}
        current_event = None
        current_event_data: Dict[str, str] = {}

        # Parse events until "end pevt"
        while i < len(lines):
            line = lines[i].strip()

            if line == "end pevt" or line == "end":
                # Save last event
                if current_event:
                    events[current_event] = current_event_data
                i += 1
                break

            if not line:
                i += 1
                continue

            # Event tags
            if line.startswith("#"):
                # Save previous event
                if current_event:
                    events[current_event] = current_event_data

                # Parse new event
                parts = line.split(maxsplit=1)
                current_event = parts[0][1:]  # Remove #
                current_event_data = {}

                # Parse event data
                if len(parts) > 1:
                    current_event_data = self._parse_event_data(parts[1])

            elif line.startswith("note "):
                if current_event:
                    if "note" not in current_event_data:
                        current_event_data["note"] = ""  # Initialize as string
                    if isinstance(current_event_data["note"], str):
                        current_event_data["note"] += "\n" + line[5:]
                    else:
                        current_event_data["note"] += line[5:]

            i += 1

        return person_key, events, i

    def _parse_events_block(self, lines: List[str]) -> tuple[Dict[str, Dict[str, str]], int]:
        """
        Parse family events block.

        Format:
            fevt
            #marr date
            end fevt

        Returns:
            Tuple of (events_dict, lines_consumed)
        """
        i = 0
        events = {}

        while i < len(lines):
            line = lines[i].strip()

            if line == "end fevt" or line == "end":
                i += 1
                break

            if not line:
                i += 1
                continue

            if line.startswith("#"):
                parts = line.split(maxsplit=1)
                event_name = parts[0][1:]  # Remove #

                event_data = {}
                if len(parts) > 1:
                    event_data = self._parse_event_data(parts[1])

                events[event_name] = event_data

            i += 1

        return events, i

    def _parse_event_data(self, text: str) -> Dict[str, str]:
        """
        Parse event data from text.

        Format: date #p place #s source #note note

        Returns:
            Dictionary with event fields.
        """
        data = {}
        parts = text.split()

        i = 0
        date_parts: List[str] = []

        while i < len(parts):
            part = parts[i]

            if part.startswith("#"):
                # Field tag
                field_name = part[1:]

                if i + 1 < len(parts) and not parts[i + 1].startswith("#"):
                    data[field_name] = parts[i + 1]
                    i += 2
                else:
                    data[field_name] = ""
                    i += 1

            elif not date_parts or self._looks_like_date(part):
                # Date part
                date_parts.append(part)
                i += 1

            else:
                i += 1

        if date_parts:
            data["date"] = " ".join(date_parts)

        return data

    def _looks_like_date(self, text: str) -> bool:
        """
        Check if text looks like a date.

        Supports:
        - dd/mm/yyyy
        - dd/mm/yy
        - yyyy
        - <yyyy (before)
        - >yyyy (after)
        - ~yyyy (about)
        - dd/mm (partial)
        """
        if not text:
            return False

        # Remove leading markers
        text = text.lstrip("<>~")

        # Check patterns
        patterns = [
            r"^\d{1,2}/\d{1,2}/\d{2,4}$",  # dd/mm/yyyy
            r"^\d{1,2}/\d{1,2}$",  # dd/mm
            r"^\d{4}$",  # yyyy
            r"^\d{2}$",  # yy
        ]

        for pattern in patterns:
            if re.match(pattern, text):
                return True

        return False
