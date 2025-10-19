"""
Tests pour utils/date_utils.py.

Tests des fonctions de gestion de dates généalogiques.
"""

from datetime import date as python_date

import pytest

from backend.core.enums import DatePrecision
from backend.core.exceptions import DateValidationError
from backend.core.models import Date
from backend.utils.date_utils import (
    calculate_age,
    compare_dates,
    date_range,
    format_date,
    format_date_iso,
    format_date_long,
    get_current_date,
    is_valid_date,
    parse_date,
)


class TestParseDate:
    """Tests pour parse_date."""

    def test_parse_full_date(self):
        """Test parsing date complète."""
        d = parse_date("15/03/1950")
        assert d.day == 15
        assert d.month == 3
        assert d.year == 1950
        assert d.precision == DatePrecision.EXACT

    def test_parse_date_with_dashes(self):
        """Test parsing avec tirets."""
        d = parse_date("15-03-1950")
        assert d.day == 15
        assert d.month == 3
        assert d.year == 1950

    def test_parse_month_year(self):
        """Test parsing mois et année."""
        d = parse_date("03/1950")
        assert d.month == 3
        assert d.year == 1950
        assert d.day is None

    def test_parse_year_only(self):
        """Test parsing année seule."""
        d = parse_date("1950")
        assert d.year == 1950
        assert d.month is None
        assert d.day is None

    def test_parse_circa_date(self):
        """Test parsing date circa."""
        d = parse_date("ca 1950")
        assert d.year == 1950
        assert d.precision == DatePrecision.CIRCA

        d = parse_date("circa 1950")
        assert d.precision == DatePrecision.CIRCA

        d = parse_date("~1950")
        assert d.precision == DatePrecision.CIRCA

    def test_parse_before_date(self):
        """Test parsing date avant."""
        d = parse_date("avant 1950")
        assert d.year == 1950
        assert d.precision == DatePrecision.BEFORE

        d = parse_date("<1950")
        assert d.precision == DatePrecision.BEFORE

    def test_parse_after_date(self):
        """Test parsing date après."""
        d = parse_date("après 1950")
        assert d.year == 1950
        assert d.precision == DatePrecision.AFTER

        d = parse_date(">1950")
        assert d.precision == DatePrecision.AFTER

    def test_parse_invalid_date(self):
        """Test parsing date invalide."""
        with pytest.raises(DateValidationError):
            parse_date("31/02/2000")  # 31 février n'existe pas

    def test_parse_empty(self):
        """Test parsing chaîne vide."""
        assert parse_date("") is None
        assert parse_date(None) is None

    def test_parse_free_text(self):
        """Test parsing texte libre - extrait l'année même avec texte."""
        # parse_date extrait intelligemment l'année même avec texte descriptif
        d = parse_date("Printemps 1950")
        assert d.year == 1950
        assert d.month is None
        assert d.day is None
        assert d.precision == DatePrecision.EXACT

        # Vrai texte libre sans année reconnaissable
        d2 = parse_date("Date inconnue")
        assert d2.text == "Date inconnue"
        assert d2.precision == DatePrecision.UNKNOWN


class TestFormatDate:
    """Tests pour format_date."""

    def test_format_date_short(self):
        """Test formatage court."""
        d = Date(day=15, month=3, year=1950)
        assert format_date(d, "short") == "15/03/1950"

    def test_format_date_long(self):
        """Test formatage long."""
        d = Date(day=15, month=3, year=1950)
        result = format_date(d, "long")
        assert "15" in result
        assert "mars" in result
        assert "1950" in result

    def test_format_date_iso(self):
        """Test formatage ISO."""
        d = Date(day=15, month=3, year=1950)
        assert format_date(d, "iso") == "1950-03-15"

    def test_format_date_with_text(self):
        """Test formatage date avec texte."""
        d = Date(text="Printemps 1950")
        assert format_date(d) == "Printemps 1950"


class TestFormatDateISO:
    """Tests pour format_date_iso."""

    def test_format_iso_complete(self):
        """Test ISO date complète."""
        d = Date(day=15, month=3, year=1950)
        assert format_date_iso(d) == "1950-03-15"

    def test_format_iso_year_month(self):
        """Test ISO année et mois."""
        d = Date(month=3, year=1950)
        assert format_date_iso(d) == "1950-03"

    def test_format_iso_year_only(self):
        """Test ISO année seule."""
        d = Date(year=1950)
        assert format_date_iso(d) == "1950"

    def test_format_iso_with_precision(self):
        """Test ISO avec précision."""
        d = Date(year=1950, precision=DatePrecision.ABOUT)
        assert format_date_iso(d) == "~1950"


class TestFormatDateLong:
    """Tests pour format_date_long."""

    def test_format_long_complete(self):
        """Test format long complet."""
        d = Date(day=15, month=3, year=1950)
        result = format_date_long(d)
        assert result == "15 mars 1950"

    def test_format_long_month_year(self):
        """Test format long mois et année."""
        d = Date(month=3, year=1950)
        result = format_date_long(d)
        assert "mars" in result
        assert "1950" in result

    def test_format_long_year_only(self):
        """Test format long année seule."""
        d = Date(year=1950)
        assert format_date_long(d) == "1950"

    def test_format_long_with_precision_about(self):
        """Test format long avec précision 'environ'."""
        d = Date(year=1950, precision=DatePrecision.ABOUT)
        result = format_date_long(d)
        assert "vers" in result

    def test_format_long_with_precision_before(self):
        """Test format long avec précision 'avant'."""
        d = Date(year=1950, precision=DatePrecision.BEFORE)
        result = format_date_long(d)
        assert "avant" in result


class TestIsValidDate:
    """Tests pour is_valid_date."""

    def test_valid_date(self):
        """Test date valide."""
        assert is_valid_date(15, 3, 1950) is True

    def test_invalid_day(self):
        """Test jour invalide."""
        assert is_valid_date(31, 2, 2000) is False

    def test_invalid_month(self):
        """Test mois invalide."""
        assert is_valid_date(15, 13, 2000) is False

    def test_leap_year(self):
        """Test année bissextile."""
        assert is_valid_date(29, 2, 2000) is True
        assert is_valid_date(29, 2, 2001) is False


class TestCalculateAge:
    """Tests pour calculate_age."""

    def test_calculate_age_simple(self):
        """Test calcul d'âge simple."""
        birth = Date(year=1950)
        ref = Date(year=2020)
        assert calculate_age(birth, ref) == 70

    def test_calculate_age_with_months(self):
        """Test calcul d'âge avec mois."""
        birth = Date(month=6, year=1950)
        ref = Date(month=3, year=2020)
        assert calculate_age(birth, ref) == 69  # Pas encore eu l'anniversaire

    def test_calculate_age_no_birth_year(self):
        """Test sans année de naissance."""
        birth = Date(month=6)
        assert calculate_age(birth) is None

    def test_calculate_age_current_date(self):
        """Test avec date actuelle."""
        birth = Date(year=1950)
        age = calculate_age(birth)
        assert age is not None
        assert age > 0


class TestCompareDates:
    """Tests pour compare_dates."""

    def test_compare_equal_dates(self):
        """Test dates égales."""
        d1 = Date(year=1950)
        d2 = Date(year=1950)
        assert compare_dates(d1, d2) == 0

    def test_compare_before(self):
        """Test date avant."""
        d1 = Date(year=1950)
        d2 = Date(year=1960)
        assert compare_dates(d1, d2) == -1

    def test_compare_after(self):
        """Test date après."""
        d1 = Date(year=1960)
        d2 = Date(year=1950)
        assert compare_dates(d1, d2) == 1

    def test_compare_with_months(self):
        """Test comparaison avec mois."""
        d1 = Date(month=3, year=1950)
        d2 = Date(month=6, year=1950)
        assert compare_dates(d1, d2) == -1


class TestDateRange:
    """Tests pour date_range."""

    def test_date_range_both_dates(self):
        """Test période avec deux dates."""
        d1 = Date(year=1950)
        d2 = Date(year=1960)
        result = date_range(d1, d2)
        assert "1950" in result
        assert "1960" in result
        assert "-" in result

    def test_date_range_start_only(self):
        """Test période avec début seul."""
        d1 = Date(year=1950)
        result = date_range(d1, None)
        assert "1950" in result
        assert "-" in result

    def test_date_range_end_only(self):
        """Test période avec fin seule."""
        d2 = Date(year=1960)
        result = date_range(None, d2)
        assert "1960" in result
        assert "-" in result

    def test_date_range_no_dates(self):
        """Test période sans dates."""
        assert date_range(None, None) == ""


class TestGetCurrentDate:
    """Tests pour get_current_date."""

    def test_get_current_date(self):
        """Test récupération date actuelle."""
        d = get_current_date()
        assert d.year is not None
        assert d.month is not None
        assert d.day is not None
        assert d.precision == DatePrecision.EXACT

        # Vérifier que c'est bien la date du jour
        today = python_date.today()
        assert d.year == today.year
        assert d.month == today.month
        assert d.day == today.day
