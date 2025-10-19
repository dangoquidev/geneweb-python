"""
Configuration centralisée pour GenEWeb.

Ce module gère toute la configuration du système de manière centralisée.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


@dataclass
class Config:
    """
    Configuration principale de GenEWeb.

    Cette classe centralise tous les paramètres de configuration utilisés
    dans l'application (serveur, base de données, sécurité, etc.).

    Args:
        port: Port du serveur HTTP
        host: Adresse d'écoute du serveur
        database_dir: Répertoire des bases de données
        data_dir: Répertoire principal des données
        debug: Mode debug activé
        secret_key: Clé secrète pour les sessions
        log_level: Niveau de log (DEBUG, INFO, WARNING, ERROR)
        max_upload_size: Taille maximale des uploads (en bytes)
        session_timeout: Timeout des sessions (en secondes)
        allowed_origins: Origines autorisées pour CORS
    """

    # Serveur
    port: int = 2317
    host: str = "localhost"
    debug: bool = False

    # Chemins
    database_dir: Path = field(default_factory=lambda: Path("data"))
    data_dir: Path = field(default_factory=lambda: Path("data"))

    # Sécurité
    secret_key: Optional[str] = None
    session_timeout: int = 1800  # 30 minutes

    # Logs
    log_level: str = "INFO"
    log_file: Optional[Path] = None

    # Upload
    max_upload_size: int = 10 * 1024 * 1024  # 10 MB

    # CORS
    allowed_origins: List[str] = field(default_factory=lambda: ["*"])

    def __post_init__(self):
        """Initialisation post-création."""
        # Convertir les chemins en Path si nécessaire
        if isinstance(self.database_dir, str):
            self.database_dir = Path(self.database_dir)
        if isinstance(self.data_dir, str):
            self.data_dir = Path(self.data_dir)
        if isinstance(self.log_file, str):
            self.log_file = Path(self.log_file)

        # Générer une clé secrète si nécessaire
        if not self.secret_key:
            self.secret_key = os.environ.get("GENEWEB_SECRET_KEY", self._generate_secret_key())

        # Créer les répertoires s'ils n'existent pas
        self.database_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _generate_secret_key() -> str:
        """Génère une clé secrète aléatoire."""
        import secrets

        return secrets.token_hex(32)

    @classmethod
    def from_env(cls) -> "Config":
        """
        Crée une configuration depuis les variables d'environnement.

        Variables d'environnement supportées:
            - GENEWEB_PORT: Port du serveur
            - GENEWEB_HOST: Hôte du serveur
            - GENEWEB_DATABASE_DIR: Répertoire des bases
            - GENEWEB_DEBUG: Mode debug (true/false)
            - GENEWEB_SECRET_KEY: Clé secrète
            - GENEWEB_LOG_LEVEL: Niveau de log

        Returns:
            Config: Configuration initialisée depuis l'environnement
        """
        return cls(
            port=int(os.environ.get("GENEWEB_PORT", 2317)),
            host=os.environ.get("GENEWEB_HOST", "localhost"),
            database_dir=Path(os.environ.get("GENEWEB_DATABASE_DIR", "data")),
            debug=os.environ.get("GENEWEB_DEBUG", "").lower() in ("true", "1", "yes"),
            secret_key=os.environ.get("GENEWEB_SECRET_KEY"),
            log_level=os.environ.get("GENEWEB_LOG_LEVEL", "INFO").upper(),
        )

    def get_database_path(self, database_name: str) -> Path:
        """
        Obtient le chemin complet d'une base de données.

        Args:
            database_name: Nom de la base de données

        Returns:
            Path: Chemin complet vers le fichier de base de données
        """
        if not database_name.endswith(".pickle"):
            database_name = f"{database_name}.pickle"
        return self.database_dir / database_name

    def list_databases(self) -> List[str]:
        """
        Liste toutes les bases de données disponibles.

        Returns:
            List[str]: Liste des noms de bases de données (sans extension)
        """
        if not self.database_dir.exists():
            return []

        databases = []
        for file in self.database_dir.glob("*.pickle"):
            databases.append(file.stem)

        return sorted(databases)

    def database_exists(self, database_name: str) -> bool:
        """
        Vérifie si une base de données existe.

        Args:
            database_name: Nom de la base de données

        Returns:
            bool: True si la base existe, False sinon
        """
        return self.get_database_path(database_name).exists()


@dataclass
class ServerConfig(Config):
    """
    Configuration spécifique au serveur HTTP.

    Étend Config avec des paramètres spécifiques au serveur web.
    """

    # Frontend
    frontend_dev: bool = False
    frontend_dist: Optional[Path] = None
    frontend_dev_url: str = "http://localhost:5173"

    # Performance
    max_workers: int = 10
    request_timeout: int = 30

    # Authentification
    auth_file: Optional[Path] = None
    require_auth: bool = False

    def __post_init__(self):
        """Initialisation post-création."""
        super().__post_init__()

        # Convertir les chemins
        if isinstance(self.frontend_dist, str):
            self.frontend_dist = Path(self.frontend_dist)
        if isinstance(self.auth_file, str):
            self.auth_file = Path(self.auth_file)


# Configuration globale par défaut
_default_config: Optional[Config] = None


def get_config() -> Config:
    """
    Obtient la configuration globale.

    Returns:
        Config: Configuration globale de l'application
    """
    global _default_config
    if _default_config is None:
        _default_config = Config.from_env()
    return _default_config


def set_config(config: Config) -> None:
    """
    Définit la configuration globale.

    Args:
        config: Nouvelle configuration à utiliser
    """
    global _default_config
    _default_config = config


def reset_config() -> None:
    """Réinitialise la configuration globale."""
    global _default_config
    _default_config = None
