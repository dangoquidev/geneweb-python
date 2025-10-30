"""
Person service - Business logic for person management.

This service provides high-level operations for creating, updating, and managing
persons with validation, duplicate detection, and family relationship handling.
"""

import uuid
from typing import Any, Dict, List, Optional

from backend.core.exceptions import ValidationError
from backend.core.models import Date, Event, Person, Sex
from backend.database.repository import Repository
from backend.utils.string_utils import capitalize_name, fuzzy_match, normalize_string


class PersonService:
    """
    Service for managing persons with business logic.

    This service encapsulates all business rules for person management,
    including validation, duplicate detection, and family relationship handling.

    Args:
        repository: Repository instance for data access.

    Examples:
        >>> repo = Repository(driver)
        >>> service = PersonService(repo)
        >>> person = service.create_person(
        ...     first_name="John",
        ...     surname="Doe",
        ...     sex=Sex.MALE
        ... )
    """

    def __init__(self, repository: Repository) -> None:
        """
        Initialize person service.

        Args:
            repository: Repository instance for data access.
        """
        self.repository = repository

    def create_person(
        self,
        first_name: str,
        surname: str,
        sex: Sex = Sex.UNKNOWN,
        birth_date: Optional[Date] = None,
        birth_place: Optional[str] = None,
        death_date: Optional[Date] = None,
        death_place: Optional[str] = None,
        check_duplicates: bool = True,
        **kwargs: Any,
    ) -> Person:
        """
        Create a new person with validation and duplicate detection.

        Args:
            first_name: Person's first name (required).
            surname: Person's surname/last name (required).
            sex: Person's sex (default: UNKNOWN).
            birth_date: Birth date if known.
            birth_place: Birth place if known.
            death_date: Death date if known.
            death_place: Death place if known.
            check_duplicates: Whether to check for potential duplicates.
            **kwargs: Additional person attributes.

        Returns:
            Created Person instance.

        Raises:
            ValidationError: If validation fails or duplicate detected.
            DatabaseError: If database operation fails.

        Examples:
            >>> person = service.create_person(
            ...     first_name="Marie",
            ...     surname="Curie",
            ...     sex=Sex.FEMALE,
            ...     birth_date=Date(year=1867, month=11, day=7)
            ... )
        """
        # Validate required fields
        if not first_name or not first_name.strip():
            raise ValidationError("first_name", "First name is required")
        if not surname or not surname.strip():
            raise ValidationError("surname", "Surname is required")

        # Capitalize names properly
        first_name = capitalize_name(first_name.strip())
        surname = capitalize_name(surname.strip())

        # Check for duplicates if requested
        if check_duplicates:
            duplicates = self.find_potential_duplicates(
                first_name=first_name,
                surname=surname,
                birth_date=birth_date,
            )
            if duplicates:
                raise ValidationError(
                    "duplicate",
                    f"Found {len(duplicates)} potential duplicate(s). " f"Set check_duplicates=False to create anyway.",
                )

        # Validate dates consistency
        if birth_date and death_date:
            self._validate_date_sequence(birth_date, death_date, "birth", "death")

        # Create person
        person_id = str(uuid.uuid4())
        person = Person(
            id=person_id,
            first_name=first_name,
            surname=surname,
            sex=sex,
            birth_date=birth_date,
            birth_place=birth_place,
            death_date=death_date,
            death_place=death_place,
            **kwargs,
        )

        # Add to repository
        self.repository.add_person(person)
        self.repository.save()

        return person

    def update_person(
        self,
        person_id: str,
        **updates: Any,
    ) -> Person:
        """
        Update an existing person.

        Args:
            person_id: ID of person to update.
            **updates: Fields to update (first_name, surname, sex, dates, etc.).

        Returns:
            Updated Person instance.

        Raises:
            ValidationError: If validation fails.
            DatabaseError: If person not found or database operation fails.

        Examples:
            >>> person = service.update_person(
            ...     person_id="123",
            ...     birth_place="Warsaw, Poland"
            ... )
        """
        # Get existing person
        person = self.repository.get_person(person_id)

        # Validate and apply updates
        if "first_name" in updates:
            first_name = updates["first_name"]
            if not first_name or not first_name.strip():
                raise ValidationError("first_name", "First name cannot be empty")
            updates["first_name"] = capitalize_name(first_name.strip())

        if "surname" in updates:
            surname = updates["surname"]
            if not surname or not surname.strip():
                raise ValidationError("surname", "Surname cannot be empty")
            updates["surname"] = capitalize_name(surname.strip())

        # Validate date sequence if both dates present
        birth_date = updates.get("birth_date", person.birth_date)
        death_date = updates.get("death_date", person.death_date)
        if birth_date and death_date:
            self._validate_date_sequence(birth_date, death_date, "birth", "death")

        # Create updated person with dataclass replace
        from dataclasses import replace

        updated_person = replace(person, **updates)

        # Update in repository
        self.repository.update_person(updated_person)
        self.repository.save()

        return updated_person

    def delete_person(
        self,
        person_id: str,
        remove_from_families: bool = True,
    ) -> None:
        """
        Delete a person.

        Args:
            person_id: ID of person to delete.
            remove_from_families: Whether to remove person from their families.

        Raises:
            DatabaseError: If person not found or database operation fails.

        Examples:
            >>> service.delete_person("123", remove_from_families=True)
        """
        if remove_from_families:
            # Remove from all families
            families = self.repository.get_person_families(person_id)
            for family in families:
                # Remove as parent
                updates: Dict[str, Any] = {}
                if family.father_id == person_id:
                    updates["father_id"] = None
                if family.mother_id == person_id:
                    updates["mother_id"] = None

                # Remove as child
                if person_id in family.children_ids:
                    children_ids = [cid for cid in family.children_ids if cid != person_id]
                    updates["children_ids"] = children_ids

                if updates:
                    self.repository.update_family(family.id, **updates)

        # Delete person
        self.repository.delete_person(person_id)
        self.repository.save()

    def find_potential_duplicates(
        self,
        first_name: str,
        surname: str,
        birth_date: Optional[Date] = None,
        threshold: float = 0.85,
    ) -> List[Person]:
        """
        Find potential duplicate persons based on name similarity.

        Args:
            first_name: First name to search for.
            surname: Surname to search for.
            birth_date: Birth date to help identify duplicates.
            threshold: Similarity threshold (0.0-1.0) for fuzzy matching.

        Returns:
            List of potentially duplicate persons.

        Examples:
            >>> duplicates = service.find_potential_duplicates(
            ...     first_name="John",
            ...     surname="Smith",
            ...     birth_date=Date(year=1980)
            ... )
        """
        # Normalize search terms
        first_name_norm = normalize_string(first_name)
        normalize_string(surname)

        # Search with exact and fuzzy matching using repository's search_persons
        candidates: List[Person] = []

        # Search by surname
        surname_matches = self.repository.search_persons(
            query=surname,
            search_in=["surname"],
            fuzzy=True,
            threshold=threshold,
        )
        candidates.extend(surname_matches)

        # Filter by first name similarity
        duplicates: List[Person] = []
        for candidate in candidates:
            candidate_first_norm = normalize_string(candidate.first_name)
            if fuzzy_match(first_name_norm, candidate_first_norm, threshold):
                # If birth date provided, check if they match
                if birth_date and candidate.birth_date:
                    # Same year is strong indicator of duplicate
                    if birth_date.year == candidate.birth_date.year:
                        duplicates.append(candidate)
                else:
                    # No birth date comparison possible
                    duplicates.append(candidate)

        return duplicates

    def add_event(
        self,
        person_id: str,
        event: Event,
    ) -> Person:
        """
        Add an event to a person's timeline.

        Args:
            person_id: ID of person.
            event: Event to add.

        Returns:
            Updated Person instance.

        Raises:
            DatabaseError: If person not found.

        Examples:
            >>> event = Event(
            ...     type=EventType.MARRIAGE,
            ...     date=Date(year=1895),
            ...     place="Paris, France"
            ... )
            >>> person = service.add_event("123", event)
        """
        person = self.repository.get_person(person_id)
        person.add_event(event)

        # Update with replace
        from dataclasses import replace

        updated_person = replace(person, events=person.events)
        self.repository.update_person(updated_person)
        self.repository.save()
        return updated_person

    def set_family(
        self,
        person_id: str,
        family_id: str,
    ) -> Person:
        """
        Set a person's primary family (as child).

        Args:
            person_id: ID of person.
            family_id: ID of family.

        Returns:
            Updated Person instance.

        Raises:
            DatabaseError: If person or family not found.

        Examples:
            >>> person = service.set_family("person123", "family456")
        """
        # Verify family exists
        self.repository.get_family(family_id)

        # Update person with replace
        person = self.repository.get_person(person_id)
        from dataclasses import replace

        updated_person = replace(person, family_id=family_id)
        self.repository.update_person(updated_person)
        self.repository.save()

        return updated_person

    def add_family_membership(
        self,
        person_id: str,
        family_id: str,
    ) -> Person:
        """
        Add a family membership (as spouse) to a person.

        Args:
            person_id: ID of person.
            family_id: ID of family.

        Returns:
            Updated Person instance.

        Raises:
            DatabaseError: If person or family not found.

        Examples:
            >>> person = service.add_family_membership("person123", "family789")
        """
        # Verify family exists
        self.repository.get_family(family_id)

        # Get person and add family
        person = self.repository.get_person(person_id)
        family_ids = list(person.family_ids) if person.family_ids else []
        if family_id not in family_ids:
            family_ids.append(family_id)

        # Update person with replace
        from dataclasses import replace

        updated_person = replace(person, family_ids=family_ids)
        self.repository.update_person(updated_person)
        self.repository.save()

        return updated_person

    def get_person_statistics(self, person_id: str) -> Dict[str, Any]:
        """
        Get statistics about a person (age, family count, etc.).

        Args:
            person_id: ID of person.

        Returns:
            Dictionary with statistics.

        Raises:
            DatabaseError: If person not found.

        Examples:
            >>> stats = service.get_person_statistics("123")
            >>> print(stats["age"])
            45
        """
        person = self.repository.get_person(person_id)
        families = self.repository.get_person_families(person_id)
        children = self.repository.get_person_children(person_id)
        parents = self.repository.get_person_parents(person_id)
        siblings = self.repository.get_person_siblings(person_id)

        # Calculate age
        age = None
        if person.birth_date and person.death_date:
            if person.birth_date.year and person.death_date.year:
                age = person.death_date.year - person.birth_date.year

        return {
            "person_id": person_id,
            "full_name": person.full_name(),
            "age": age,
            "is_alive": not bool(person.death_date),
            "families_count": len(families),
            "children_count": len(children),
            "parents_count": len(parents),
            "siblings_count": len(siblings),
            "events_count": len(person.events) if person.events else 0,
        }

    def _validate_date_sequence(
        self,
        first_date: Date,
        second_date: Date,
        first_label: str,
        second_label: str,
    ) -> None:
        """
        Validate that second date is after first date.

        Args:
            first_date: First date.
            second_date: Second date.
            first_label: Label for first date (e.g., "birth").
            second_label: Label for second date (e.g., "death").

        Raises:
            ValidationError: If dates are inconsistent.
        """
        if not first_date.year or not second_date.year:
            return  # Cannot validate without years

        if second_date.year < first_date.year:
            raise ValidationError(
                second_label,
                f"{second_label.capitalize()} date ({second_date.year}) "
                f"cannot be before {first_label} date ({first_date.year})",
            )

        # Check month if both have months
        if first_date.month and second_date.month and first_date.year == second_date.year:
            if second_date.month < first_date.month:
                raise ValidationError(
                    second_label,
                    f"{second_label.capitalize()} date " f"cannot be before {first_label} date in same year",
                )

            # Check day if both have days
            if first_date.day and second_date.day and first_date.month == second_date.month:
                if second_date.day < first_date.day:
                    raise ValidationError(
                        second_label,
                        f"{second_label.capitalize()} date " f"cannot be before {first_label} date in same month",
                    )
