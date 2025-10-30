"""
Repository pour l'accès haut niveau aux données généalogiques.

Ce module implémente le pattern Repository pour fournir une API
métier pour manipuler les personnes et familles.
"""

from typing import Dict, List, Optional, cast

from ..core.enums import Sex
from ..core.exceptions import FamilyNotFoundError, PersonNotFoundError, ValidationError
from ..core.models import Family, Person
from ..utils.string_utils import fuzzy_match, normalize_string
from .base import DatabaseDriver


class Repository:
    """
    Repository pour accéder aux données généalogiques.

    Fournit une API haut niveau pour CRUD sur les personnes et familles,
    avec recherche, validation et gestion de cache.

    Attributes:
        driver: Driver de base de données utilisé
        _persons: Cache des personnes en mémoire
        _families: Cache des familles en mémoire
        _dirty: Flag indiquant si les données ont été modifiées

    Examples:
        >>> repo = Repository(PickleDriver(Path("data.pickle")))
        >>> person = repo.get_person("P123")
        >>> results = repo.search_persons("Dupont")
        >>> repo.add_person(person)
        >>> repo.save()
    """

    def __init__(self, driver: DatabaseDriver) -> None:
        """
        Initialise le repository avec un driver.

        Args:
            driver: Driver de base de données à utiliser

        Examples:
            >>> driver = PickleDriver(Path("data.pickle"))
            >>> repo = Repository(driver)
        """
        self.driver = driver
        self._persons: Dict[str, Person] = {}
        self._families: Dict[str, Family] = {}
        self._dirty = False

        # Charger les données si la base existe
        if self.driver.exists():
            self.load()

    def load(self) -> None:
        """
        Charge les données depuis le driver.

        Raises:
            DatabaseError: Si le chargement échoue

        Examples:
            >>> repo.load()
        """
        data = self.driver.load()
        self._persons = cast(Dict[str, Person], data.get("persons", {}))
        self._families = cast(Dict[str, Family], data.get("families", {}))
        self._dirty = False

    def save(self, create_backup: bool = True) -> None:
        """
        Sauvegarde les données via le driver.

        Args:
            create_backup: Si True, crée un backup avant de sauvegarder

        Raises:
            DatabaseError: Si la sauvegarde échoue

        Examples:
            >>> repo.save(create_backup=True)
        """
        self.driver.save(self._persons, self._families, create_backup)
        self._dirty = False

    def is_dirty(self) -> bool:
        """
        Indique si les données ont été modifiées.

        Returns:
            True si des modifications n'ont pas été sauvegardées

        Examples:
            >>> if repo.is_dirty():
            ...     repo.save()
        """
        return self._dirty

    # ==================== Personnes ====================

    def get_person(self, person_id: str) -> Person:
        """
        Récupère une personne par son ID.

        Args:
            person_id: Identifiant de la personne

        Returns:
            Person: La personne trouvée

        Raises:
            PersonNotFoundError: Si la personne n'existe pas

        Examples:
            >>> person = repo.get_person("P123")
            >>> print(person.full_name)
        """
        if person_id not in self._persons:
            raise PersonNotFoundError(person_id)
        return self._persons[person_id]

    def get_all_persons(self) -> Dict[str, Person]:
        """
        Récupère toutes les personnes.

        Returns:
            Dict: Dictionnaire {id: Person}

        Examples:
            >>> persons = repo.get_all_persons()
            >>> print(f"{len(persons)} personnes")
        """
        return self._persons.copy()

    def add_person(self, person: Person) -> None:
        """
        Ajoute une nouvelle personne.

        Args:
            person: Personne à ajouter

        Raises:
            ValidationError: Si l'ID existe déjà ou la personne est invalide

        Examples:
            >>> person = Person(id="P456", first_name="Jean", surname="Dupont")
            >>> repo.add_person(person)
        """
        if not person.id:
            raise ValidationError("Person must have an ID")

        if person.id in self._persons:
            raise ValidationError(f"Person {person.id} already exists")

        self._persons[person.id] = person
        self._dirty = True

    def update_person(self, person: Person) -> None:
        """
        Met à jour une personne existante.

        Args:
            person: Personne avec les nouvelles données

        Raises:
            PersonNotFoundError: Si la personne n'existe pas

        Examples:
            >>> person = repo.get_person("P123")
            >>> person.first_name = "Pierre"
            >>> repo.update_person(person)
        """
        if person.id not in self._persons:
            raise PersonNotFoundError(person.id)

        self._persons[person.id] = person
        self._dirty = True

    def delete_person(self, person_id: str) -> None:
        """
        Supprime une personne.

        Args:
            person_id: Identifiant de la personne

        Raises:
            PersonNotFoundError: Si la personne n'existe pas

        Examples:
            >>> repo.delete_person("P123")
        """
        if person_id not in self._persons:
            raise PersonNotFoundError(person_id)

        del self._persons[person_id]
        self._dirty = True

    def search_persons(
        self, query: str, search_in: Optional[List[str]] = None, fuzzy: bool = True, threshold: float = 0.8
    ) -> List[Person]:
        """
        Recherche des personnes par nom.

        Args:
            query: Chaîne de recherche
            search_in: Champs à rechercher (["first_name", "last_name", "public_name"])
            fuzzy: Si True, utilise la recherche floue
            threshold: Seuil de similarité pour fuzzy search (0.0 à 1.0)

        Returns:
            List[Person]: Liste des personnes correspondantes

        Examples:
            >>> results = repo.search_persons("Dupont")
            >>> results = repo.search_persons("Jean", search_in=["first_name"])
        """
        if search_in is None:
            search_in = ["first_name", "last_name", "public_name"]

        query_normalized = normalize_string(query)
        results = []

        for person in self._persons.values():
            for field in search_in:
                value = getattr(person, field, None)
                if value:
                    value_normalized = normalize_string(value)

                    if fuzzy:
                        if fuzzy_match(query_normalized, value_normalized, threshold):
                            results.append(person)
                            break
                    else:
                        if query_normalized in value_normalized:
                            results.append(person)
                            break

        return results

    def get_persons_by_name(
        self, first_name: Optional[str] = None, surname: Optional[str] = None, exact: bool = False
    ) -> List[Person]:
        """
        Recherche des personnes par prénom et/ou nom.

        Args:
            first_name: Prénom à rechercher
            surname: Nom à rechercher
            exact: Si True, recherche exacte (sensible à la casse)

        Returns:
            List[Person]: Liste des personnes correspondantes

        Examples:
            >>> persons = repo.get_persons_by_name(surname="Dupont")
            >>> persons = repo.get_persons_by_name("Jean", "Dupont", exact=True)
        """
        results = []

        for person in self._persons.values():
            match = True

            if first_name:
                if exact:
                    match = match and person.first_name == first_name
                else:
                    match = match and normalize_string(first_name) in normalize_string(person.first_name or "")

            if surname:
                if exact:
                    match = match and person.surname == surname
                else:
                    match = match and normalize_string(surname) in normalize_string(person.surname or "")

            if match:
                results.append(person)

        return results

    def get_persons_by_sex(self, sex: Sex) -> List[Person]:
        """
        Récupère toutes les personnes d'un sexe donné.

        Args:
            sex: Sexe recherché

        Returns:
            List[Person]: Liste des personnes du sexe spécifié

        Examples:
            >>> men = repo.get_persons_by_sex(Sex.MALE)
            >>> women = repo.get_persons_by_sex(Sex.FEMALE)
        """
        return [p for p in self._persons.values() if p.sex == sex]

    # ==================== Familles ====================

    def get_family(self, family_id: str) -> Family:
        """
        Récupère une famille par son ID.

        Args:
            family_id: Identifiant de la famille

        Returns:
            Family: La famille trouvée

        Raises:
            FamilyNotFoundError: Si la famille n'existe pas

        Examples:
            >>> family = repo.get_family("F123")
        """
        if family_id not in self._families:
            raise FamilyNotFoundError(family_id)
        return self._families[family_id]

    def get_all_families(self) -> Dict[str, Family]:
        """
        Récupère toutes les familles.

        Returns:
            Dict: Dictionnaire {id: Family}

        Examples:
            >>> families = repo.get_all_families()
        """
        return self._families.copy()

    def add_family(self, family: Family) -> None:
        """
        Ajoute une nouvelle famille.

        Args:
            family: Famille à ajouter

        Raises:
            ValidationError: Si l'ID existe déjà ou la famille est invalide

        Examples:
            >>> family = Family(id="F456", father_id="P1", mother_id="P2")
            >>> repo.add_family(family)
        """
        if not family.id:
            raise ValidationError("Family must have an ID")

        if family.id in self._families:
            raise ValidationError(f"Family {family.id} already exists")

        self._families[family.id] = family
        self._dirty = True

    def update_family(self, family: Family) -> None:
        """
        Met à jour une famille existante.

        Args:
            family: Famille avec les nouvelles données

        Raises:
            FamilyNotFoundError: Si la famille n'existe pas

        Examples:
            >>> family = repo.get_family("F123")
            >>> family.marriage_date = Date(year=2000)
            >>> repo.update_family(family)
        """
        if family.id not in self._families:
            raise FamilyNotFoundError(family.id)

        self._families[family.id] = family
        self._dirty = True

    def delete_family(self, family_id: str) -> None:
        """
        Supprime une famille.

        Args:
            family_id: Identifiant de la famille

        Raises:
            FamilyNotFoundError: Si la famille n'existe pas

        Examples:
            >>> repo.delete_family("F123")
        """
        if family_id not in self._families:
            raise FamilyNotFoundError(family_id)

        del self._families[family_id]
        self._dirty = True

    def get_person_families(self, person_id: str) -> List[Family]:
        """
        Récupère toutes les familles où une personne est parent.

        Args:
            person_id: Identifiant de la personne

        Returns:
            List[Family]: Liste des familles où la personne est parent

        Examples:
            >>> families = repo.get_person_families("P123")
        """
        return [f for f in self._families.values() if f.father_id == person_id or f.mother_id == person_id]

    def get_person_parents(self, person_id: str) -> tuple[Optional[Person], Optional[Person]]:
        """
        Récupère les parents d'une personne.

        Args:
            person_id: Identifiant de la personne

        Returns:
            Tuple (father, mother) - peut contenir None

        Examples:
            >>> father, mother = repo.get_person_parents("P123")
        """
        person = self.get_person(person_id)

        if not person.family_id:
            return (None, None)

        try:
            family = self.get_family(person.family_id)
            father = self.get_person(family.father_id) if family.father_id else None
            mother = self.get_person(family.mother_id) if family.mother_id else None
            return (father, mother)
        except (FamilyNotFoundError, PersonNotFoundError):
            return (None, None)

    def get_person_children(self, person_id: str) -> List[Person]:
        """
        Récupère tous les enfants d'une personne.

        Args:
            person_id: Identifiant de la personne

        Returns:
            List[Person]: Liste des enfants

        Examples:
            >>> children = repo.get_person_children("P123")
        """
        children = []
        families = self.get_person_families(person_id)

        for family in families:
            for child_id in family.children_ids:
                try:
                    children.append(self.get_person(child_id))
                except PersonNotFoundError:
                    pass  # Ignorer les références cassées

        return children

    def get_person_siblings(self, person_id: str) -> List[Person]:
        """
        Récupère les frères et sœurs d'une personne.

        Args:
            person_id: Identifiant de la personne

        Returns:
            List[Person]: Liste des frères et sœurs

        Examples:
            >>> siblings = repo.get_person_siblings("P123")
        """
        person = self.get_person(person_id)

        if not person.family_id:
            return []

        try:
            family = self.get_family(person.family_id)
            siblings = []

            for child_id in family.children_ids:
                if child_id != person_id:
                    try:
                        siblings.append(self.get_person(child_id))
                    except PersonNotFoundError:
                        pass

            return siblings
        except FamilyNotFoundError:
            return []

    # ==================== Statistiques ====================

    def get_statistics(self) -> Dict[str, int]:
        """
        Calcule des statistiques sur la base.

        Returns:
            Dict avec total_persons, total_families, male_count, female_count

        Examples:
            >>> stats = repo.get_statistics()
            >>> print(f"{stats['total_persons']} personnes")
        """
        male = sum(1 for p in self._persons.values() if p.sex == Sex.MALE)
        female = sum(1 for p in self._persons.values() if p.sex == Sex.FEMALE)
        unknown = sum(1 for p in self._persons.values() if p.sex == Sex.UNKNOWN)

        return {
            "total_persons": len(self._persons),
            "total_families": len(self._families),
            "male_count": male,
            "female_count": female,
            "unknown_sex_count": unknown,
        }

    def validate(self) -> tuple[bool, List[str]]:
        """
        Valide l'intégrité des données en mémoire.

        Returns:
            Tuple (is_valid, errors)

        Examples:
            >>> valid, errors = repo.validate()
            >>> if not valid:
            ...     for error in errors:
            ...         print(error)
        """
        # Valider les données en mémoire directement
        errors = []

        try:
            person_ids = set(self._persons.keys())
            family_ids = set(self._families.keys())

            # Vérifier les références des personnes vers les familles
            for person_id, person in self._persons.items():
                # Famille en tant qu'enfant
                if person.family_id and person.family_id not in family_ids:
                    errors.append(f"Person {person_id} references non-existent family {person.family_id}")

                # Familles en tant que parent
                for fam_id in person.family_ids:
                    if fam_id not in family_ids:
                        errors.append(f"Person {person_id} references non-existent family {fam_id}")

            # Vérifier les références des familles vers les personnes
            for family_id, family in self._families.items():
                # Parents
                if family.father_id and family.father_id not in person_ids:
                    errors.append(f"Family {family_id} references non-existent father {family.father_id}")
                if family.mother_id and family.mother_id not in person_ids:
                    errors.append(f"Family {family_id} references non-existent mother {family.mother_id}")

                # Enfants
                for child_id in family.children_ids:
                    if child_id not in person_ids:
                        errors.append(f"Family {family_id} references non-existent child {child_id}")

            return (len(errors) == 0, errors)

        except Exception as e:
            errors.append(f"Validation failed: {e}")
            return (False, errors)
