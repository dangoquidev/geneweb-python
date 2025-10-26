"""
GeneWeb to GenEWeb converter.

Converts parsed GeneWeb .gw records into GenEWeb internal models (Person, Family).
"""

import logging
from typing import Dict, List, Optional, Tuple

from backend.core.models import Date, Family, Person, Sex
from backend.parsers.geneweb_parser import GeneWebFamily, GeneWebPerson, GeneWebRecord

logger = logging.getLogger(__name__)


class GeneWebConverter:
    """
    Convert parsed GeneWeb records to GenEWeb models.

    This converter:
    1. Maps GeneWeb persons to GenEWeb Person models
    2. Maps GeneWeb families to GenEWeb Family models
    3. Handles person references and deduplication
    4. Converts dates to GenEWeb Date format
    5. Links family relationships

    Usage:
        converter = GeneWebConverter()
        persons, families = converter.convert(geneweb_record)
    """

    def __init__(self):
        """Initialize converter."""
        self.person_map: Dict[str, Person] = {}
        self.person_counter = 0

    def convert(self, record: GeneWebRecord) -> Tuple[List[Person], List[Family]]:
        """
        Convert GeneWeb record to GenEWeb models.

        Args:
            record: Parsed GeneWeb record.

        Returns:
            Tuple of (persons_list, families_list).

        Examples:
            >>> converter = GeneWebConverter()
            >>> persons, families = converter.convert(record)
            >>> print(f"Converted {len(persons)} persons, {len(families)} families")
        """
        self.person_map = {}
        self.person_counter = 0

        families = []

        logger.info(f"Converting {len(record.families)} families from GeneWeb format")

        # First pass: create all persons and build person map
        for gw_family in record.families:
            # Process father
            if gw_family.father:
                self._get_or_create_person(gw_family.father)

            # Process mother
            if gw_family.mother:
                self._get_or_create_person(gw_family.mother)

            # Process children
            for gw_child in gw_family.children:
                # Inherit surname from father if not specified
                if not gw_child.surname and gw_family.father:
                    gw_child.surname = gw_family.father.surname

                self._get_or_create_person(gw_child)

        # Apply notes and events
        self._apply_notes_and_events(record)

        # Second pass: create families and link relationships
        for gw_family in record.families:
            family = self._convert_family(gw_family)
            if family:
                families.append(family)

        persons = list(self.person_map.values())

        logger.info(f"✅ Converted {len(persons)} persons, {len(families)} families")

        return persons, families

    def _get_or_create_person(self, gw_person: GeneWebPerson) -> Person:
        """
        Get existing person or create new one.

        Args:
            gw_person: GeneWeb person definition.

        Returns:
            GenEWeb Person model.
        """
        key = gw_person.key

        if key in self.person_map:
            # Update existing person with new information
            person = self.person_map[key]
            self._update_person_from_geneweb(person, gw_person)
            return person

        # Create new person
        person = self._convert_person(gw_person)
        self.person_map[key] = person

        return person

    def _convert_person(self, gw_person: GeneWebPerson) -> Person:
        """
        Convert GeneWeb person to GenEWeb Person model.

        Args:
            gw_person: GeneWeb person definition.

        Returns:
            GenEWeb Person model.
        """
        # Determine sex
        sex = Sex.UNKNOWN
        if gw_person.sex == "m":
            sex = Sex.MALE
        elif gw_person.sex == "f":
            sex = Sex.FEMALE

        # Convert dates
        birth_date = self._parse_date(gw_person.birth_date) if gw_person.birth_date else None
        death_date = self._parse_date(gw_person.death_date) if gw_person.death_date else None

        # Create person
        person = Person(
            id=str(self.person_counter),
            first_name=gw_person.first_name.replace("_", " "),
            surname=gw_person.surname.replace("_", " "),
            sex=sex,
            birth_date=birth_date,
            death_date=death_date,
            birth_place=gw_person.birth_place or "",
            death_place=gw_person.death_place or "",
            occupation=gw_person.occupation or "",
        )

        self.person_counter += 1

        # Add source as notes if present
        if gw_person.source:
            person.notes = f"Source: {gw_person.source}"

        # Add notes
        if gw_person.notes:
            notes_text = "\n".join(gw_person.notes)
            if person.notes:
                person.notes += "\n\n" + notes_text
            else:
                person.notes = notes_text

        # Store occurrence number for reference
        person.occurrence = gw_person.occurrence

        logger.debug(f"Created person: {person.first_name} {person.surname} (ID: {person.id})")

        return person

    def _update_person_from_geneweb(self, person: Person, gw_person: GeneWebPerson) -> None:
        """
        Update existing person with additional information from GeneWeb.

        Args:
            person: Existing GenEWeb Person.
            gw_person: GeneWeb person with additional info.
        """
        # Update fields if not already set
        if not person.birth_date and gw_person.birth_date:
            person.birth_date = self._parse_date(gw_person.birth_date)

        if not person.death_date and gw_person.death_date:
            person.death_date = self._parse_date(gw_person.death_date)

        if not person.birth_place and gw_person.birth_place:
            person.birth_place = gw_person.birth_place

        if not person.death_place and gw_person.death_place:
            person.death_place = gw_person.death_place

        if not person.occupation and gw_person.occupation:
            person.occupation = gw_person.occupation

        # Add notes
        if gw_person.notes:
            notes_text = "\n".join(gw_person.notes)
            if person.notes:
                person.notes += "\n\n" + notes_text
            else:
                person.notes = notes_text

        # Update sex if unknown
        if person.sex == Sex.UNKNOWN and gw_person.sex:
            if gw_person.sex == "m":
                person.sex = Sex.MALE
            elif gw_person.sex == "f":
                person.sex = Sex.FEMALE

    def _convert_family(self, gw_family: GeneWebFamily) -> Optional[Family]:
        """
        Convert GeneWeb family to GenEWeb Family model.

        Args:
            gw_family: GeneWeb family definition.

        Returns:
            GenEWeb Family model or None if invalid.
        """
        if not gw_family.father and not gw_family.mother:
            logger.warning("Family has no parents, skipping")
            return None

        # Get parent persons
        father_person = None
        if gw_family.father:
            father_key = gw_family.father.key
            father_person = self.person_map.get(father_key)

        mother_person = None
        if gw_family.mother:
            mother_key = gw_family.mother.key
            mother_person = self.person_map.get(mother_key)

        # Get children
        children_ids = []
        for gw_child in gw_family.children:
            # Inherit surname from father if not specified
            if not gw_child.surname and gw_family.father:
                gw_child.surname = gw_family.father.surname

            child_key = gw_child.key
            child_person = self.person_map.get(child_key)

            if child_person:
                children_ids.append(child_person.id)

        # Convert marriage date
        marriage_date = None
        if gw_family.marriage_date:
            marriage_date = self._parse_date(gw_family.marriage_date)
        elif "marr" in gw_family.events:
            marr_event = gw_family.events["marr"]
            if "date" in marr_event:
                marriage_date = self._parse_date(marr_event["date"])

        # Create family
        family = Family(
            id=str(len(self.person_map) + len(self.person_map)),  # Simple ID
            father_id=father_person.id if father_person else "",
            mother_id=mother_person.id if mother_person else "",
            children_ids=children_ids,
            marriage_date=marriage_date,
            marriage_place=gw_family.marriage_place or "",
        )

        # Add source as notes
        if gw_family.source:
            family.notes = f"Source: {gw_family.source}"

        if gw_family.children_source:
            children_note = f"Children source: {gw_family.children_source}"
            if family.notes:
                family.notes += "\n" + children_note
            else:
                family.notes = children_note

        # Add family notes
        if gw_family.notes:
            notes_text = "\n".join(gw_family.notes)
            if family.notes:
                family.notes += "\n\n" + notes_text
            else:
                family.notes = notes_text

        # Update parent relationships
        if father_person:
            if not father_person.family_ids:
                father_person.family_ids = []
            father_person.family_ids.append(family.id)

        if mother_person:
            if not mother_person.family_ids:
                mother_person.family_ids = []
            mother_person.family_ids.append(family.id)

        # Update children relationships
        for child_id in children_ids:
            # Find child person
            child_person = next((p for p in self.person_map.values() if p.id == child_id), None)
            if child_person:
                child_person.family_id = family.id

        logger.debug(
            f"Created family: {father_person.first_name if father_person else '?'} "
            f"+ {mother_person.first_name if mother_person else '?'} "
            f"({len(children_ids)} children)"
        )

        return family

    def _apply_notes_and_events(self, record: GeneWebRecord) -> None:
        """
        Apply notes and events from record to persons.

        Args:
            record: GeneWeb record with notes and events.
        """
        # Apply person notes
        for person_key, notes in record.person_notes.items():
            if person_key in self.person_map:
                person = self.person_map[person_key]
                notes_text = "\n".join(notes)

                if person.notes:
                    person.notes += "\n\n" + notes_text
                else:
                    person.notes = notes_text

        # Apply person events
        for person_key, events in record.person_events.items():
            if person_key in self.person_map:
                person = self.person_map[person_key]

                # Extract birth/death info from events
                if "birt" in events:
                    birth_event = events["birt"]
                    if "date" in birth_event and not person.birth_date:
                        person.birth_date = self._parse_date(birth_event["date"])
                    if "p" in birth_event and not person.birth_place:
                        person.birth_place = birth_event["p"]

                if "deat" in events:
                    death_event = events["deat"]
                    if "date" in death_event and not person.death_date:
                        person.death_date = self._parse_date(death_event["date"])
                    if "p" in death_event and not person.death_place:
                        person.death_place = death_event["p"]

                # Add other events as notes
                other_events = []
                for event_name, event_data in events.items():
                    if event_name not in ("birt", "deat"):
                        event_str = f"{event_name}"
                        if "date" in event_data:
                            event_str += f": {event_data['date']}"
                        if "p" in event_data:
                            event_str += f" at {event_data['p']}"
                        if "note" in event_data:
                            notes_list = event_data["note"]
                            if isinstance(notes_list, list):
                                event_str += "\n" + "\n".join(notes_list)
                        other_events.append(event_str)

                if other_events:
                    events_text = "\n\nEvents:\n" + "\n".join(other_events)
                    if person.notes:
                        person.notes += events_text
                    else:
                        person.notes = events_text.strip()

    def _parse_date(self, date_str: str) -> Optional[Date]:
        """
        Parse GeneWeb date string to GenEWeb Date model.

        Supports various formats:
        - dd/mm/yyyy
        - yyyy
        - <yyyy (before)
        - >yyyy (after)
        - ~yyyy (about)
        - od (of death marker)

        Args:
            date_str: Date string from GeneWeb.

        Returns:
            GenEWeb Date model or None if invalid.
        """
        if not date_str or date_str == "?":
            return None

        # Handle special markers
        if date_str in ("od", "†"):
            # "of death" marker - no specific date
            return None

        original = date_str
        prefix = ""

        # Extract prefix
        if date_str.startswith("<"):
            prefix = "before"
            date_str = date_str[1:].strip()
        elif date_str.startswith(">"):
            prefix = "after"
            date_str = date_str[1:].strip()
        elif date_str.startswith("~"):
            prefix = "about"
            date_str = date_str[1:].strip()

        # Try to parse date
        day = None
        month = None
        year = None

        # dd/mm/yyyy format
        if "/" in date_str:
            parts = date_str.split("/")

            try:
                if len(parts) >= 1:
                    day = int(parts[0])
                if len(parts) >= 2:
                    month = int(parts[1])
                if len(parts) >= 3:
                    year_str = parts[2]
                    # Handle 2-digit years
                    year = int(year_str)
                    if year < 100:
                        # Assume 1900s for < 100
                        year += 1900
            except ValueError:
                logger.warning(f"Failed to parse date: {original}")
                return None

        # yyyy format
        elif date_str.isdigit():
            try:
                year = int(date_str)
            except ValueError:
                logger.warning(f"Failed to parse year: {original}")
                return None

        else:
            logger.warning(f"Unsupported date format: {original}")
            return None

        # Create Date model
        try:
            date = Date(
                day=day,
                month=month,
                year=year,
                calendar="gregorian",
            )

            # Add prefix as note if present
            if prefix:
                date.text = f"{prefix} {date_str}"

            return date

        except Exception as e:
            logger.warning(f"Failed to create Date object from {original}: {e}")
            return None
