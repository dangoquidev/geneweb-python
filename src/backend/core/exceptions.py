"""
Exceptions personnalisées pour GenEWeb.

Hiérarchie des exceptions métier avec messages clairs et actionnables.
"""

from typing import Any, Optional


class GenEWebError(Exception):
    """Exception de base pour toutes les erreurs GenEWeb."""

    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __str__(self) -> str:
        if self.details:
            details_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            return f"{self.message} ({details_str})"
        return self.message


# ============================================================================
# Exceptions de base de données
# ============================================================================


class DatabaseError(GenEWebError):
    """Erreur liée à la base de données."""

    def __init__(self, database_or_message: str, message: Optional[str] = None):
        """
        Initialise une erreur de base de données.

        Args:
            database_or_message: Nom de la base OU message complet
            message: Message d'erreur (si premier arg est le nom de base)
        """
        if message is None:
            # Un seul argument : c'est le message complet
            super().__init__(database_or_message)
        else:
            # Deux arguments : database + message
            super().__init__(f"Database '{database_or_message}' error: {message}", {"database": database_or_message})
            self.database_name = database_or_message


class DatabaseNotFoundError(DatabaseError):
    """Base de données introuvable."""

    def __init__(self, database_name: str):
        super().__init__(f"Database '{database_name}' not found")
        self.database_name = database_name


class DatabaseAlreadyExistsError(DatabaseError):
    """Base de données existe déjà."""

    def __init__(self, database_name: str):
        super().__init__(f"Database '{database_name}' already exists")
        self.database_name = database_name


class DatabaseCorruptedError(DatabaseError):
    """Base de données corrompue ou invalide."""

    def __init__(self, database_name: str, reason: str):
        super().__init__(f"Database '{database_name}' is corrupted: {reason}")
        self.database_name = database_name
        self.reason = reason


class DatabaseReadOnlyError(DatabaseError):
    """Tentative d'écriture sur une base en lecture seule."""

    def __init__(self, database_name: str):
        super().__init__(f"Database '{database_name}' is read-only")
        self.database_name = database_name


# ============================================================================
# Exceptions de données
# ============================================================================


class DataError(GenEWebError):
    """Erreur liée aux données métier."""


class PersonNotFoundError(DataError):
    """Personne introuvable."""

    def __init__(self, person_id: str):
        super().__init__(f"Person with ID {person_id} not found", {"person_id": person_id})
        self.person_id = person_id


class FamilyNotFoundError(DataError):
    """Famille introuvable."""

    def __init__(self, family_id: str):
        super().__init__(f"Family with ID {family_id} not found", {"family_id": family_id})
        self.family_id = family_id


class InvalidDataError(DataError):
    """Données invalides."""

    def __init__(self, field: str, value: Any, reason: str):
        super().__init__(
            f"Invalid value for field '{field}': {reason}", {"field": field, "value": str(value), "reason": reason}
        )
        self.field = field
        self.value = value
        self.reason = reason


class DuplicatePersonError(DataError):
    """Personne en doublon."""

    def __init__(self, first_name: str, surname: str, existing_id: int):
        super().__init__(
            f"Person '{first_name} {surname}' already exists (ID: {existing_id})",
            {"first_name": first_name, "surname": surname, "existing_id": existing_id},
        )
        self.first_name = first_name
        self.surname = surname
        self.existing_id = existing_id


# ============================================================================
# Exceptions d'authentification et d'autorisation
# ============================================================================


class AuthenticationError(GenEWebError):
    """Erreur d'authentification."""


class InvalidCredentialsError(AuthenticationError):
    """Identifiants invalides."""

    def __init__(self, username: str):
        super().__init__(f"Invalid credentials for user '{username}'", {"username": username})
        self.username = username


class AuthorizationError(GenEWebError):
    """Erreur d'autorisation (permissions insuffisantes)."""

    def __init__(self, required_level: str, current_level: str):
        super().__init__(
            f"Insufficient permissions: requires {required_level}, has {current_level}",
            {"required": required_level, "current": current_level},
        )
        self.required_level = required_level
        self.current_level = current_level


class SessionExpiredError(AuthenticationError):
    """Session expirée."""

    def __init__(self):
        super().__init__("Session has expired, please log in again")


# ============================================================================
# Exceptions d'import/export
# ============================================================================


class ImportError(GenEWebError):
    """Erreur lors de l'import de données."""

    def __init__(self, source: str, reason: str, line: Optional[int] = None):
        details: dict[str, Any] = {"source": source, "reason": reason}
        if line:
            details["line"] = line
            message = f"Import error from '{source}' at line {line}: {reason}"
        else:
            message = f"Import error from '{source}': {reason}"

        super().__init__(message, details)
        self.source = source
        self.reason = reason
        self.line = line


class ExportError(GenEWebError):
    """Erreur lors de l'export de données."""

    def __init__(self, destination: str, reason: str):
        super().__init__(f"Export error to '{destination}': {reason}", {"destination": destination, "reason": reason})
        self.destination = destination
        self.reason = reason


class GEDCOMParseError(ImportError):
    """Erreur de parsing GEDCOM."""

    def __init__(self, line: int, content: str, reason: str):
        super().__init__(source="GEDCOM", reason=f"Parse error: {reason} (content: '{content}')", line=line)
        self.content = content


# ============================================================================
# Exceptions de validation
# ============================================================================


class ValidationError(GenEWebError):
    """Erreur de validation des données."""

    def __init__(self, field_or_message: str, message: Optional[str] = None):
        """
        Initialise une erreur de validation.

        Args:
            field_or_message: Nom du champ OU message complet
            message: Message d'erreur (si premier arg est le champ)
        """
        if message is None:
            # Un seul argument : c'est le message complet
            super().__init__(field_or_message)
            self.field = None
        else:
            # Deux arguments : field + message
            super().__init__(f"Validation error for field '{field_or_message}': {message}", {"field": field_or_message})
            self.field = field_or_message


class DateValidationError(ValidationError):
    """Erreur de validation de date."""

    def __init__(self, date_string: str, reason: str):
        super().__init__("date", f"Invalid date '{date_string}': {reason}")  # field  # message
        self.date_string = date_string
        self.reason = reason


# ============================================================================
# Exceptions de configuration
# ============================================================================


class ConfigurationError(GenEWebError):
    """Erreur de configuration."""

    def __init__(self, parameter: str, reason: str):
        super().__init__(f"Configuration error for '{parameter}': {reason}", {"parameter": parameter, "reason": reason})
        self.parameter = parameter
        self.reason = reason
