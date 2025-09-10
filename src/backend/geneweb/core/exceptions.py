"""Exceptions personnalisées pour GenEWeb."""


class GenEWebError(Exception):
    """Exception de base pour GenEWeb."""

    pass


class DatabaseError(GenEWebError):
    """Erreur liée à la base de données."""

    pass


class TemplateError(GenEWebError):
    """Erreur liée au rendu de templates."""

    pass


class AuthenticationError(GenEWebError):
    """Erreur d'authentification."""

    pass


class ConfigurationError(GenEWebError):
    """Erreur de configuration."""

    pass


class AccessDeniedError(GenEWebError):
    """Erreur d'accès refusé."""

    pass
