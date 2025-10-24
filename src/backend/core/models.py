"""
Modèles de domaine pour GenEWeb.

Ce module contient les dataclasses représentant les entités du domaine généalogique.
Ces modèles sont purs (sans dépendances externes) et immuables par défaut.
"""

from dataclasses import dataclass, field
from datetime import date as python_date
from typing import Dict, List, Optional

from .enums import (
    AccessLevel,
    BurialType,
    Calendar,
    DatePrecision,
    DeathType,
    DivorceType,
    EventType,
    MaritalStatus,
    MarriageType,
    Sex,
)

# ============================================================================
# Dates généalogiques
# ============================================================================


@dataclass(frozen=True)
class Date:
    """
    Représente une date généalogique avec précision variable.

    Exemples:
        Date(day=15, month=3, year=1950)  # 15/03/1950 (date exacte)
        Date(year=1950, precision=DatePrecision.ABOUT)  # ~1950
        Date(year=1950, precision=DatePrecision.BEFORE)  # <1950
    """

    year: Optional[int] = None
    month: Optional[int] = None
    day: Optional[int] = None
    precision: DatePrecision = DatePrecision.EXACT
    calendar: Calendar = Calendar.GREGORIAN
    text: Optional[str] = None  # Texte libre pour dates non structurées

    def __str__(self) -> str:
        """Représentation textuelle de la date."""
        if self.text:
            return self.text

        parts = []
        if self.day:
            parts.append(f"{self.day:02d}")
        if self.month:
            parts.append(f"{self.month:02d}")
        if self.year:
            parts.append(str(self.year))

        date_str = "/".join(parts) if parts else "?"

        if self.precision == DatePrecision.ABOUT:
            return f"~{date_str}"
        elif self.precision == DatePrecision.BEFORE:
            return f"<{date_str}"
        elif self.precision == DatePrecision.AFTER:
            return f">{date_str}"
        elif self.precision == DatePrecision.CIRCA:
            return f"ca. {date_str}"

        return date_str

    def is_complete(self) -> bool:
        """Vérifie si la date est complète (jour, mois, année)."""
        return self.day is not None and self.month is not None and self.year is not None

    def to_python_date(self) -> Optional[python_date]:
        """Convertit en date Python standard si possible."""
        if self.is_complete() and self.year is not None and self.month is not None and self.day is not None:
            return python_date(self.year, self.month, self.day)
        return None

    @classmethod
    def from_python_date(cls, d: python_date) -> "Date":
        """Crée une Date depuis une date Python standard."""
        return cls(year=d.year, month=d.month, day=d.day)


# ============================================================================
# Événements
# ============================================================================


@dataclass(frozen=True)
class Event:
    """
    Représente un événement de la vie d'une personne.

    Args:
        event_type: Type d'événement (naissance, décès, mariage, etc.)
        date: Date de l'événement
        place: Lieu de l'événement
        note: Note ou description de l'événement
        source: Source de l'information
    """

    event_type: EventType
    date: Optional[Date] = None
    place: Optional[str] = None
    note: Optional[str] = None
    source: Optional[str] = None

    def __str__(self) -> str:
        parts = [self.event_type.name]
        if self.date:
            parts.append(str(self.date))
        if self.place:
            parts.append(self.place)
        return " - ".join(parts)


# ============================================================================
# Personne
# ============================================================================


@dataclass
class Person:
    """
    Représente une personne dans l'arbre généalogique.

    Args:
        id: Identifiant unique de la personne
        first_name: Prénom
        surname: Nom de famille
        sex: Sexe
        birth_date: Date de naissance
        birth_place: Lieu de naissance
        baptism_date: Date de baptême
        baptism_place: Lieu de baptême
        death_date: Date de décès
        death_place: Lieu de décès
        death_type: Type de décès
        burial_date: Date de sépulture
        burial_place: Lieu de sépulture
        burial_type: Type de sépulture
        occupation: Profession
        notes: Notes supplémentaires
        sources: Sources documentaires
        public_name: Nom public (surnom)
        qualifiers: Qualificatifs (Jr, Sr, etc.)
        aliases: Alias ou surnoms
        titles: Titres de noblesse ou honorifiques
        related_persons: IDs des personnes liées (parents, conjoints, enfants)
        events: Liste des événements de la vie
        access_level: Niveau d'accès requis pour voir cette personne
    """

    id: str
    first_name: str
    surname: str
    sex: Sex = Sex.UNKNOWN

    # Naissance
    birth_date: Optional[Date] = None
    birth_place: Optional[str] = None

    # Baptême
    baptism_date: Optional[Date] = None
    baptism_place: Optional[str] = None

    # Décès
    death_date: Optional[Date] = None
    death_place: Optional[str] = None
    death_type: DeathType = DeathType.DONT_KNOW_IF_DEAD

    # Sépulture
    burial_date: Optional[Date] = None
    burial_place: Optional[str] = None
    burial_type: BurialType = BurialType.UNKNOWN_BURIAL

    # Informations supplémentaires
    occupation: Optional[str] = None
    notes: Optional[str] = None
    sources: Optional[str] = None

    # Noms alternatifs
    public_name: Optional[str] = None
    qualifiers: List[str] = field(default_factory=list)
    aliases: List[str] = field(default_factory=list)
    titles: List[str] = field(default_factory=list)

    # Relations familiales (compatibilité GeneWeb legacy)
    family_id: Optional[str] = None  # ID de la famille en tant qu'enfant
    family_ids: List[str] = field(default_factory=list)  # IDs des familles en tant que parent

    # Relations
    related_persons: Dict[str, List[int]] = field(default_factory=dict)

    # Événements
    events: List[Event] = field(default_factory=list)

    # Sécurité
    access_level: AccessLevel = AccessLevel.PUBLIC

    @property
    def last_name(self) -> str:
        """Alias pour surname (compatibilité)."""
        return self.surname

    def full_name(self) -> str:
        """Retourne le nom complet (prénom + nom)."""
        return f"{self.first_name} {self.surname}"

    def display_name(self) -> str:
        """Retourne le nom d'affichage (avec nom public si présent)."""
        if self.public_name:
            return f"{self.first_name} '{self.public_name}' {self.surname}"
        return self.full_name()

    def age_at_death(self) -> Optional[int]:
        """Calcule l'âge au décès si possible."""
        if not (self.birth_date and self.death_date):
            return None
        if not (self.birth_date.year and self.death_date.year):
            return None
        return self.death_date.year - self.birth_date.year

    def is_alive(self) -> bool:
        """Vérifie si la personne est probablement vivante."""
        return self.death_type in [DeathType.NOT_DEAD, DeathType.DONT_KNOW_IF_DEAD]

    def add_event(self, event: Event) -> None:
        """Ajoute un événement à la personne."""
        self.events.append(event)

    def get_events_by_type(self, event_type: EventType) -> List[Event]:
        """Récupère tous les événements d'un type donné."""
        return [e for e in self.events if e.event_type == event_type]


# ============================================================================
# Famille
# ============================================================================


@dataclass
class Family:
    """
    Représente une famille (union de deux personnes et leurs enfants).

    Args:
        id: Identifiant unique de la famille
        father_id: ID du père
        mother_id: ID de la mère
        children_ids: IDs des enfants
        marriage_date: Date de mariage
        marriage_place: Lieu de mariage
        marriage_type: Type de mariage
        divorce_date: Date de divorce
        divorce_type: Type de divorce
        marriage_note: Note sur le mariage
        marriage_source: Source sur le mariage
        witnesses: Témoins du mariage
    """

    id: str
    father_id: Optional[str] = None
    mother_id: Optional[str] = None
    children_ids: List[str] = field(default_factory=list)

    # Statut marital (nouveau champ unifié)
    marital_status: MaritalStatus = MaritalStatus.UNKNOWN

    # Mariage
    marriage_date: Optional[Date] = None
    marriage_place: Optional[str] = None
    marriage_type: MarriageType = MarriageType.MARRIED
    marriage_note: Optional[str] = None
    marriage_source: Optional[str] = None

    # Divorce
    divorce_date: Optional[Date] = None
    divorce_place: Optional[str] = None
    divorce_type: DivorceType = DivorceType.NOT_DIVORCED

    # Notes et sources
    notes: Optional[str] = None

    # Témoins et relations
    witnesses: List[str] = field(default_factory=list)

    def has_father(self) -> bool:
        """Vérifie si la famille a un père."""
        return self.father_id is not None

    def has_mother(self) -> bool:
        """Vérifie si la famille a une mère."""
        return self.mother_id is not None

    def has_children(self) -> bool:
        """Vérifie si la famille a des enfants."""
        return len(self.children_ids) > 0

    def number_of_children(self) -> int:
        """Retourne le nombre d'enfants."""
        return len(self.children_ids)

    def is_married(self) -> bool:
        """Vérifie si le couple est marié."""
        return self.marital_status == MaritalStatus.MARRIED or self.marriage_type == MarriageType.MARRIED

    def is_divorced(self) -> bool:
        """Vérifie si le couple est divorcé."""
        return self.marital_status == MaritalStatus.DIVORCED or self.divorce_type == DivorceType.DIVORCED

    def add_child(self, child_id: str) -> None:
        """Ajoute un enfant à la famille."""
        if child_id not in self.children_ids:
            self.children_ids.append(child_id)


# ============================================================================
# Note
# ============================================================================


@dataclass(frozen=True)
class Note:
    """
    Représente une note ou annotation.

    Args:
        id: Identifiant unique de la note
        content: Contenu de la note
        author: Auteur de la note
        created_at: Date de création
        category: Catégorie de la note
    """

    id: int
    content: str
    author: Optional[str] = None
    created_at: Optional[Date] = None
    category: Optional[str] = None


# ============================================================================
# Source
# ============================================================================


@dataclass(frozen=True)
class Source:
    """
    Représente une source documentaire.

    Args:
        id: Identifiant unique de la source
        title: Titre de la source
        author: Auteur de la source
        publication: Information de publication
        repository: Dépôt ou archive
        note: Note sur la source
    """

    id: int
    title: str
    author: Optional[str] = None
    publication: Optional[str] = None
    repository: Optional[str] = None
    note: Optional[str] = None
