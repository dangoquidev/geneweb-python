"""
Search service - Advanced search and genealogy calculations.

This service provides sophisticated search capabilities including filtering,
sorting, pagination, and genealogy tree calculations (ancestors, descendants).
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, cast

from backend.core.exceptions import ValidationError
from backend.core.models import Person, Sex
from backend.database.repository import Repository
from backend.utils.string_utils import normalize_string


@dataclass
class SearchFilters:
    """
    Filters for person search.

    Attributes:
        first_name: Filter by first name (fuzzy).
        last_name: Filter by surname (fuzzy).
        sex: Filter by sex.
        birth_year_min: Minimum birth year.
        birth_year_max: Maximum birth year.
        death_year_min: Minimum death year.
        death_year_max: Maximum death year.
        birth_place: Filter by birth place (fuzzy).
        death_place: Filter by death place (fuzzy).
        is_alive: Filter by alive status.
    """

    first_name: Optional[str] = None
    last_name: Optional[str] = None
    sex: Optional[Sex] = None
    birth_year_min: Optional[int] = None
    birth_year_max: Optional[int] = None
    death_year_min: Optional[int] = None
    death_year_max: Optional[int] = None
    birth_place: Optional[str] = None
    death_place: Optional[str] = None
    is_alive: Optional[bool] = None


@dataclass
class SearchResult:
    """
    Search result with pagination info.

    Attributes:
        persons: List of matching persons.
        total_count: Total number of matches.
        page: Current page number (1-indexed).
        page_size: Number of results per page.
        total_pages: Total number of pages.
    """

    persons: List[Person]
    total_count: int
    page: int
    page_size: int
    total_pages: int


class SearchService:
    """
    Service for advanced search and genealogy calculations.

    This service provides sophisticated search capabilities with filtering,
    sorting, and pagination, plus genealogy tree traversal.

    Args:
        repository: Repository instance for data access.

    Examples:
        >>> repo = Repository(driver)
        >>> service = SearchService(repo)
        >>> results = service.search_persons(
        ...     filters=SearchFilters(last_name="Curie"),
        ...     page=1,
        ...     page_size=10
        ... )
    """

    def __init__(self, repository: Repository) -> None:
        """
        Initialize search service.

        Args:
            repository: Repository instance for data access.
        """
        self.repository = repository

    def search_persons(
        self,
        filters: SearchFilters,
        sort_by: str = "surname",
        sort_desc: bool = False,
        page: int = 1,
        page_size: int = 50,
    ) -> SearchResult:
        """
        Search persons with filters, sorting, and pagination.

        Args:
            filters: Search filters to apply.
            sort_by: Field to sort by (surname, first_name, birth_date).
            sort_desc: Whether to sort descending.
            page: Page number (1-indexed).
            page_size: Number of results per page.

        Returns:
            SearchResult with matching persons and pagination info.

        Raises:
            ValidationError: If invalid parameters.

        Examples:
            >>> filters = SearchFilters(
            ...     last_name="Smith",
            ...     birth_year_min=1900,
            ...     birth_year_max=2000
            ... )
            >>> results = service.search_persons(filters, page=1, page_size=20)
        """
        if page < 1:
            raise ValidationError("page", "Page must be >= 1")
        if page_size < 1 or page_size > 1000:
            raise ValidationError("page_size", "Page size must be between 1 and 1000")

        # Get all persons (dict from repository, convert to list)
        all_persons_dict = self.repository.get_all_persons()
        all_persons = list(all_persons_dict.values())

        # Apply filters
        filtered_persons = self._apply_filters(all_persons, filters)

        # Sort results
        sorted_persons = self._sort_persons(filtered_persons, sort_by, sort_desc)

        # Calculate pagination
        total_count = len(sorted_persons)
        total_pages = (total_count + page_size - 1) // page_size if total_count > 0 else 1
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_persons = sorted_persons[start_idx:end_idx]

        return SearchResult(
            persons=paginated_persons,
            total_count=total_count,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    def get_ancestors(
        self,
        person_id: str,
        max_generations: Optional[int] = None,
    ) -> List[Person]:
        """
        Get all ancestors of a person (parents, grandparents, etc.).

        Args:
            person_id: ID of person.
            max_generations: Maximum number of generations to traverse (None = all).

        Returns:
            List of ancestor persons.

        Raises:
            DatabaseError: If person not found.

        Examples:
            >>> ancestors = service.get_ancestors("123", max_generations=3)
        """
        ancestors: List[Person] = []
        visited: Set[str] = set()

        def traverse(current_id: str, generation: int) -> None:
            if current_id in visited:
                return
            if max_generations is not None and generation > max_generations:
                return

            visited.add(current_id)

            # Get parents (returns tuple)
            parents_tuple = self.repository.get_person_parents(current_id)
            parents = [p for p in parents_tuple if p is not None]
            for parent in parents:
                if parent.id not in visited:
                    ancestors.append(parent)
                    traverse(parent.id, generation + 1)

        traverse(person_id, 1)
        return ancestors

    def get_descendants(
        self,
        person_id: str,
        max_generations: Optional[int] = None,
    ) -> List[Person]:
        """
        Get all descendants of a person (children, grandchildren, etc.).

        Args:
            person_id: ID of person.
            max_generations: Maximum number of generations to traverse (None = all).

        Returns:
            List of descendant persons.

        Raises:
            DatabaseError: If person not found.

        Examples:
            >>> descendants = service.get_descendants("123", max_generations=2)
        """
        descendants: List[Person] = []
        visited: Set[str] = set()

        def traverse(current_id: str, generation: int) -> None:
            if current_id in visited:
                return
            if max_generations is not None and generation > max_generations:
                return

            visited.add(current_id)

            # Get children
            children = self.repository.get_person_children(current_id)
            for child in children:
                if child.id not in visited:
                    descendants.append(child)
                    traverse(child.id, generation + 1)

        traverse(person_id, 1)
        return descendants

    def get_all_relatives(
        self,
        person_id: str,
        max_distance: Optional[int] = None,
    ) -> List[Person]:
        """
        Get all relatives of a person up to a certain distance.

        Args:
            person_id: ID of person.
            max_distance: Maximum relationship distance (None = all).

        Returns:
            List of all related persons.

        Raises:
            DatabaseError: If person not found.

        Examples:
            >>> relatives = service.get_all_relatives("123", max_distance=3)
        """
        # Get ancestors and descendants
        ancestors = self.get_ancestors(person_id, max_distance)
        descendants = self.get_descendants(person_id, max_distance)

        # Get siblings
        siblings = self.repository.get_person_siblings(person_id)

        # Combine and deduplicate
        all_relatives_dict: Dict[str, Person] = {}
        for person in ancestors + descendants + siblings:
            all_relatives_dict[person.id] = person

        return list(all_relatives_dict.values())

    def find_relationship_path(
        self,
        person1_id: str,
        person2_id: str,
        max_depth: int = 10,
    ) -> Optional[List[Person]]:
        """
        Find shortest relationship path between two persons.

        Uses breadth-first search to find the shortest path through family
        relationships (parent-child, spouse).

        Args:
            person1_id: ID of first person.
            person2_id: ID of second person.
            max_depth: Maximum search depth.

        Returns:
            List of persons forming the path, or None if no path found.

        Raises:
            DatabaseError: If either person not found.

        Examples:
            >>> path = service.find_relationship_path("123", "456")
            >>> if path:
            ...     print(" -> ".join(p.full_name for p in path))
        """
        # Verify both persons exist
        self.repository.get_person(person1_id)
        self.repository.get_person(person2_id)

        if person1_id == person2_id:
            return [self.repository.get_person(person1_id)]

        # BFS to find shortest path
        from collections import deque

        queue: deque = deque([(person1_id, [person1_id])])
        visited: Set[str] = {person1_id}

        while queue:
            current_id, path = queue.popleft()

            if len(path) > max_depth:
                continue

            # Get related persons
            parents_tuple = self.repository.get_person_parents(current_id)
            parents = [p for p in parents_tuple if p is not None]  # Filter out None values
            children = self.repository.get_person_children(current_id)
            siblings = self.repository.get_person_siblings(current_id)

            # Get spouses (from family memberships)
            families = self.repository.get_person_families(current_id)
            spouses: List[Person] = []
            for family in families:
                if family.father_id and family.father_id != current_id:
                    try:
                        spouses.append(self.repository.get_person(family.father_id))
                    except BaseException:
                        pass
                if family.mother_id and family.mother_id != current_id:
                    try:
                        spouses.append(self.repository.get_person(family.mother_id))
                    except BaseException:
                        pass

            # Check all related persons
            for related in parents + children + siblings + spouses:
                if related.id == person2_id:
                    # Found target
                    full_path = path + [related.id]
                    return [self.repository.get_person(pid) for pid in full_path]

                if related.id not in visited:
                    visited.add(related.id)
                    queue.append((related.id, path + [related.id]))

        return None  # No path found

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get overall database statistics.

        Returns:
            Dictionary with various statistics.

        Examples:
            >>> stats = service.get_statistics()
            >>> print(f"Total persons: {stats['total_persons']}")
        """
        stats = self.repository.get_statistics()

        # Calculate additional statistics (convert dict to list)
        all_persons_dict = self.repository.get_all_persons()
        all_persons = list(all_persons_dict.values())

        male_count = sum(1 for p in all_persons if p.sex == Sex.MALE)
        female_count = sum(1 for p in all_persons if p.sex == Sex.FEMALE)
        unknown_sex_count = sum(1 for p in all_persons if p.sex == Sex.UNKNOWN)

        living_count = sum(1 for p in all_persons if not p.death_date)
        deceased_count = sum(1 for p in all_persons if p.death_date)

        with_birth_date = sum(1 for p in all_persons if p.birth_date)
        with_death_date = sum(1 for p in all_persons if p.death_date)

        stats.update(
            {
                "male_count": male_count,
                "female_count": female_count,
                "unknown_sex_count": unknown_sex_count,
                "living_count": living_count,
                "deceased_count": deceased_count,
                "with_birth_date": with_birth_date,
                "with_death_date": with_death_date,
            }
        )

        return cast(dict[str, Any], stats)

    def _apply_filters(
        self,
        persons: List[Person],
        filters: SearchFilters,
    ) -> List[Person]:
        """Apply search filters to person list."""
        filtered = persons

        # Name filters (fuzzy)
        if filters.first_name:
            first_name_norm = normalize_string(filters.first_name)
            filtered = [p for p in filtered if first_name_norm in normalize_string(p.first_name)]

        if filters.last_name:
            last_name_norm = normalize_string(filters.last_name)
            filtered = [p for p in filtered if last_name_norm in normalize_string(p.surname)]

        # Sex filter
        if filters.sex is not None:
            filtered = [p for p in filtered if p.sex == filters.sex]

        # Birth year filters
        if filters.birth_year_min is not None:
            filtered = [
                p
                for p in filtered
                if p.birth_date and p.birth_date.year and p.birth_date.year >= filters.birth_year_min
            ]

        if filters.birth_year_max is not None:
            filtered = [
                p
                for p in filtered
                if p.birth_date and p.birth_date.year and p.birth_date.year <= filters.birth_year_max
            ]

        # Death year filters
        if filters.death_year_min is not None:
            filtered = [
                p
                for p in filtered
                if p.death_date and p.death_date.year and p.death_date.year >= filters.death_year_min
            ]

        if filters.death_year_max is not None:
            filtered = [
                p
                for p in filtered
                if p.death_date and p.death_date.year and p.death_date.year <= filters.death_year_max
            ]

        # Place filters (fuzzy)
        if filters.birth_place:
            place_norm = normalize_string(filters.birth_place)
            filtered = [p for p in filtered if p.birth_place and place_norm in normalize_string(p.birth_place)]

        if filters.death_place:
            place_norm = normalize_string(filters.death_place)
            filtered = [p for p in filtered if p.death_place and place_norm in normalize_string(p.death_place)]

        # Alive status filter
        if filters.is_alive is not None:
            if filters.is_alive:
                filtered = [p for p in filtered if not p.death_date]
            else:
                filtered = [p for p in filtered if p.death_date]

        return filtered

    def _sort_persons(
        self,
        persons: List[Person],
        sort_by: str,
        descending: bool = False,
    ) -> List[Person]:
        """Sort persons by specified field."""
        if sort_by == "surname" or sort_by == "last_name":

            def key_func(p):
                return normalize_string(p.surname)

        elif sort_by == "first_name":

            def key_func(p):
                return normalize_string(p.first_name)

        elif sort_by == "birth_date":

            def key_func(p):
                return p.birth_date.year if p.birth_date and p.birth_date.year else 9999

        elif sort_by == "death_date":

            def key_func(p):
                return p.death_date.year if p.death_date and p.death_date.year else 9999

        else:
            # Default to surname
            def key_func(p):
                return normalize_string(p.surname)

        return sorted(persons, key=key_func, reverse=descending)
