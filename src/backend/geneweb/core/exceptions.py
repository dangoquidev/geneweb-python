"""Exceptions personnalisées pour GenEWeb."""


class GenEWebError(Exception):
    """Exception de base pour GenEWeb."""


class DatabaseError(GenEWebError):
    """Erreur liée à la base de données."""


class TemplateError(GenEWebError):
    """Erreur liée au rendu de templates."""


class AuthenticationError(GenEWebError):
    """Erreur d'authentification."""


class ConfigurationError(GenEWebError):
    """Erreur de configuration."""


class AccessDeniedError(GenEWebError):
    """Erreur d'accès refusé."""
