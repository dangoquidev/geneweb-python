"""
Utilitaires de gestion de dates généalogiques pour GenEWeb.

Ce module fournit des fonctions pour parser, formater et manipuler
les dates généalogiques avec leurs différentes précisions et formats.
"""

import re
from datetime import date as python_date
from datetime import datetime
from typing import Optional, Tuple

from ..core.enums import DatePrecision
from ..core.exceptions import DateValidationError
from ..core.models import Date

# Patterns de reconnaissance de dates
DATE_PATTERNS = {
    # Format complet: 15/03/1950, 15-03-1950, 15.03.1950
    "full": r"(\d{1,2})[\/.\\-](\d{1,2})[\/.\\-](\d{4})",
    # Mois et année: 03/1950, 03-1950
    "month_year": r"(\d{1,2})[\/-](\d{4})",
    # Année seule: 1950
    "year": r"(\d{4})",
    # Circa/environ: ca 1950, circa 1950, ~1950
    "circa": r"(?:ca\.?|circa|~)\s*(\d{4})",
    # Avant: avant 1950, <1950
    "before": r"(?:avant|before|<)\s*(\d{4})",
    # Après: après 1950, >1950
    "after": r"(?:après|after|>)\s*(\d{4})",
}


def parse_date(date_string: str) -> Optional[Date]:
    """
    Parse une chaîne de date en objet Date.

    Supporte de nombreux formats:
    - Dates complètes: "15/03/1950", "15-03-1950"
    - Mois et année: "03/1950"
    - Année seule: "1950"
    - Dates approximatives: "~1950", "ca 1950", "circa 1950"
    - Dates relatives: "avant 1950", "<1950", "après 1950", ">1950"

    Args:
        date_string: Chaîne représentant une date

    Returns:
        Date: Objet Date ou None si parsing impossible

    Raises:
        DateValidationError: Si la date est invalide

    Examples:
        >>> parse_date("15/03/1950")
        Date(day=15, month=3, year=1950, precision=DatePrecision.EXACT)
        >>> parse_date("~1950")
        Date(year=1950, precision=DatePrecision.ABOUT)
    """
    if not date_string:
        return None

    date_string = date_string.strip()

    # Circa/environ
    match = re.search(DATE_PATTERNS["circa"], date_string, re.IGNORECASE)
    if match:
        year = int(match.group(1))
        return Date(year=year, precision=DatePrecision.CIRCA)

    # Avant
    match = re.search(DATE_PATTERNS["before"], date_string, re.IGNORECASE)
    if match:
        year = int(match.group(1))
        return Date(year=year, precision=DatePrecision.BEFORE)

    # Après
    match = re.search(DATE_PATTERNS["after"], date_string, re.IGNORECASE)
    if match:
        year = int(match.group(1))
        return Date(year=year, precision=DatePrecision.AFTER)

    # Date complète
    match = re.search(DATE_PATTERNS["full"], date_string)
    if match:
        day, month, year = int(match.group(1)), int(match.group(2)), int(match.group(3))
        if not is_valid_date(day, month, year):
            raise DateValidationError(date_string, f"Invalid date: {day}/{month}/{year}")
        return Date(day=day, month=month, year=year, precision=DatePrecision.EXACT)

    # Mois et année
    match = re.search(DATE_PATTERNS["month_year"], date_string)
    if match:
        month, year = int(match.group(1)), int(match.group(2))
        if not (1 <= month <= 12):
            raise DateValidationError(date_string, f"Invalid month: {month}")
        return Date(month=month, year=year, precision=DatePrecision.EXACT)

    # Année seule
    match = re.search(DATE_PATTERNS["year"], date_string)
    if match:
        year = int(match.group(1))
        return Date(year=year, precision=DatePrecision.EXACT)

    # Si aucun pattern ne correspond, retourner date avec texte libre
    return Date(text=date_string, precision=DatePrecision.UNKNOWN)


def format_date(date: Date, format_str: str = "long") -> str:
    """
    Formate une date en chaîne lisible.

    Args:
        date: Date à formater
        format_str: Format de sortie ("short", "long", "iso")

    Returns:
        str: Date formatée

    Examples:
        >>> d = Date(day=15, month=3, year=1950)
        >>> format_date(d, "long")
        '15 mars 1950'
        >>> format_date(d, "iso")
        '1950-03-15'
    """
    if not date:
        return ""

    # Si date avec texte libre
    if date.text:
        return date.text

    if format_str == "iso":
        return format_date_iso(date)
    elif format_str == "long":
        return format_date_long(date)
    else:  # short
        return str(date)


def format_date_iso(date: Date) -> str:
    """
    Formate une date au format ISO (YYYY-MM-DD).

    Args:
        date: Date à formater

    Returns:
        str: Date au format ISO

    Examples:
        >>> d = Date(day=15, month=3, year=1950)
        >>> format_date_iso(d)
        '1950-03-15'
    """
    if not date.year:
        return ""

    parts = [str(date.year)]

    if date.month:
        parts.append(f"{date.month:02d}")
        if date.day:
            parts.append(f"{date.day:02d}")

    date_str = "-".join(parts)

    # Ajouter précision si nécessaire
    if date.precision == DatePrecision.ABOUT:
        return f"~{date_str}"
    elif date.precision == DatePrecision.BEFORE:
        return f"<{date_str}"
    elif date.precision == DatePrecision.AFTER:
        return f">{date_str}"

    return date_str


def format_date_long(date: Date) -> str:
    """
    Formate une date en format long lisible.

    Args:
        date: Date à formater

    Returns:
        str: Date en format long

    Examples:
        >>> d = Date(day=15, month=3, year=1950)
        >>> format_date_long(d)
        '15 mars 1950'
    """
    month_names = {
        1: "janvier",
        2: "février",
        3: "mars",
        4: "avril",
        5: "mai",
        6: "juin",
        7: "juillet",
        8: "août",
        9: "septembre",
        10: "octobre",
        11: "novembre",
        12: "décembre",
    }

    if not date.year:
        return ""

    parts = []

    if date.day:
        parts.append(str(date.day))

    if date.month:
        parts.append(month_names.get(date.month, str(date.month)))

    parts.append(str(date.year))

    date_str = " ".join(parts)

    # Ajouter préfixe selon précision
    if date.precision == DatePrecision.ABOUT:
        return f"vers {date_str}"
    elif date.precision == DatePrecision.CIRCA:
        return f"circa {date_str}"
    elif date.precision == DatePrecision.BEFORE:
        return f"avant {date_str}"
    elif date.precision == DatePrecision.AFTER:
        return f"après {date_str}"

    return date_str


def is_valid_date(day: int, month: int, year: int) -> bool:
    """
    Vérifie si une date est valide.

    Args:
        day: Jour (1-31)
        month: Mois (1-12)
        year: Année

    Returns:
        bool: True si la date est valide

    Examples:
        >>> is_valid_date(31, 2, 2000)
        False
        >>> is_valid_date(29, 2, 2000)
        True
    """
    try:
        python_date(year, month, day)
        return True
    except ValueError:
        return False


def calculate_age(birth_date: Date, reference_date: Optional[Date] = None) -> Optional[int]:
    """
    Calcule l'âge d'une personne à partir de sa date de naissance.

    Args:
        birth_date: Date de naissance
        reference_date: Date de référence (aujourd'hui par défaut)

    Returns:
        int: Âge en années, ou None si calcul impossible

    Examples:
        >>> birth = Date(year=1950)
        >>> ref = Date(year=2020)
        >>> calculate_age(birth, ref)
        70
    """
    if not birth_date or not birth_date.year:
        return None

    if reference_date is None:
        ref_year = datetime.now().year
    else:
        ref_year = reference_date.year if reference_date.year else datetime.now().year

    age = ref_year - birth_date.year

    # Ajuster si on a les mois et jours
    if birth_date.month and reference_date and reference_date.month:
        if reference_date.month < birth_date.month:
            age -= 1
        elif reference_date.month == birth_date.month:
            if birth_date.day and reference_date.day:
                if reference_date.day < birth_date.day:
                    age -= 1

    return age


def compare_dates(date1: Date, date2: Date) -> int:
    """
    Compare deux dates.

    Args:
        date1: Première date
        date2: Deuxième date

    Returns:
        int: -1 si date1 < date2, 0 si égales, 1 si date1 > date2

    Examples:
        >>> d1 = Date(year=1950)
        >>> d2 = Date(year=1960)
        >>> compare_dates(d1, d2)
        -1
    """

    # Convertir en tuples comparables
    def to_comparable(d: Date) -> Tuple[int, int, int]:
        return (d.year or 0, d.month or 0, d.day or 0)

    t1 = to_comparable(date1)
    t2 = to_comparable(date2)

    if t1 < t2:
        return -1
    elif t1 > t2:
        return 1
    else:
        return 0


def date_range(start: Date, end: Date) -> str:
    """
    Formate une période entre deux dates.

    Args:
        start: Date de début
        end: Date de fin

    Returns:
        str: Période formatée

    Examples:
        >>> d1 = Date(year=1950)
        >>> d2 = Date(year=1960)
        >>> date_range(d1, d2)
        '1950 - 1960'
    """
    if not start and not end:
        return ""
    elif not end:
        return f"{format_date_long(start)} -"
    elif not start:
        return f"- {format_date_long(end)}"
    else:
        return f"{format_date_long(start)} - {format_date_long(end)}"


def is_date_complete(date: Date) -> bool:
    """
    Vérifie si une date est complète (jour, mois, année).

    Args:
        date: Date à vérifier

    Returns:
        bool: True si la date est complète
    """
    return date.is_complete() if date else False


def get_current_date() -> Date:
    """
    Obtient la date actuelle.

    Returns:
        Date: Date du jour
    """
    today = datetime.now()
    return Date(day=today.day, month=today.month, year=today.year, precision=DatePrecision.EXACT)
