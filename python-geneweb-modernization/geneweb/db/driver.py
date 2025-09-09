"""
Database driver interface for GenEWeb

This module provides the database abstraction layer for GenEWeb,
allowing different database backends while maintaining compatibility
with the original database formats.

Copyright (c) 1998-2007 INRIA
Python modernization preserving original structure and functionality.
"""

import os
import pickle
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Protocol, Tuple

from ..core.definitions import Ascendants, BaseUpdate, Descendants, Family, NameKey, Person, Union, Warning


class PersonId(int):
    """Type for person identifiers"""

    pass


class FamilyId(int):
    """Type for family identifiers"""

    pass


@dataclass
class DatabaseInfo:
    """Information about a database"""

    name: str
    path: str
    number_of_persons: int
    number_of_families: int
    created_date: Optional[str] = None
    modified_date: Optional[str] = None
    version: str = "1.0"


class DatabaseDriver(ABC):
    """
    Abstract base class for database drivers
    Provides interface for all database operations
    """

    def __init__(self, database_path: str):
        self.database_path = database_path
        self.database_name = os.path.basename(database_path)
        self.is_open = False

    @abstractmethod
    def open_database(self, read_only: bool = True) -> bool:
        """Open the database connection"""
        pass

    @abstractmethod
    def close_database(self) -> None:
        """Close the database connection"""
        pass

    @abstractmethod
    def get_database_info(self) -> DatabaseInfo:
        """Get information about the database"""
        pass

    # Person operations
    @abstractmethod
    def get_person(self, person_id: PersonId) -> Optional[Person]:
        """Retrieve a person by ID"""
        pass

    @abstractmethod
    def get_persons(self) -> Iterator[Tuple[PersonId, Person]]:
        """Iterate over all persons"""
        pass

    @abstractmethod
    def find_person_by_name(
        self, first_name: str, surname: str, occurrence: int = 0
    ) -> Optional[Tuple[PersonId, Person]]:
        """Find person by name"""
        pass

    @abstractmethod
    def search_persons(self, query: str, max_results: int = 100) -> List[Tuple[PersonId, Person]]:
        """Search persons by various criteria"""
        pass

    @abstractmethod
    def add_person(self, person: Person) -> PersonId:
        """Add a new person"""
        pass

    @abstractmethod
    def update_person(self, person_id: PersonId, person: Person) -> bool:
        """Update an existing person"""
        pass

    @abstractmethod
    def delete_person(self, person_id: PersonId) -> bool:
        """Delete a person"""
        pass

    # Family operations
    @abstractmethod
    def get_family(self, family_id: FamilyId) -> Optional[Family]:
        """Retrieve a family by ID"""
        pass

    @abstractmethod
    def get_families(self) -> Iterator[Tuple[FamilyId, Family]]:
        """Iterate over all families"""
        pass

    @abstractmethod
    def add_family(self, family: Family) -> FamilyId:
        """Add a new family"""
        pass

    @abstractmethod
    def update_family(self, family_id: FamilyId, family: Family) -> bool:
        """Update an existing family"""
        pass

    @abstractmethod
    def delete_family(self, family_id: FamilyId) -> bool:
        """Delete a family"""
        pass

    # Relationship operations
    @abstractmethod
    def get_ascendants(self, person_id: PersonId) -> Optional[Ascendants]:
        """Get person's ascendants (parents)"""
        pass

    @abstractmethod
    def get_union(self, person_id: PersonId) -> Optional[Union]:
        """Get person's unions (families as parent)"""
        pass

    @abstractmethod
    def get_descendants(self, family_id: FamilyId) -> Optional[Descendants]:
        """Get family's descendants (children)"""
        pass

    @abstractmethod
    def set_ascendants(self, person_id: PersonId, ascendants: Ascendants) -> bool:
        """Set person's ascendants"""
        pass

    @abstractmethod
    def set_union(self, person_id: PersonId, union: Union) -> bool:
        """Set person's unions"""
        pass

    @abstractmethod
    def set_descendants(self, family_id: FamilyId, descendants: Descendants) -> bool:
        """Set family's descendants"""
        pass

    # Validation and integrity
    @abstractmethod
    def validate_database(self) -> List[Warning]:
        """Validate database integrity and return warnings"""
        pass

    @abstractmethod
    def check_person(self, person: Person) -> List[Warning]:
        """Check a person for potential issues"""
        pass

    @abstractmethod
    def check_family(self, family: Family) -> List[Warning]:
        """Check a family for potential issues"""
        pass

    # History and updates
    @abstractmethod
    def record_update(self, update: BaseUpdate) -> bool:
        """Record an update for history tracking"""
        pass

    @abstractmethod
    def get_update_history(self, limit: Optional[int] = None) -> List[BaseUpdate]:
        """Get update history"""
        pass

    # Utility methods
    @abstractmethod
    def get_person_count(self) -> int:
        """Get total number of persons"""
        pass

    @abstractmethod
    def get_family_count(self) -> int:
        """Get total number of families"""
        pass

    @abstractmethod
    def backup_database(self, backup_path: str) -> bool:
        """Create a backup of the database"""
        pass

    @abstractmethod
    def restore_database(self, backup_path: str) -> bool:
        """Restore database from backup"""
        pass


class PickleDatabaseDriver(DatabaseDriver):
    """
    Simple file-based database driver using pickle format
    This provides a basic implementation for development and small databases
    """

    def __init__(self, database_path: str):
        super().__init__(database_path)
        self.persons: Dict[PersonId, Person] = {}
        self.families: Dict[FamilyId, Family] = {}
        self.ascendants: Dict[PersonId, Ascendants] = {}
        self.unions: Dict[PersonId, Union] = {}
        self.descendants: Dict[FamilyId, Descendants] = {}
        self.name_index: Dict[NameKey, PersonId] = {}
        self.next_person_id = 1
        self.next_family_id = 1
        self.update_history: List[BaseUpdate] = []

    def open_database(self, read_only: bool = True) -> bool:
        """Open the pickle database"""
        try:
            if os.path.exists(self.database_path):
                self._load_database()
            else:
                # Create new empty database
                self._create_new_database()
            self.is_open = True
            return True
        except Exception as e:
            print(f"Error opening database: {e}")
            return False

    def close_database(self) -> None:
        """Close and save the database"""
        if self.is_open:
            self._save_database()
            self.is_open = False

    def get_database_info(self) -> DatabaseInfo:
        """Get database information"""
        return DatabaseInfo(
            name=self.database_name,
            path=self.database_path,
            number_of_persons=len(self.persons),
            number_of_families=len(self.families),
        )

    def get_person(self, person_id: PersonId) -> Optional[Person]:
        """Get person by ID"""
        return self.persons.get(person_id)

    def get_persons(self) -> Iterator[Tuple[PersonId, Person]]:
        """Iterate over all persons"""
        for person_id, person in self.persons.items():
            yield (person_id, person)

    def find_person_by_name(
        self, first_name: str, surname: str, occurrence: int = 0
    ) -> Optional[Tuple[PersonId, Person]]:
        """Find person by name"""
        key = NameKey(first_name, surname, occurrence)
        person_id = self.name_index.get(key)
        if person_id:
            person = self.persons.get(person_id)
            if person:
                return (person_id, person)
        return None

    def search_persons(self, query: str, max_results: int = 100) -> List[Tuple[PersonId, Person]]:
        """Simple search implementation"""
        results = []
        query = query.lower()

        for person_id, person in self.persons.items():
            if len(results) >= max_results:
                break

            # Search in names
            if (
                query in person.first_name.lower()
                or query in person.surname.lower()
                or query in person.public_name.lower()
            ):
                results.append((person_id, person))

        return results

    def add_person(self, person: Person) -> PersonId:
        """Add a new person"""
        person_id = PersonId(self.next_person_id)
        self.next_person_id += 1

        person.key_index = person_id
        self.persons[person_id] = person

        # Update name index
        key = NameKey(person.first_name, person.surname, person.occurrence)
        self.name_index[key] = person_id

        return person_id

    def update_person(self, person_id: PersonId, person: Person) -> bool:
        """Update an existing person"""
        if person_id in self.persons:
            old_person = self.persons[person_id]

            # Update name index if name changed
            old_key = NameKey(
                old_person.first_name,
                old_person.surname,
                old_person.occurrence,
            )
            new_key = NameKey(person.first_name, person.surname, person.occurrence)

            if old_key != new_key:
                if old_key in self.name_index:
                    del self.name_index[old_key]
                self.name_index[new_key] = person_id

            person.key_index = person_id
            self.persons[person_id] = person
            return True

        return False

    def delete_person(self, person_id: PersonId) -> bool:
        """Delete a person"""
        if person_id in self.persons:
            person = self.persons[person_id]

            # Remove from name index
            key = NameKey(person.first_name, person.surname, person.occurrence)
            if key in self.name_index:
                del self.name_index[key]

            # Remove person
            del self.persons[person_id]

            # Clean up relationships
            if person_id in self.ascendants:
                del self.ascendants[person_id]
            if person_id in self.unions:
                del self.unions[person_id]

            return True

        return False

    def get_family(self, family_id: FamilyId) -> Optional[Family]:
        """Get family by ID"""
        return self.families.get(family_id)

    def get_families(self) -> Iterator[Tuple[FamilyId, Family]]:
        """Iterate over all families"""
        for family_id, family in self.families.items():
            yield (family_id, family)

    def add_family(self, family: Family) -> FamilyId:
        """Add a new family"""
        family_id = FamilyId(self.next_family_id)
        self.next_family_id += 1

        family.family_index = family_id
        self.families[family_id] = family

        return family_id

    def update_family(self, family_id: FamilyId, family: Family) -> bool:
        """Update an existing family"""
        if family_id in self.families:
            family.family_index = family_id
            self.families[family_id] = family
            return True
        return False

    def delete_family(self, family_id: FamilyId) -> bool:
        """Delete a family"""
        if family_id in self.families:
            del self.families[family_id]

            # Clean up relationships
            if family_id in self.descendants:
                del self.descendants[family_id]

            return True
        return False

    def get_ascendants(self, person_id: PersonId) -> Optional[Ascendants]:
        """Get person's ascendants"""
        return self.ascendants.get(person_id)

    def get_union(self, person_id: PersonId) -> Optional[Union]:
        """Get person's unions"""
        return self.unions.get(person_id)

    def get_descendants(self, family_id: FamilyId) -> Optional[Descendants]:
        """Get family's descendants"""
        return self.descendants.get(family_id)

    def set_ascendants(self, person_id: PersonId, ascendants: Ascendants) -> bool:
        """Set person's ascendants"""
        self.ascendants[person_id] = ascendants
        return True

    def set_union(self, person_id: PersonId, union: Union) -> bool:
        """Set person's unions"""
        self.unions[person_id] = union
        return True

    def set_descendants(self, family_id: FamilyId, descendants: Descendants) -> bool:
        """Set family's descendants"""
        self.descendants[family_id] = descendants
        return True

    def validate_database(self) -> List[Warning]:
        """Basic validation - would be expanded in full implementation"""
        warnings = []
        # Implementation would check for data consistency issues
        return warnings

    def check_person(self, person: Person) -> List[Warning]:
        """Check person for issues"""
        warnings = []
        # Implementation would check person data for issues
        return warnings

    def check_family(self, family: Family) -> List[Warning]:
        """Check family for issues"""
        warnings = []
        # Implementation would check family data for issues
        return warnings

    def record_update(self, update: BaseUpdate) -> bool:
        """Record an update"""
        self.update_history.append(update)
        return True

    def get_update_history(self, limit: Optional[int] = None) -> List[BaseUpdate]:
        """Get update history"""
        if limit:
            return self.update_history[-limit:]
        return self.update_history.copy()

    def get_person_count(self) -> int:
        """Get person count"""
        return len(self.persons)

    def get_family_count(self) -> int:
        """Get family count"""
        return len(self.families)

    def backup_database(self, backup_path: str) -> bool:
        """Create backup"""
        try:
            import shutil

            shutil.copy2(self.database_path, backup_path)
            return True
        except Exception:
            return False

    def restore_database(self, backup_path: str) -> bool:
        """Restore from backup"""
        try:
            import shutil

            shutil.copy2(backup_path, self.database_path)
            self._load_database()
            return True
        except Exception:
            return False

    def _create_new_database(self) -> None:
        """Create a new empty database"""
        self.persons = {}
        self.families = {}
        self.ascendants = {}
        self.unions = {}
        self.descendants = {}
        self.name_index = {}
        self.next_person_id = 1
        self.next_family_id = 1
        self.update_history = []

    def _load_database(self) -> None:
        """Load database from pickle file"""
        with open(self.database_path, "rb") as f:
            data = pickle.load(f)
            self.persons = data.get("persons", {})
            self.families = data.get("families", {})
            self.ascendants = data.get("ascendants", {})
            self.unions = data.get("unions", {})
            self.descendants = data.get("descendants", {})
            self.name_index = data.get("name_index", {})
            self.next_person_id = data.get("next_person_id", 1)
            self.next_family_id = data.get("next_family_id", 1)
            self.update_history = data.get("update_history", [])

    def _save_database(self) -> None:
        """Save database to pickle file"""
        data = {
            "persons": self.persons,
            "families": self.families,
            "ascendants": self.ascendants,
            "unions": self.unions,
            "descendants": self.descendants,
            "name_index": self.name_index,
            "next_person_id": self.next_person_id,
            "next_family_id": self.next_family_id,
            "update_history": self.update_history,
        }

        # Create backup first
        if os.path.exists(self.database_path):
            backup_path = self.database_path + ".backup"
            import shutil

            shutil.copy2(self.database_path, backup_path)

        with open(self.database_path, "wb") as f:
            pickle.dump(data, f)


def get_available_databases(base_directory: str) -> List[str]:
    """Get list of available databases in directory"""
    databases = []

    if not os.path.exists(base_directory):
        return databases

    for item in os.listdir(base_directory):
        item_path = os.path.join(base_directory, item)

        # Check for various database formats
        if os.path.isfile(item_path):
            if item.endswith(".gwb") or item.endswith(".pickle") or item.endswith(".db"):
                databases.append(os.path.splitext(item)[0])
        elif os.path.isdir(item_path):
            # Check if directory contains database files
            if any(f.endswith((".gwb", ".pickle", ".db")) for f in os.listdir(item_path)):
                databases.append(item)

    return sorted(databases)


def create_database_driver(database_path: str, driver_type: str = "pickle") -> DatabaseDriver:
    """Factory function to create appropriate database driver"""
    if driver_type == "pickle":
        return PickleDatabaseDriver(database_path)
    else:
        raise ValueError(f"Unknown database driver type: {driver_type}")


# Dummy classes for compatibility with original OCaml types
class Iper:
    """Person ID type for compatibility"""

    def __init__(self, value: int):
        self.value = value

    @classmethod
    def dummy(cls):
        return cls(0)

    def __eq__(self, other):
        return isinstance(other, Iper) and self.value == other.value

    def __hash__(self):
        return hash(self.value)

    def __repr__(self):
        return f"Iper({self.value})"


class Ifam:
    """Family ID type for compatibility"""

    def __init__(self, value: int):
        self.value = value

    @classmethod
    def dummy(cls):
        return cls(0)

    def __eq__(self, other):
        return isinstance(other, Ifam) and self.value == other.value

    def __hash__(self):
        return hash(self.value)

    def __repr__(self):
        return f"Ifam({self.value})"
