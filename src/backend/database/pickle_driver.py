"""
Driver de base de données utilisant le format Pickle.

Ce module implémente DatabaseDriver pour le format Pickle,
permettant de sauvegarder et charger des bases généalogiques.
"""

import pickle
import shutil
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, cast

from ..core.exceptions import DatabaseCorruptedError, DatabaseError
from ..core.models import Date, DatePrecision, Family, Person, Sex
from .base import DatabaseDriver


def _migrate_dict_to_person(data: dict) -> Person:
    """
    Convert a dictionary to a Person object (for legacy database compatibility).

    Args:
        data: Dictionary containing person data.

    Returns:
        Person object.
    """
    # Extract ID (can be string or dict with 'id' key)
    person_id = data.get("key_index", "")
    if isinstance(person_id, dict):
        person_id = person_id.get("id", "")

    # Extract sex (can be string or dict with 'value' key)
    sex = data.get("sex")
    if isinstance(sex, dict):
        sex_value = sex.get("value", "").upper()
    elif isinstance(sex, str):
        sex_value = sex.upper() if sex else None
    else:
        sex_value = None

    # Map various formats to Sex enum values
    if sex_value:
        if sex_value in ["MALE", "M", "MAN", "BOY"]:
            sex = Sex.MALE
        elif sex_value in ["FEMALE", "F", "WOMAN", "GIRL"]:
            sex = Sex.FEMALE
        elif sex_value in ["UNKNOWN", "U", "OTHER", "NON-BINARY"]:
            sex = Sex.UNKNOWN
        else:
            sex = Sex.UNKNOWN  # Default to unknown
    else:
        sex = None

    # Convert nested structures
    birth_date = None
    if data.get("birth_date"):
        bd = data["birth_date"]
        if isinstance(bd, dict):
            birth_date = Date(
                year=bd.get("year"),
                month=bd.get("month"),
                day=bd.get("day"),
                text=bd.get("text"),
                precision=bd.get("precision") or DatePrecision.EXACT,
            )
        elif isinstance(bd, Date):
            birth_date = bd

    death_date = None
    if data.get("death"):
        dd = data["death"]
        if isinstance(dd, dict):
            death_date = Date(
                year=dd.get("year"),
                month=dd.get("month"),
                day=dd.get("day"),
                text=dd.get("text"),
                precision=dd.get("precision") or DatePrecision.EXACT,
            )
        elif isinstance(dd, Date):
            death_date = dd

    return Person(
        id=person_id,
        first_name=data.get("first_name", ""),
        surname=data.get("surname", ""),
        sex=sex or Sex.UNKNOWN,
        birth_date=birth_date,
        birth_place=data.get("birth_place"),
        death_date=death_date,
        death_place=data.get("death_place"),
        public_name=data.get("public_name"),
        occupation=data.get("occupation"),
        notes=data.get("notes"),
        sources=data.get("sources"),
    )


def _migrate_dict_to_family(data: dict) -> Family:
    """
    Convert a dictionary to a Family object (for legacy database compatibility).

    Args:
        data: Dictionary containing family data.

    Returns:
        Family object.
    """
    # Extract ID (can be string or dict with 'id' key)
    family_id = data.get("key_index", "")
    if isinstance(family_id, dict):
        family_id = family_id.get("id", "")

    # Extract parent IDs (can be string or dict)
    father_id = data.get("father_id")
    if isinstance(father_id, dict):
        father_id = father_id.get("id")

    mother_id = data.get("mother_id")
    if isinstance(mother_id, dict):
        mother_id = mother_id.get("id")

    # Extract children IDs (list of strings or dicts)
    children_ids = data.get("children_ids", [])
    if children_ids:
        children_ids = [child_id.get("id") if isinstance(child_id, dict) else child_id for child_id in children_ids]

    marriage_date = None
    if data.get("marriage_date"):
        md = data["marriage_date"]
        if isinstance(md, dict):
            marriage_date = Date(
                year=md.get("year"),
                month=md.get("month"),
                day=md.get("day"),
                text=md.get("text"),
                precision=md.get("precision") or DatePrecision.EXACT,
            )
        elif isinstance(md, Date):
            marriage_date = md

    divorce_date = None
    if data.get("divorce_date"):
        dd = data["divorce_date"]
        if isinstance(dd, dict):
            divorce_date = Date(
                year=dd.get("year"),
                month=dd.get("month"),
                day=dd.get("day"),
                text=dd.get("text"),
                precision=dd.get("precision") or DatePrecision.EXACT,
            )
        elif isinstance(dd, Date):
            divorce_date = dd

    return Family(
        id=family_id,
        father_id=father_id,
        mother_id=mother_id,
        children_ids=children_ids,
        marriage_date=marriage_date,
        marriage_place=data.get("marriage_place"),
        divorce_date=divorce_date,
        divorce_place=data.get("divorce_place"),
        marriage_note=data.get("marriage_note"),
        marriage_source=data.get("marriage_source"),
        # Note: 'notes' and 'sources' fields don't exist in Family model
    )


class PickleDriver(DatabaseDriver):
    """
    Driver de base de données utilisant le format Pickle.

    Gère la sérialisation/désérialisation des données généalogiques
    avec support de backup, validation et thread-safety.

    Attributes:
        db_path: Chemin vers le fichier Pickle
        _lock: Lock pour thread-safety

    Examples:
        >>> driver = PickleDriver(Path("data/ma_famille.pickle"))
        >>> if driver.exists():
        ...     data = driver.load()
        >>> driver.save(persons, families)
    """

    def __init__(self, db_path: Path) -> None:
        """
        Initialise le driver Pickle.

        Args:
            db_path: Chemin vers le fichier .pickle

        Raises:
            DatabaseError: Si le chemin est invalide
        """
        super().__init__(db_path)
        self._lock = threading.RLock()

        # Vérifier l'extension
        if self.db_path.suffix != ".pickle":
            raise DatabaseError(str(self.db_path), "Pickle driver requires .pickle extension")

    def load(self) -> Dict[str, Dict[str, Union[Person, Family]]]:
        """
        Charge la base de données depuis le fichier Pickle.

        Returns:
            Dict avec clés "persons" et "families"

        Raises:
            DatabaseError: Si le chargement échoue
            FileNotFoundError: Si le fichier n'existe pas
            DatabaseCorruptedError: Si le fichier est corrompu

        Examples:
            >>> data = driver.load()
            >>> print(f"{len(data['persons'])} personnes")
        """
        with self._lock:
            if not self.exists():
                raise FileNotFoundError(f"Database file not found: {self.db_path}")

            try:
                with open(self.db_path, "rb") as f:
                    data = pickle.load(f)

                # Validation de la structure
                if not isinstance(data, dict):
                    raise DatabaseCorruptedError(str(self.db_path), "Database must be a dictionary")

                if "persons" not in data or "families" not in data:
                    raise DatabaseCorruptedError(
                        str(self.db_path), "Database must contain 'persons' and 'families' keys"
                    )

                # Migrate legacy dict format to Person/Family objects if needed
                persons: Dict[str, Person] = {}
                for person_id, person_data in data.get("persons", {}).items():
                    if isinstance(person_data, dict):
                        # Legacy format: convert dict to Person
                        persons[str(person_id)] = _migrate_dict_to_person(person_data)
                    elif isinstance(person_data, Person):
                        # Already a Person object
                        persons[str(person_id)] = person_data
                    else:
                        raise DatabaseCorruptedError(
                            str(self.db_path), f"Invalid person data type: {type(person_data)}"
                        )

                families: Dict[str, Family] = {}
                for family_id, family_data in data.get("families", {}).items():
                    if isinstance(family_data, dict):
                        # Legacy format: convert dict to Family
                        families[str(family_id)] = _migrate_dict_to_family(family_data)
                    elif isinstance(family_data, Family):
                        # Already a Family object
                        families[str(family_id)] = family_data
                    else:
                        raise DatabaseCorruptedError(
                            str(self.db_path), f"Invalid family data type: {type(family_data)}"
                        )

                # Return migrated data
                return {
                    "persons": cast(Dict[str, Union[Person, Family]], persons),
                    "families": cast(Dict[str, Union[Person, Family]], families),
                }

            except pickle.UnpicklingError as e:
                raise DatabaseCorruptedError(str(self.db_path), f"Failed to unpickle: {e}")
            except DatabaseError:
                # Re-raise DatabaseError et ses sous-classes telles quelles
                raise
            except Exception as e:
                raise DatabaseError(str(self.db_path), f"Failed to load database: {e}")

    def save(self, persons: Dict[str, Person], families: Dict[str, Family], create_backup: bool = True) -> None:
        """
        Sauvegarde la base de données au format Pickle.

        Args:
            persons: Dictionnaire des personnes {id: Person}
            families: Dictionnaire des familles {id: Family}
            create_backup: Si True, crée un backup avant d'écraser

        Raises:
            DatabaseError: Si la sauvegarde échoue

        Examples:
            >>> driver.save(persons, families, create_backup=True)
        """
        with self._lock:
            # Créer le répertoire parent si nécessaire
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

            # Backup automatique si demandé et fichier existe
            if create_backup and self.exists():
                try:
                    self.backup()
                except Exception as e:
                    # Log mais ne bloque pas la sauvegarde
                    print(f"Warning: Backup failed: {e}")

            # Préparer les données
            data = {
                "persons": persons,
                "families": families,
                "metadata": {
                    "saved_at": datetime.now().isoformat(),
                    "version": "1.0",
                },
            }

            # Sauvegarder avec pickle
            try:
                # Écrire dans un fichier temporaire d'abord
                temp_path = self.db_path.with_suffix(".tmp")
                with open(temp_path, "wb") as f:
                    pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)

                # Remplacer l'ancien fichier atomiquement
                temp_path.replace(self.db_path)

            except Exception as e:
                raise DatabaseError(str(self.db_path), f"Failed to save database: {e}")

    def exists(self) -> bool:
        """
        Vérifie si la base de données existe.

        Returns:
            True si le fichier existe et est lisible

        Examples:
            >>> if driver.exists():
            ...     data = driver.load()
        """
        return self.db_path.exists() and self.db_path.is_file()

    def delete(self) -> None:
        """
        Supprime la base de données du disque.

        Raises:
            DatabaseError: Si la suppression échoue
            FileNotFoundError: Si le fichier n'existe pas

        Examples:
            >>> driver.delete()
        """
        with self._lock:
            if not self.exists():
                raise FileNotFoundError(f"Database file not found: {self.db_path}")

            try:
                self.db_path.unlink()
            except Exception as e:
                raise DatabaseError(str(self.db_path), f"Failed to delete database: {e}")

    def get_metadata(self) -> Dict[str, Any]:
        """
        Récupère les métadonnées de la base de données.

        Returns:
            Dict avec size, modified, person_count, family_count

        Raises:
            DatabaseError: Si la lecture des métadonnées échoue
            FileNotFoundError: Si le fichier n'existe pas

        Examples:
            >>> meta = driver.get_metadata()
            >>> print(f"Size: {meta['size']} bytes")
        """
        if not self.exists():
            raise FileNotFoundError(f"Database file not found: {self.db_path}")

        try:
            stat = self.db_path.stat()
            data = self.load()

            return {
                "size": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime),
                "person_count": len(data.get("persons", {})),
                "family_count": len(data.get("families", {})),
                "saved_at": data.get("metadata", {}).get("saved_at"),
                "version": data.get("metadata", {}).get("version"),
            }
        except Exception as e:
            raise DatabaseError(str(self.db_path), f"Failed to get metadata: {e}")

    def get_info(self) -> Dict[str, Any]:
        """
        Récupère les informations sur la base de données.
        Alias de get_metadata() avec format compatible API.

        Returns:
            Dict avec persons_count, families_count, version, created_date, modified_date

        Examples:
            >>> info = driver.get_info()
            >>> print(f"Persons: {info['persons_count']}")
        """
        meta = self.get_metadata()
        stat = self.db_path.stat()

        return {
            "persons_count": meta.get("person_count", 0),
            "families_count": meta.get("family_count", 0),
            "version": meta.get("version") or "1.0",  # Default if None
            "created_date": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "modified_date": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        }

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
            >>> print(f"Backup created: {backup_file}")
        """
        with self._lock:
            if not self.exists():
                raise FileNotFoundError(f"Database file not found: {self.db_path}")

            # Générer le nom du backup si non fourni
            if backup_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = self.db_path.with_suffix(f".backup_{timestamp}")

            try:
                shutil.copy2(self.db_path, backup_path)
                return backup_path
            except Exception as e:
                raise DatabaseError(str(self.db_path), f"Failed to create backup: {e}")

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
        with self._lock:
            if not backup_path.exists():
                raise FileNotFoundError(f"Backup file not found: {backup_path}")

            try:
                # Backup du fichier actuel avant de restaurer
                if self.exists():
                    safety_backup = self.db_path.with_suffix(".safety_backup")
                    shutil.copy2(self.db_path, safety_backup)

                # Restaurer
                shutil.copy2(backup_path, self.db_path)

            except Exception as e:
                raise DatabaseError(str(self.db_path), f"Failed to restore from backup: {e}")

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
            ...     print(f"{len(errors)} erreurs trouvées")
        """
        errors = []

        try:
            data = self.load()
            persons_dict = data.get("persons", {})
            families_dict = data.get("families", {})

            # Type narrowing: extract only Person objects
            persons: Dict[str, Person] = {pid: p for pid, p in persons_dict.items() if isinstance(p, Person)}
            families: Dict[str, Family] = {fid: f for fid, f in families_dict.items() if isinstance(f, Family)}

            # Vérifier unicité des IDs (implicite avec dict, mais on vérifie quand même)
            person_ids = set(persons.keys())
            family_ids = set(families.keys())

            # Vérifier les références des personnes vers les familles
            for person_id, person in persons.items():
                # Famille en tant qu'enfant
                if person.family_id and person.family_id not in family_ids:
                    errors.append(f"Person {person_id} references non-existent family {person.family_id}")

                # Familles en tant que parent
                for fam_id in person.family_ids:
                    if fam_id not in family_ids:
                        errors.append(f"Person {person_id} references non-existent family {fam_id}")

            # Vérifier les références des familles vers les personnes
            for family_id, family in families.items():
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
