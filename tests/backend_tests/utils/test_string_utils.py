"""
Tests pour utils/string_utils.py.

Tests des fonctions de manipulation de chaînes.
"""

from backend.utils.string_utils import (
    capitalize_name,
    extract_words,
    format_list,
    fuzzy_match,
    levenshtein_distance,
    normalize_string,
    parse_name_parts,
    remove_accents,
    sanitize_filename,
    search_in_text,
    truncate,
)


class TestNormalizeString:
    """Tests pour normalize_string."""

    def test_normalize_with_accents(self):
        """Test normalisation avec accents."""
        assert normalize_string("Élève") == "eleve"
        assert normalize_string("François") == "francois"

    def test_normalize_uppercase(self):
        """Test conversion en minuscules."""
        assert normalize_string("DUPONT") == "dupont"
        assert normalize_string("Jean-Paul") == "jeanpaul"

    def test_normalize_special_chars(self):
        """Test suppression caractères spéciaux."""
        assert normalize_string("Jean-Paul") == "jeanpaul"
        assert normalize_string("O'Brien") == "obrien"

    def test_normalize_multiple_spaces(self):
        """Test normalisation espaces multiples."""
        assert normalize_string("Jean  Paul   Dupont") == "jean paul dupont"

    def test_normalize_empty_string(self):
        """Test avec chaîne vide."""
        assert normalize_string("") == ""
        assert normalize_string("   ") == ""


class TestRemoveAccents:
    """Tests pour remove_accents."""

    def test_remove_french_accents(self):
        """Test suppression accents français."""
        assert remove_accents("Élève") == "Eleve"
        assert remove_accents("François") == "Francois"
        assert remove_accents("Hélène") == "Helene"

    def test_remove_no_accents(self):
        """Test sans accents."""
        assert remove_accents("Dupont") == "Dupont"

    def test_remove_accents_empty(self):
        """Test avec chaîne vide."""
        assert remove_accents("") == ""


class TestCapitalizeName:
    """Tests pour capitalize_name."""

    def test_capitalize_simple_name(self):
        """Test nom simple."""
        assert capitalize_name("dupont") == "Dupont"
        assert capitalize_name("DUPONT") == "Dupont"

    def test_capitalize_compound_name(self):
        """Test nom composé avec tiret."""
        assert capitalize_name("jean-paul") == "Jean-Paul"
        assert capitalize_name("JEAN-PAUL") == "Jean-Paul"

    def test_capitalize_with_apostrophe(self):
        """Test avec apostrophe."""
        assert capitalize_name("o'brien") == "O'Brien"
        assert capitalize_name("d'artagnan") == "D'Artagnan"

    def test_capitalize_with_particle(self):
        """Test avec particule."""
        assert capitalize_name("jean de la fontaine") == "Jean de la Fontaine"
        assert capitalize_name("jean du pré") == "Jean du Pré"

    def test_capitalize_empty(self):
        """Test avec chaîne vide."""
        assert capitalize_name("") == ""


class TestFuzzyMatch:
    """Tests pour fuzzy_match."""

    def test_fuzzy_match_similar(self):
        """Test correspondance similaire."""
        assert fuzzy_match("Jean", "Jeane") is True
        assert fuzzy_match("Dupont", "Dupond") is True

    def test_fuzzy_match_different(self):
        """Test correspondance différente."""
        assert fuzzy_match("Jean", "Paul") is False
        assert fuzzy_match("Dupont", "Martin") is False

    def test_fuzzy_match_exact(self):
        """Test correspondance exacte."""
        assert fuzzy_match("Jean", "Jean") is True

    def test_fuzzy_match_empty(self):
        """Test avec chaînes vides."""
        assert fuzzy_match("", "Jean") is False
        assert fuzzy_match("Jean", "") is False

    def test_fuzzy_match_threshold(self):
        """Test avec seuil personnalisé."""
        assert fuzzy_match("Jean", "Jeane", threshold=0.9) is False
        assert fuzzy_match("Jean", "Jean", threshold=0.9) is True


class TestLevenshteinDistance:
    """Tests pour levenshtein_distance."""

    def test_levenshtein_identical(self):
        """Test chaînes identiques."""
        assert levenshtein_distance("Jean", "Jean") == 0

    def test_levenshtein_one_char_diff(self):
        """Test différence d'un caractère."""
        assert levenshtein_distance("Jean", "Jeane") == 1

    def test_levenshtein_empty(self):
        """Test avec chaîne vide."""
        assert levenshtein_distance("", "Jean") == 4
        assert levenshtein_distance("Jean", "") == 4


class TestSearchInText:
    """Tests pour search_in_text."""

    def test_search_found(self):
        """Test recherche trouvée."""
        assert search_in_text("jean", "Jean Dupont") is True

    def test_search_not_found(self):
        """Test recherche non trouvée."""
        assert search_in_text("pierre", "Jean Dupont") is False

    def test_search_case_sensitive(self):
        """Test recherche sensible à la casse."""
        assert search_in_text("jean", "Jean Dupont", case_sensitive=True) is False
        assert search_in_text("Jean", "Jean Dupont", case_sensitive=True) is True

    def test_search_empty(self):
        """Test avec chaînes vides."""
        assert search_in_text("", "Jean Dupont") is False
        assert search_in_text("Jean", "") is False


class TestExtractWords:
    """Tests pour extract_words."""

    def test_extract_simple_words(self):
        """Test extraction mots simples."""
        assert extract_words("Jean Paul Dupont") == ["Jean", "Paul", "Dupont"]

    def test_extract_compound_words(self):
        """Test extraction mots composés."""
        words = extract_words("Jean-Paul de la Fontaine")
        assert "Jean" in words
        assert "Paul" in words
        assert "Fontaine" in words

    def test_extract_empty(self):
        """Test avec chaîne vide."""
        assert extract_words("") == []


class TestTruncate:
    """Tests pour truncate."""

    def test_truncate_long_text(self):
        """Test troncature texte long."""
        result = truncate("Ceci est un texte très long", 10)
        assert result == "Ceci es..."
        assert len(result) == 10

    def test_truncate_short_text(self):
        """Test texte court (pas de troncature)."""
        assert truncate("Court", 10) == "Court"

    def test_truncate_custom_suffix(self):
        """Test avec suffixe personnalisé."""
        result = truncate("Texte long", 8, suffix="…")
        assert result == "Texte l…"

    def test_truncate_empty(self):
        """Test avec chaîne vide."""
        assert truncate("", 10) == ""


class TestParseNameParts:
    """Tests pour parse_name_parts."""

    def test_parse_full_name(self):
        """Test parsing nom complet."""
        first, last = parse_name_parts("Jean Paul Dupont")
        assert first == "Jean Paul"
        assert last == "Dupont"

    def test_parse_single_name(self):
        """Test parsing nom simple."""
        first, last = parse_name_parts("Dupont")
        assert first is None
        assert last == "Dupont"

    def test_parse_two_names(self):
        """Test parsing deux noms."""
        first, last = parse_name_parts("Jean Dupont")
        assert first == "Jean"
        assert last == "Dupont"

    def test_parse_empty(self):
        """Test avec chaîne vide."""
        first, last = parse_name_parts("")
        assert first is None
        assert last is None


class TestSanitizeFilename:
    """Tests pour sanitize_filename."""

    def test_sanitize_normal_filename(self):
        """Test nom de fichier normal."""
        assert sanitize_filename("database.pickle") == "database.pickle"

    def test_sanitize_path_traversal(self):
        """Test protection contre path traversal."""
        result = sanitize_filename("../secret.db")
        assert ".." not in result

    def test_sanitize_special_chars(self):
        """Test remplacement caractères spéciaux."""
        result = sanitize_filename("ma base@2024!.db")
        assert "@" not in result
        assert "!" not in result

    def test_sanitize_empty(self):
        """Test avec chaîne vide."""
        assert sanitize_filename("") == "unnamed"

    def test_sanitize_windows_reserved(self):
        """Test noms réservés Windows."""
        assert sanitize_filename("CON") == "_CON"
        assert sanitize_filename("PRN") == "_PRN"


class TestFormatList:
    """Tests pour format_list."""

    def test_format_single_item(self):
        """Test liste à un élément."""
        assert format_list(["Jean"]) == "Jean"

    def test_format_two_items(self):
        """Test liste à deux éléments."""
        assert format_list(["Jean", "Paul"]) == "Jean et Paul"

    def test_format_three_items(self):
        """Test liste à trois éléments."""
        assert format_list(["Jean", "Paul", "Marie"]) == "Jean, Paul et Marie"

    def test_format_custom_conjunction(self):
        """Test avec conjonction personnalisée."""
        assert format_list(["Jean", "Paul"], conjunction="ou") == "Jean ou Paul"

    def test_format_empty_list(self):
        """Test liste vide."""
        assert format_list([]) == ""
