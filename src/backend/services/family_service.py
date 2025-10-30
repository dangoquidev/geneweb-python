"""
Family service - Business logic for family management.

This service provides high-level operations for creating, updating, and managing
families with validation and relationship integrity.
"""

import uuid
from typing import Any, Dict, List, Optional

from backend.core.exceptions import DatabaseError, ValidationError
from backend.core.models import Date, Family, MaritalStatus, Sex
from backend.database.repository import Repository


class FamilyService:
    """
    Service for managing families with business logic.

    This service encapsulates all business rules for family management,
    including validation and relationship integrity checks.

    Args:
        repository: Repository instance for data access.

    Examples:
        >>> repo = Repository(driver)
        >>> service = FamilyService(repo)
        >>> family = service.create_family(
        ...     father_id="123",
        ...     mother_id="456"
        ... )
    """

    def __init__(self, repository: Repository) -> None:
        """
        Initialize family service.

        Args:
            repository: Repository instance for data access.
        """
        self.repository = repository

    def create_family(
        self,
        father_id: Optional[str] = None,
        mother_id: Optional[str] = None,
        children_ids: Optional[List[str]] = None,
        marital_status: MaritalStatus = MaritalStatus.UNKNOWN,
        marriage_date: Optional[Date] = None,
        marriage_place: Optional[str] = None,
        divorce_date: Optional[Date] = None,
        divorce_place: Optional[str] = None,
        validate_parents: bool = True,
        **kwargs: Any,
    ) -> Family:
        """
        Create a new family with validation.

        Args:
            father_id: ID of father (optional).
            mother_id: ID of mother (optional).
            children_ids: List of children IDs (optional).
            marital_status: Marital status of parents.
            marriage_date: Marriage date if applicable.
            marriage_place: Marriage place if applicable.
            divorce_date: Divorce date if applicable.
            divorce_place: Divorce place if applicable.
            validate_parents: Whether to validate parent sex.
            **kwargs: Additional family attributes.

        Returns:
            Created Family instance.

        Raises:
            ValidationError: If validation fails.
            DatabaseError: If database operation fails.

        Examples:
            >>> family = service.create_family(
            ...     father_id="123",
            ...     mother_id="456",
            ...     marital_status=MaritalStatus.MARRIED,
            ...     marriage_date=Date(year=1950)
            ... )
        """
        # Validate at least one parent
        if not father_id and not mother_id:
            raise ValidationError(
                "parents",
                "Family must have at least one parent",
            )

        # Validate parents exist and have correct sex
        if validate_parents:
            if father_id:
                father = self.repository.get_person(father_id)
                if father.sex == Sex.FEMALE:
                    raise ValidationError(
                        "father_id",
                        f"Person {father_id} is marked as female",
                    )

            if mother_id:
                mother = self.repository.get_person(mother_id)
                if mother.sex == Sex.MALE:
                    raise ValidationError(
                        "mother_id",
                        f"Person {mother_id} is marked as male",
                    )

        # Validate children exist
        if children_ids:
            for child_id in children_ids:
                self.repository.get_person(child_id)

        # Validate date sequence
        if marriage_date and divorce_date:
            self._validate_date_sequence(
                marriage_date,
                divorce_date,
                "marriage",
                "divorce",
            )

        # Create family
        family_id = str(uuid.uuid4())
        family = Family(
            id=family_id,
            father_id=father_id,
            mother_id=mother_id,
            children_ids=children_ids or [],
            marital_status=marital_status,
            marriage_date=marriage_date,
            marriage_place=marriage_place,
            divorce_date=divorce_date,
            divorce_place=divorce_place,
            **kwargs,
        )

        # Add to repository
        self.repository.add_family(family)

        # Update parent memberships
        if father_id:
            self._add_family_to_person(father_id, family_id)
        if mother_id:
            self._add_family_to_person(mother_id, family_id)

        # Update children family references
        for child_id in children_ids or []:
            self._set_person_family(child_id, family_id)

        self.repository.save()

        return family

    def update_family(
        self,
        family_id: str,
        validate_parents: bool = True,
        **updates: Any,
    ) -> Family:
        """
        Update an existing family.

        Args:
            family_id: ID of family to update.
            validate_parents: Whether to validate parent sex.
            **updates: Fields to update.

        Returns:
            Updated Family instance.

        Raises:
            ValidationError: If validation fails.
            DatabaseError: If family not found or database operation fails.

        Examples:
            >>> family = service.update_family(
            ...     family_id="789",
            ...     marital_status=MaritalStatus.DIVORCED,
            ...     divorce_date=Date(year=1960)
            ... )
        """
        # Get existing family
        family = self.repository.get_family(family_id)

        # Validate parent sex if changed
        if validate_parents:
            if "father_id" in updates and updates["father_id"]:
                father = self.repository.get_person(updates["father_id"])
                if father.sex == Sex.FEMALE:
                    raise ValidationError(
                        "father_id",
                        f"Person {updates['father_id']} is marked as female",
                    )

            if "mother_id" in updates and updates["mother_id"]:
                mother = self.repository.get_person(updates["mother_id"])
                if mother.sex == Sex.MALE:
                    raise ValidationError(
                        "mother_id",
                        f"Person {updates['mother_id']} is marked as male",
                    )

        # Validate date sequence
        marriage_date = updates.get("marriage_date", family.marriage_date)
        divorce_date = updates.get("divorce_date", family.divorce_date)
        if marriage_date and divorce_date:
            self._validate_date_sequence(
                marriage_date,
                divorce_date,
                "marriage",
                "divorce",
            )

        # Handle parent changes - update person memberships
        if "father_id" in updates and updates["father_id"] != family.father_id:
            # Remove old father
            if family.father_id:
                self._remove_family_from_person(family.father_id, family_id)
            # Add new father
            if updates["father_id"]:
                self._add_family_to_person(updates["father_id"], family_id)

        if "mother_id" in updates and updates["mother_id"] != family.mother_id:
            # Remove old mother
            if family.mother_id:
                self._remove_family_from_person(family.mother_id, family_id)
            # Add new mother
            if updates["mother_id"]:
                self._add_family_to_person(updates["mother_id"], family_id)

        # Update family with replace
        from dataclasses import replace

        updated_family = replace(family, **updates)
        self.repository.update_family(updated_family)
        self.repository.save()

        return updated_family

    def delete_family(
        self,
        family_id: str,
        update_members: bool = True,
    ) -> None:
        """
        Delete a family.

        Args:
            family_id: ID of family to delete.
            update_members: Whether to update family members.

        Raises:
            DatabaseError: If family not found or database operation fails.

        Examples:
            >>> service.delete_family("789", update_members=True)
        """
        if update_members:
            family = self.repository.get_family(family_id)

            # Remove from parents
            if family.father_id:
                self._remove_family_from_person(family.father_id, family_id)
            if family.mother_id:
                self._remove_family_from_person(family.mother_id, family_id)

            # Remove from children
            for child_id in family.children_ids:
                person = self.repository.get_person(child_id)
                if person.family_id == family_id:
                    from dataclasses import replace

                    updated_person = replace(person, family_id=None)
                    self.repository.update_person(updated_person)

        # Delete family
        self.repository.delete_family(family_id)
        self.repository.save()

    def add_child(
        self,
        family_id: str,
        child_id: str,
        set_as_primary_family: bool = True,
    ) -> Family:
        """
        Add a child to a family.

        Args:
            family_id: ID of family.
            child_id: ID of child to add.
            set_as_primary_family: Whether to set this as child's primary family.

        Returns:
            Updated Family instance.

        Raises:
            DatabaseError: If family or child not found.

        Examples:
            >>> family = service.add_child("family789", "child123")
        """
        # Verify child exists
        self.repository.get_person(child_id)

        # Get family and add child
        family = self.repository.get_family(family_id)
        children_ids = list(family.children_ids)
        if child_id not in children_ids:
            children_ids.append(child_id)

        # Update family with replace
        from dataclasses import replace

        updated_family = replace(family, children_ids=children_ids)
        self.repository.update_family(updated_family)

        # Update child's family reference
        if set_as_primary_family:
            self._set_person_family(child_id, family_id)

        self.repository.save()

        return updated_family

    def remove_child(
        self,
        family_id: str,
        child_id: str,
        clear_family_reference: bool = True,
    ) -> Family:
        """
        Remove a child from a family.

        Args:
            family_id: ID of family.
            child_id: ID of child to remove.
            clear_family_reference: Whether to clear child's family reference.

        Returns:
            Updated Family instance.

        Raises:
            DatabaseError: If family not found.

        Examples:
            >>> family = service.remove_child("family789", "child123")
        """
        # Get family and remove child
        family = self.repository.get_family(family_id)
        children_ids = [cid for cid in family.children_ids if cid != child_id]

        # Update family with replace
        from dataclasses import replace

        updated_family = replace(family, children_ids=children_ids)
        self.repository.update_family(updated_family)

        # Clear child's family reference if it points to this family
        if clear_family_reference:
            try:
                person = self.repository.get_person(child_id)
                if person.family_id == family_id:
                    updated_person = replace(person, family_id=None)
                    self.repository.update_person(updated_person)
            except DatabaseError:
                pass  # Child might not exist anymore

        self.repository.save()

        return updated_family

    def get_family_statistics(self, family_id: str) -> Dict[str, Any]:
        """
        Get statistics about a family.

        Args:
            family_id: ID of family.

        Returns:
            Dictionary with statistics.

        Raises:
            DatabaseError: If family not found.

        Examples:
            >>> stats = service.get_family_statistics("789")
            >>> print(stats["children_count"])
            3
        """
        family = self.repository.get_family(family_id)

        # Get parent info
        father_name = None
        mother_name = None
        if family.father_id:
            try:
                father = self.repository.get_person(family.father_id)
                father_name = father.full_name()
            except DatabaseError:
                pass

        if family.mother_id:
            try:
                mother = self.repository.get_person(family.mother_id)
                mother_name = mother.full_name()
            except DatabaseError:
                pass

        return {
            "family_id": family_id,
            "father_name": father_name,
            "mother_name": mother_name,
            "children_count": len(family.children_ids),
            "is_married": family.is_married(),
            "is_divorced": family.is_divorced(),
            "marital_status": family.marital_status.value,
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
            first_label: Label for first date.
            second_label: Label for second date.

        Raises:
            ValidationError: If dates are inconsistent.
        """
        if not first_date.year or not second_date.year:
            return

        if second_date.year < first_date.year:
            raise ValidationError(
                second_label,
                f"{second_label.capitalize()} date ({second_date.year}) "
                f"cannot be before {first_label} date ({first_date.year})",
            )

    def _add_family_to_person(self, person_id: str, family_id: str) -> None:
        """Add family membership to person's family_ids list."""
        person = self.repository.get_person(person_id)
        family_ids = list(person.family_ids) if person.family_ids else []
        if family_id not in family_ids:
            family_ids.append(family_id)
            from dataclasses import replace

            updated_person = replace(person, family_ids=family_ids)
            self.repository.update_person(updated_person)

    def _remove_family_from_person(self, person_id: str, family_id: str) -> None:
        """Remove family membership from person's family_ids list."""
        try:
            person = self.repository.get_person(person_id)
            if person.family_ids:
                family_ids = [fid for fid in person.family_ids if fid != family_id]
                from dataclasses import replace

                updated_person = replace(person, family_ids=family_ids)
                self.repository.update_person(updated_person)
        except DatabaseError:
            pass  # Person might not exist anymore

    def _set_person_family(self, person_id: str, family_id: str) -> None:
        """Set person's primary family (as child)."""
        person = self.repository.get_person(person_id)
        from dataclasses import replace

        updated_person = replace(person, family_id=family_id)
        self.repository.update_person(updated_person)
