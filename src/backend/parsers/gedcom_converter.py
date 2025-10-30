"""
GEDCOM to GenEWeb model converter.

Converts parsed GEDCOM records to GenEWeb Person and Family models.
Handles date parsing, name parsing, event conversion, and relationship mapping.
"""

import logging
import re
from typing import Dict, List, Optional, Tuple

from backend.core.models import Date, Event, Family, Person, Sex
from backend.parsers.gedcom_parser import GedcomRecord, GedcomTag

logger = logging.getLogger(__name__)


class GedcomConverter:
    """
    Convert GEDCOM records to GenEWeb models.

    Handles:
    - Individual (INDI) → Person
    - Family (FAM) → Family
    - Dates (various GEDCOM formats)
    - Names (GIVN, SURN, NAME)
    - Events (BIRT, DEAT, MARR, etc.)
    - Relationships (FAMC, FAMS, HUSB, WIFE, CHIL)

    Usage:
        converter = GedcomConverter()
        persons, families = converter.convert(gedcom_records)
    """

    def __init__(self, lenient: bool = True):
        """
        Initialize converter.

        Args:
            lenient: If True, ignore non-critical errors and use defaults.
                    If False, raise exceptions on errors.
        """
        self.lenient = lenient
        self.warnings: List[str] = []
        self.errors: List[str] = []

    def convert(self, records: List[GedcomRecord]) -> Tuple[Dict[str, Person], Dict[str, Family]]:
        """
        Convert GEDCOM records to GenEWeb models.

        Args:
            records: List of parsed GEDCOM records.

        Returns:
            Tuple of (persons_dict, families_dict).
            Keys are xref_ids (e.g., "@I1@", "@F1@").

        Raises:
            ValueError: If not lenient and critical errors occur.

        Examples:
            >>> converter = GedcomConverter()
            >>> persons, families = converter.convert(records)
            >>> print(f"Converted {len(persons)} persons, {len(families)} families")
        """
        persons: Dict[str, Person] = {}
        families: Dict[str, Family] = {}

        # First pass: Create all Person and Family objects
        for record in records:
            if record.tag == GedcomTag.INDI and record.xref_id:
                try:
                    person = self._convert_individual(record)
                    persons[record.xref_id] = person
                except Exception as e:
                    error_msg = f"Error converting individual {record.xref_id}: {e}"
                    self.errors.append(error_msg)
                    if not self.lenient:
                        raise ValueError(error_msg) from e
                    logger.warning(error_msg)

            elif record.tag == GedcomTag.FAM and record.xref_id:
                try:
                    family = self._convert_family(record)
                    families[record.xref_id] = family
                except Exception as e:
                    error_msg = f"Error converting family {record.xref_id}: {e}"
                    self.errors.append(error_msg)
                    if not self.lenient:
                        raise ValueError(error_msg) from e
                    logger.warning(error_msg)

        # Second pass: Link family relationships
        self._link_relationships(persons, families, records)

        logger.info(
            f"Converted {len(persons)} persons, {len(families)} families "
            f"({len(self.warnings)} warnings, {len(self.errors)} errors)"
        )

        return persons, families

    def _convert_individual(self, record: GedcomRecord) -> Person:
        """
        Convert GEDCOM INDI record to Person model.

        Args:
            record: GEDCOM INDI record.

        Returns:
            Person instance.

        Raises:
            ValueError: If required fields are missing and not lenient.
        """
        person_id = self._clean_xref_id(record.xref_id)

        # Parse name
        name_record = record.get_child(GedcomTag.NAME)
        first_name, last_name, public_name = self._parse_name(name_record)

        # Parse sex
        sex_value = record.get_value_or_default(GedcomTag.SEX, "U")
        sex = self._parse_sex(sex_value)

        # Parse birth
        birth_date, birth_place = None, None
        birth_record = record.get_child(GedcomTag.BIRT)
        if birth_record:
            birth_date = self._parse_date(birth_record.get_child(GedcomTag.DATE))
            birth_place = birth_record.get_value_or_default(GedcomTag.PLAC)

        # Parse death
        death_date, death_place = None, None
        death_record = record.get_child(GedcomTag.DEAT)
        if death_record:
            death_date = self._parse_date(death_record.get_child(GedcomTag.DATE))
            death_place = death_record.get_value_or_default(GedcomTag.PLAC)

        # Parse baptism
        baptism_date, baptism_place = None, None
        baptism_record = record.get_child(GedcomTag.BAPM) or record.get_child(GedcomTag.CHR)
        if baptism_record:
            baptism_date = self._parse_date(baptism_record.get_child(GedcomTag.DATE))
            baptism_place = baptism_record.get_value_or_default(GedcomTag.PLAC)

        # Parse burial
        burial_date, burial_place = None, None
        burial_record = record.get_child(GedcomTag.BURI)
        if burial_record:
            burial_date = self._parse_date(burial_record.get_child(GedcomTag.DATE))
            burial_place = burial_record.get_value_or_default(GedcomTag.PLAC)

        # Parse occupation
        occupation = record.get_value_or_default(GedcomTag.OCCU)

        # Parse notes (combine into single string)
        notes_text = self._parse_notes_as_text(record)

        # Create Person
        person = Person(
            id=person_id,
            first_name=first_name,
            surname=last_name,  # surname, not last_name
            public_name=public_name,
            sex=sex,
            birth_date=birth_date,
            birth_place=birth_place,
            death_date=death_date,
            death_place=death_place,
            baptism_date=baptism_date,
            baptism_place=baptism_place,
            burial_date=burial_date,
            burial_place=burial_place,
            occupation=occupation,
            notes=notes_text,  # Single string, not list
        )

        # Parse additional events
        for event_record in record.get_children(GedcomTag.EVEN):
            event = self._parse_event(event_record)
            if event:
                person.add_event(event)

        # Parse residence events
        for resi_record in record.get_children(GedcomTag.RESI):
            event = self._parse_event(resi_record, event_type="Residence")
            if event:
                person.add_event(event)

        return person

    def _convert_family(self, record: GedcomRecord) -> Family:
        """
        Convert GEDCOM FAM record to Family model.

        Args:
            record: GEDCOM FAM record.

        Returns:
            Family instance.
        """
        family_id = self._clean_xref_id(record.xref_id)

        # Parse marriage
        marriage_date, marriage_place = None, None
        marriage_record = record.get_child(GedcomTag.MARR)
        if marriage_record:
            marriage_date = self._parse_date(marriage_record.get_child(GedcomTag.DATE))
            marriage_place = marriage_record.get_value_or_default(GedcomTag.PLAC)

        # Parse divorce
        divorce_date = None
        divorce_record = record.get_child(GedcomTag.DIV)
        if divorce_record:
            divorce_date = self._parse_date(divorce_record.get_child(GedcomTag.DATE))

        # Parse notes (combine into single string)
        notes_text = self._parse_notes_as_text(record)

        # Create Family (relationships will be linked in second pass)
        family = Family(
            id=family_id,
            marriage_date=marriage_date,
            marriage_place=marriage_place,
            divorce_date=divorce_date,
            notes=notes_text,  # Single string, not list
        )

        return family

    def _link_relationships(
        self,
        persons: Dict[str, Person],
        families: Dict[str, Family],
        records: List[GedcomRecord],
    ) -> None:
        """
        Link family relationships (parents, spouses, children).

        Args:
            persons: Dictionary of Person objects.
            families: Dictionary of Family objects.
            records: Original GEDCOM records for relationship data.
        """
        # Process each individual for family relationships
        for record in records:
            if record.tag != GedcomTag.INDI or not record.xref_id:
                continue

            person_id = self._clean_xref_id(record.xref_id)
            person = persons.get(person_id)

            if not person:
                continue

            # FAMC - Family as child (parent families)
            for famc_record in record.get_children(GedcomTag.FAMC):
                if famc_record.value:
                    family_id = self._clean_xref_id(famc_record.value)
                    family = families.get(family_id)
                    if family:
                        family.add_child(person_id)
                        # Link to parent family
                        person.family_id = family_id

            # FAMS - Family as spouse (spouse families)
            for fams_record in record.get_children(GedcomTag.FAMS):
                if fams_record.value:
                    family_id = self._clean_xref_id(fams_record.value)
                    person.family_ids.append(family_id)

        # Process each family for spouse relationships
        for record in records:
            if record.tag != GedcomTag.FAM or not record.xref_id:
                continue

            family_id = self._clean_xref_id(record.xref_id)
            family = families.get(family_id)

            if not family:
                continue

            # HUSB - Husband
            husb_record = record.get_child(GedcomTag.HUSB)
            if husb_record and husb_record.value:
                father_id = self._clean_xref_id(husb_record.value)
                family.father_id = father_id

            # WIFE - Wife
            wife_record = record.get_child(GedcomTag.WIFE)
            if wife_record and wife_record.value:
                mother_id = self._clean_xref_id(wife_record.value)
                family.mother_id = mother_id

            # CHIL - Children (already processed in FAMC loop, but verify)
            for chil_record in record.get_children(GedcomTag.CHIL):
                if chil_record.value:
                    child_id = self._clean_xref_id(chil_record.value)
                    if child_id not in family.children_ids:
                        family.add_child(child_id)

    def _parse_name(self, name_record: Optional[GedcomRecord]) -> Tuple[str, str, Optional[str]]:
        """
        Parse GEDCOM NAME field.

        GEDCOM name format: "Given Name /Surname/ Suffix"
        Surname is enclosed in slashes.

        Args:
            name_record: NAME record.

        Returns:
            Tuple of (first_name, last_name, public_name).

        Examples:
            >>> self._parse_name(name_record)  # "John /Doe/"
            ("John", "Doe", None)

            >>> self._parse_name(name_record)  # "Marie Anne /Dupont-Martin/"
            ("Marie Anne", "Dupont-Martin", None)
        """
        if not name_record or not name_record.value:
            return ("Unknown", "", None)

        name_value = name_record.get_concatenated_value()

        # Parse name: "Given /Surname/"
        match = re.match(r"^([^/]*)/([^/]*)/?(.*)$", name_value)
        if match:
            given = match.group(1).strip()
            surname = match.group(2).strip()
            suffix = match.group(3).strip()

            # Check for explicit GIVN and SURN tags
            givn_record = name_record.get_child("GIVN")
            if givn_record and givn_record.value:
                given = givn_record.value.strip()

            surn_record = name_record.get_child("SURN")
            if surn_record and surn_record.value:
                surname = surn_record.value.strip()

            first_name = given or "Unknown"
            last_name = surname or ""

            # Public name includes suffix if present
            public_name = None
            if suffix:
                public_name = f"{given} {surname} {suffix}".strip()

            return (first_name, last_name, public_name)

        # Fallback: no slashes, treat whole value as first name
        return (name_value.strip() or "Unknown", "", None)

    def _parse_sex(self, sex_value: str) -> Sex:
        """
        Parse GEDCOM SEX field.

        Args:
            sex_value: SEX value ("M", "F", "U", etc.).

        Returns:
            Sex enum value.
        """
        sex_value = sex_value.strip().upper()

        if sex_value in ("M", "MALE"):
            return Sex.MALE
        elif sex_value in ("F", "FEMALE"):
            return Sex.FEMALE
        else:
            return Sex.UNKNOWN

    def _parse_date(self, date_record: Optional[GedcomRecord]) -> Optional[Date]:
        """
        Parse GEDCOM DATE field.

        Supports various GEDCOM date formats:
        - "DD MMM YYYY" (e.g., "12 JAN 1980")
        - "MMM YYYY" (e.g., "JAN 1980")
        - "YYYY" (e.g., "1980")
        - "ABT 1980" (about)
        - "BEF 1980" (before)
        - "AFT 1980" (after)
        - "BET 1980 AND 1985" (between)

        Args:
            date_record: DATE record.

        Returns:
            Date instance or None.

        Examples:
            >>> self._parse_date(date_record)  # "12 JAN 1980"
            Date(day=12, month=1, year=1980)

            >>> self._parse_date(date_record)  # "ABT 1980"
            Date(year=1980, precision="about")
        """
        if not date_record or not date_record.value:
            return None

        date_value = date_record.get_concatenated_value().strip()

        # Remove leading/trailing whitespace
        date_value = date_value.strip()

        # Handle qualifiers
        precision = None
        if date_value.startswith("ABT "):
            precision = "about"
            date_value = date_value[4:]
        elif date_value.startswith("BEF "):
            precision = "before"
            date_value = date_value[4:]
        elif date_value.startswith("AFT "):
            precision = "after"
            date_value = date_value[4:]
        elif "BET " in date_value and " AND " in date_value:
            # BET 1980 AND 1985 - use first date
            match = re.match(r"BET\s+(.+?)\s+AND\s+(.+)", date_value)
            if match:
                date_value = match.group(1)
                precision = "about"

        # Parse date components
        month_map = {
            "JAN": 1,
            "FEB": 2,
            "MAR": 3,
            "APR": 4,
            "MAY": 5,
            "JUN": 6,
            "JUL": 7,
            "AUG": 8,
            "SEP": 9,
            "OCT": 10,
            "NOV": 11,
            "DEC": 12,
        }

        # Try DD MMM YYYY
        match = re.match(r"(\d{1,2})\s+([A-Z]{3})\s+(\d{4})", date_value)
        if match:
            day = int(match.group(1))
            month = month_map.get(match.group(2))
            year = int(match.group(3))
            return Date(day=day, month=month, year=year, precision=precision)

        # Try MMM YYYY
        match = re.match(r"([A-Z]{3})\s+(\d{4})", date_value)
        if match:
            month = month_map.get(match.group(1))
            year = int(match.group(2))
            return Date(month=month, year=year, precision=precision)

        # Try YYYY
        match = re.match(r"(\d{4})", date_value)
        if match:
            year = int(match.group(1))
            return Date(year=year, precision=precision)

        # Couldn't parse
        warning = f"Could not parse date: {date_value}"
        self.warnings.append(warning)
        logger.warning(warning)
        return None

    def _parse_event(self, event_record: GedcomRecord, event_type: Optional[str] = None) -> Optional[Event]:
        """
        Parse GEDCOM event record.

        Args:
            event_record: Event record (EVEN, RESI, etc.).
            event_type: Event type (if not specified in record).

        Returns:
            Event instance or None.
        """
        # Get event type
        if not event_type:
            type_record = event_record.get_child(GedcomTag.TYPE)
            event_type = type_record.value if type_record and type_record.value else "Event"

        # Get date
        date = self._parse_date(event_record.get_child(GedcomTag.DATE))

        # Get place
        place = event_record.get_value_or_default(GedcomTag.PLAC)

        # Get note
        note = event_record.get_value_or_default(GedcomTag.NOTE)

        return Event(event_type=event_type, date=date, place=place, note=note)

    def _parse_notes_as_text(self, record: GedcomRecord) -> Optional[str]:
        """
        Parse all NOTE records and combine into single string.

        Args:
            record: Parent record.

        Returns:
            Combined notes text or None.
        """
        notes_parts = []

        for note_record in record.get_children(GedcomTag.NOTE):
            text = note_record.get_concatenated_value()
            if text:
                notes_parts.append(text)

        return "\n\n".join(notes_parts) if notes_parts else None

    @staticmethod
    def _clean_xref_id(xref_id: Optional[str]) -> str:
        """
        Clean GEDCOM cross-reference ID.

        Removes @ symbols: "@I1@" → "I1"

        Args:
            xref_id: Cross-reference ID.

        Returns:
            Cleaned ID.
        """
        if not xref_id:
            return ""

        return xref_id.strip("@")
