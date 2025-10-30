"""
Enumérations pour le domaine GenEWeb.

Ce module définit les énumérations utilisées dans tout le système.
"""

from enum import Enum, auto


class Sex(Enum):
    """Sexe d'une personne."""

    MALE = "M"
    FEMALE = "F"
    UNKNOWN = "U"

    def __str__(self) -> str:
        return self.value


class EventType(Enum):
    """Types d'événements généalogiques."""

    BIRTH = auto()
    BAPTISM = auto()
    DEATH = auto()
    BURIAL = auto()
    CREMATION = auto()
    MARRIAGE = auto()
    DIVORCE = auto()
    ENGAGEMENT = auto()
    OCCUPATION = auto()
    RESIDENCE = auto()
    EMIGRATION = auto()
    IMMIGRATION = auto()
    MILITARY_SERVICE = auto()
    EDUCATION = auto()
    PROPERTY = auto()
    NOTE = auto()
    OTHER = auto()


class DatePrecision(Enum):
    """Précision d'une date généalogique."""

    EXACT = "exact"  # Date exacte (15/03/1950)
    ABOUT = "about"  # Vers (~1950)
    BEFORE = "before"  # Avant (<1950)
    AFTER = "after"  # Après (>1950)
    BETWEEN = "between"  # Entre (1950-1960)
    CIRCA = "circa"  # Circa (ca. 1950)
    UNKNOWN = "unknown"  # Date inconnue

    def __str__(self) -> str:
        return self.value


class Calendar(Enum):
    """Calendriers utilisés pour les dates."""

    GREGORIAN = "gregorian"  # Calendrier grégorien (défaut)
    JULIAN = "julian"  # Calendrier julien
    FRENCH = "french"  # Calendrier républicain français
    HEBREW = "hebrew"  # Calendrier hébraïque

    def __str__(self) -> str:
        return self.value


class RelationType(Enum):
    """Types de relations familiales."""

    BIOLOGICAL = "biological"
    ADOPTIVE = "adoptive"
    FOSTER = "foster"
    GODPARENT = "godparent"

    def __str__(self) -> str:
        return self.value


class MaritalStatus(Enum):
    """Statut marital d'une famille."""

    UNKNOWN = "UNKNOWN"
    MARRIED = "MARRIED"
    NOT_MARRIED = "NOT_MARRIED"
    DIVORCED = "DIVORCED"
    SEPARATED = "SEPARATED"
    WIDOWED = "WIDOWED"

    def __str__(self) -> str:
        return self.value


class MarriageType(Enum):
    """Types de mariages/unions."""

    MARRIED = "married"
    NOT_MARRIED = "not_married"
    ENGAGED = "engaged"
    NO_SEXES_CHECK = "no_sexes_check"
    NO_MENTION = "no_mention"
    NO_MARRIAGE = "no_marriage"

    def __str__(self) -> str:
        return self.value


class DivorceType(Enum):
    """Types de divorce."""

    NOT_DIVORCED = "not_divorced"
    DIVORCED = "divorced"
    SEPARATED = "separated"

    def __str__(self) -> str:
        return self.value


class DeathType(Enum):
    """État vital d'une personne."""

    NOT_DEAD = "not_dead"  # Vivant
    DEAD = "dead"  # Décédé
    DEAD_YOUNG = "dead_young"  # Décédé jeune
    DEAD_DONT_KNOW_WHEN = "dead_dont_know_when"  # Décédé (date inconnue)
    DONT_KNOW_IF_DEAD = "dont_know_if_dead"  # Statut inconnu
    OF_COURSE_DEAD = "of_course_dead"  # Certainement décédé

    def __str__(self) -> str:
        return self.value


class BurialType(Enum):
    """Types de sépulture."""

    UNKNOWN_BURIAL = "unknown"
    BURIED = "buried"
    CREMATED = "cremated"

    def __str__(self) -> str:
        return self.value


class AccessLevel(Enum):
    """Niveaux d'accès pour les utilisateurs."""

    PUBLIC = 0  # Accès public (personnes > 100 ans)
    FRIEND = 1  # Accès ami (personnes < 100 ans sans détails sensibles)
    WIZARD = 2  # Accès complet (administration)

    def __lt__(self, other):
        if isinstance(other, AccessLevel):
            return self.value < other.value
        return NotImplemented

    def __le__(self, other):
        if isinstance(other, AccessLevel):
            return self.value <= other.value
        return NotImplemented
