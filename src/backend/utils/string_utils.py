"""
Utilitaires de manipulation de chaînes pour GenEWeb.

Ce module fournit des fonctions pour normaliser, rechercher et manipuler
les chaînes de caractères, notamment pour les noms de personnes.
"""

import re
import unicodedata
from typing import List, Optional


def normalize_string(text: str) -> str:
    """
    Normalise une chaîne pour la recherche et la comparaison.

    Transformations appliquées:
    - Conversion en minuscules
    - Suppression des accents
    - Suppression des caractères spéciaux
    - Trim des espaces

    Args:
        text: Texte à normaliser

    Returns:
        str: Texte normalisé

    Examples:
        >>> normalize_string("Élève")
        'eleve'
        >>> normalize_string("Jean-Paul")
        'jeanpaul'
    """
    if not text:
        return ""

    # Conversion en minuscules
    text = text.lower()

    # Suppression des accents (NFD = décomposition canonique)
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")

    # Suppression des caractères spéciaux (garde lettres, chiffres, espaces)
    text = re.sub(r"[^a-z0-9\s]", "", text)

    # Normalisation des espaces multiples
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def remove_accents(text: str) -> str:
    """
    Supprime les accents d'une chaîne.

    Args:
        text: Texte avec accents

    Returns:
        str: Texte sans accents

    Examples:
        >>> remove_accents("Élève français")
        'Eleve francais'
    """
    if not text:
        return ""

    # Décomposition canonique (sépare caractère de base et accent)
    nfd = unicodedata.normalize("NFD", text)

    # Filtre les marques diacritiques (accents)
    return "".join(c for c in nfd if unicodedata.category(c) != "Mn")


def capitalize_name(name: str) -> str:
    """
    Met en majuscule un nom propre de manière intelligente.

    Gère les cas spéciaux comme:
    - Noms composés (Jean-Paul -> Jean-Paul)
    - Particules (de la Fontaine -> de la Fontaine)
    - Préfixes (O'Brien -> O'Brien, McDonald -> McDonald)

    Args:
        name: Nom à mettre en forme

    Returns:
        str: Nom correctement capitalisé

    Examples:
        >>> capitalize_name("jean-paul DUPONT")
        'Jean-Paul Dupont'
        >>> capitalize_name("o'brien")
        "O'Brien"
    """
    if not name:
        return ""

    # Particules à garder en minuscules
    particles = {"de", "la", "le", "du", "des", "van", "von", "van der", "de la"}

    words = []
    for word in name.split():
        # Gérer les tirets (Jean-Paul)
        if "-" in word:
            parts = [p.capitalize() for p in word.split("-")]
            words.append("-".join(parts))
        # Gérer les apostrophes (O'Brien)
        elif "'" in word:
            parts = word.split("'")
            words.append("'".join([p.capitalize() for p in parts]))
        # Particules en minuscules
        elif word.lower() in particles and words:  # Pas au début
            words.append(word.lower())
        else:
            words.append(word.capitalize())

    return " ".join(words)


def fuzzy_match(text1: str, text2: str, threshold: float = 0.8) -> bool:
    """
    Compare deux chaînes avec une correspondance floue.

    Utilise la distance de Levenshtein normalisée pour comparer.

    Args:
        text1: Première chaîne
        text2: Deuxième chaîne
        threshold: Seuil de similarité (0.0 à 1.0)

    Returns:
        bool: True si les chaînes sont similaires au-dessus du seuil

    Examples:
        >>> fuzzy_match("Jean", "Jeane")
        True
        >>> fuzzy_match("Jean", "Paul")
        False
    """
    if not text1 or not text2:
        return False

    # Normaliser les textes
    text1 = normalize_string(text1)
    text2 = normalize_string(text2)

    # Calcul de la distance de Levenshtein
    distance = levenshtein_distance(text1, text2)
    max_len = max(len(text1), len(text2))

    if max_len == 0:
        return True

    similarity = 1.0 - (distance / max_len)
    return similarity >= threshold


def levenshtein_distance(s1: str, s2: str) -> int:
    """
    Calcule la distance de Levenshtein entre deux chaînes.

    La distance de Levenshtein mesure le nombre minimum d'opérations
    (insertion, suppression, substitution) nécessaires pour transformer
    une chaîne en une autre.

    Args:
        s1: Première chaîne
        s2: Deuxième chaîne

    Returns:
        int: Distance de Levenshtein
    """
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)

    if len(s2) == 0:
        return len(s1)

    previous_row = list(range(len(s2) + 1))
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            # Coût d'insertion, suppression, substitution
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]


def search_in_text(query: str, text: str, case_sensitive: bool = False) -> bool:
    """
    Recherche une requête dans un texte.

    Args:
        query: Requête à rechercher
        text: Texte dans lequel rechercher
        case_sensitive: Recherche sensible à la casse

    Returns:
        bool: True si la requête est trouvée

    Examples:
        >>> search_in_text("jean", "Jean Dupont")
        True
        >>> search_in_text("jean", "Jean Dupont", case_sensitive=True)
        False
    """
    if not query or not text:
        return False

    if not case_sensitive:
        query = normalize_string(query)
        text = normalize_string(text)

    return query in text


def extract_words(text: str) -> List[str]:
    """
    Extrait les mots d'un texte.

    Args:
        text: Texte à analyser

    Returns:
        List[str]: Liste des mots extraits

    Examples:
        >>> extract_words("Jean-Paul de la Fontaine")
        ['Jean', 'Paul', 'de', 'la', 'Fontaine']
    """
    if not text:
        return []

    # Remplacer tirets et apostrophes par des espaces
    text = re.sub(r"[-']", " ", text)

    # Extraire les mots (lettres uniquement)
    words = re.findall(r"\b[a-zA-ZÀ-ÿ]+\b", text)

    return words


def truncate(text: str, max_length: int, suffix: str = "...") -> str:
    """
    Tronque un texte à une longueur maximale.

    Args:
        text: Texte à tronquer
        max_length: Longueur maximale
        suffix: Suffixe à ajouter si tronqué

    Returns:
        str: Texte tronqué

    Examples:
        >>> truncate("Ceci est un texte très long", 10)
        'Ceci es...'
    """
    if not text or len(text) <= max_length:
        return text

    return text[: max_length - len(suffix)] + suffix


def parse_name_parts(full_name: str) -> tuple[Optional[str], Optional[str]]:
    """
    Parse un nom complet en prénom et nom de famille.

    Assume que le dernier mot est le nom de famille et le(s) premier(s)
    mot(s) sont le(s) prénom(s).

    Args:
        full_name: Nom complet

    Returns:
        tuple: (prénom, nom de famille)

    Examples:
        >>> parse_name_parts("Jean Paul Dupont")
        ('Jean Paul', 'Dupont')
        >>> parse_name_parts("Dupont")
        (None, 'Dupont')
    """
    if not full_name:
        return None, None

    parts = full_name.strip().split()

    if len(parts) == 0:
        return None, None
    elif len(parts) == 1:
        return None, parts[0]
    else:
        first_name = " ".join(parts[:-1])
        surname = parts[-1]
        return first_name, surname


def sanitize_filename(filename: str) -> str:
    """
    Nettoie un nom de fichier pour le rendre sûr.

    Supprime ou remplace les caractères dangereux.

    Args:
        filename: Nom de fichier à nettoyer

    Returns:
        str: Nom de fichier sécurisé

    Examples:
        >>> sanitize_filename("ma base/../secret.db")
        'ma_base_secret.db'
    """
    if not filename:
        return "unnamed"

    # Supprimer les chemins relatifs
    filename = filename.replace("..", "")
    filename = filename.replace("/", "_")
    filename = filename.replace("\\", "_")

    # Garder uniquement caractères alphanumériques, tirets, underscores, points
    filename = re.sub(r"[^a-zA-Z0-9._-]", "_", filename)

    # Éviter les noms de fichiers spéciaux Windows
    reserved = {"CON", "PRN", "AUX", "NUL", "COM1", "LPT1"}
    if filename.upper() in reserved:
        filename = f"_{filename}"

    return filename or "unnamed"


def format_list(items: List[str], conjunction: str = "et") -> str:
    """
    Formate une liste en chaîne avec conjonction.

    Args:
        items: Liste d'éléments
        conjunction: Conjonction à utiliser

    Returns:
        str: Liste formatée

    Examples:
        >>> format_list(["Jean", "Paul", "Marie"])
        'Jean, Paul et Marie'
        >>> format_list(["Jean", "Paul"])
        'Jean et Paul'
        >>> format_list(["Jean"])
        'Jean'
    """
    if not items:
        return ""

    if len(items) == 1:
        return items[0]
    elif len(items) == 2:
        return f"{items[0]} {conjunction} {items[1]}"
    else:
        return ", ".join(items[:-1]) + f" {conjunction} {items[-1]}"
