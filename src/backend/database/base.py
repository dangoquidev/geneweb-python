"""
Interface abstraite pour les drivers de base de données généalogiques.

Ce module définit le contrat que tous les drivers de base de données
doivent respecter pour assurer l'interchangeabilité.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from ..core.exceptions import DatabaseError
from ..core.models import Family, Person


class DatabaseDriver(ABC):
    """
    Interface abstraite pour les drivers de base de données.

    Définit les opérations CRUD de base que tout driver doit implémenter
    pour gérer une base de données généalogique.

    Attributes:
        db_path: Chemin vers le fichier de base de données

    Examples:
        >>> class MyDriver(DatabaseDriver):
        ...     def load(self):
        ...         # Implementation
        ...         pass
        >>> driver = MyDriver(Path("data.db"))
    """

    def __init__(self, db_path: Path) -> None:
        """
        Initialise le driver avec un chemin de base de données.

        Args:
            db_path: Chemin vers le fichier de base de données

        Raises:
            DatabaseError: Si le chemin est invalide
        """
        if not isinstance(db_path, Path):
            db_path = Path(db_path)
        self.db_path = db_path

    @abstractmethod
    def load(self) -> Dict[str, Dict[str, Union[Person, Family]]]:
        """
        Charge la base de données depuis le disque.

        Returns:
            Dict avec clés "persons" et "families", chaque valeur étant
            un dict {id: objet}

        Raises:
            DatabaseError: Si le chargement échoue
            FileNotFoundError: Si le fichier n'existe pas

        Examples:
            >>> data = driver.load()
            >>> persons = data["persons"]
            >>> families = data["families"]
        """

    @abstractmethod
    def save(self, persons: Dict[str, Person], families: Dict[str, Family], create_backup: bool = True) -> None:
        """
        Sauvegarde la base de données sur le disque.

        Args:
            persons: Dictionnaire des personnes {id: Person}
            families: Dictionnaire des familles {id: Family}
            create_backup: Si True, crée une sauvegarde avant d'écraser

        Raises:
            DatabaseError: Si la sauvegarde échoue

        Examples:
            >>> driver.save(persons, families, create_backup=True)
        """

    @abstractmethod
    def exists(self) -> bool:
        """
        Vérifie si la base de données existe.

        Returns:
            True si le fichier existe et est lisible

        Examples:
            >>> if driver.exists():
            ...     data = driver.load()
        """

    @abstractmethod
    def delete(self) -> None:
        """
        Supprime la base de données du disque.

        Raises:
            DatabaseError: Si la suppression échoue
            FileNotFoundError: Si le fichier n'existe pas

        Examples:
            >>> driver.delete()
        """

    @abstractmethod
    def get_metadata(self) -> Dict[str, Any]:
        """
        Récupère les métadonnées de la base de données.

        Returns:
            Dict contenant:
            - size: Taille du fichier en octets
            - modified: Date de dernière modification
            - person_count: Nombre de personnes
            - family_count: Nombre de familles

        Raises:
            DatabaseError: Si la lecture des métadonnées échoue
            FileNotFoundError: Si le fichier n'existe pas

        Examples:
            >>> meta = driver.get_metadata()
            >>> print(f"{meta['person_count']} personnes")
        """

    @abstractmethod
    def backup(self, backup_path: Optional[Path] = None) -> Path:
        """
        Crée une sauvegarde de la base de données.

        Args:
            backup_path: Chemin de destination (auto si None)

        Returns:
            Path: Chemin du fichier de sauvegarde créé

        Raises:
            DatabaseError: Si la sauvegarde échoue
            FileNotFoundError: Si la base n'existe pas

        Examples:
            >>> backup_file = driver.backup()
            >>> print(f"Backup: {backup_file}")
        """

    @abstractmethod
    def restore(self, backup_path: Path) -> None:
        """
        Restaure la base de données depuis une sauvegarde.

        Args:
            backup_path: Chemin du fichier de sauvegarde

        Raises:
            DatabaseError: Si la restauration échoue
            FileNotFoundError: Si le backup n'existe pas

        Examples:
            >>> driver.restore(Path("data.backup"))
        """

    @abstractmethod
    def validate(self) -> tuple[bool, List[str]]:
        """
        Valide l'intégrité de la base de données.

        Vérifie:
        - Références entre personnes et familles
        - Cohérence des relations parent/enfant
        - Unicité des IDs

        Returns:
            Tuple (is_valid, errors) où errors est la liste des problèmes

        Examples:
            >>> valid, errors = driver.validate()
            >>> if not valid:
            ...     for error in errors:
            ...         print(f"Erreur: {error}")
        """

    def get_statistics(self) -> Dict[str, int]:
        """
        Calcule des statistiques sur la base de données.

        Returns:
            Dict avec clés:
            - total_persons: Nombre total de personnes
            - total_families: Nombre total de familles
            - male_count: Nombre d'hommes
            - female_count: Nombre de femmes
            - unknown_sex_count: Nombre de personnes sans sexe défini

        Raises:
            DatabaseError: Si le calcul échoue

        Examples:
            >>> stats = driver.get_statistics()
            >>> print(f"{stats['male_count']} hommes")
        """
        try:
            data = self.load()
            persons = data.get("persons", {})
            families = data.get("families", {})

            from ..core.enums import Sex
            from ..core.models import Person

            male = sum(1 for p in persons.values() if isinstance(p, Person) and p.sex == Sex.MALE)
            female = sum(1 for p in persons.values() if isinstance(p, Person) and p.sex == Sex.FEMALE)
            unknown = sum(1 for p in persons.values() if isinstance(p, Person) and p.sex == Sex.UNKNOWN)

            return {
                "total_persons": len(persons),
                "total_families": len(families),
                "male_count": male,
                "female_count": female,
                "unknown_sex_count": unknown,
            }
        except Exception as e:
            raise DatabaseError(str(self.db_path), f"Failed to compute statistics: {e}")
