"""
Tests pour utils/config.py.

Tests de la configuration centralisée.
"""

import os
import tempfile
from pathlib import Path

from backend.utils.config import Config, ServerConfig, get_config, reset_config, set_config


class TestConfig:
    """Tests pour la classe Config."""

    def test_config_default_values(self):
        """Test valeurs par défaut."""
        config = Config()
        assert config.port == 2317
        assert config.host == "localhost"
        assert config.debug is False
        assert config.session_timeout == 1800

    def test_config_custom_values(self):
        """Test valeurs personnalisées."""
        config = Config(port=8080, host="0.0.0.0", debug=True)
        assert config.port == 8080
        assert config.host == "0.0.0.0"
        assert config.debug is True

    def test_config_paths_conversion(self):
        """Test conversion des chemins en Path."""
        config = Config(database_dir="data", data_dir="data")
        assert isinstance(config.database_dir, Path)
        assert isinstance(config.data_dir, Path)

    def test_config_secret_key_generation(self):
        """Test génération clé secrète."""
        config = Config()
        assert config.secret_key is not None
        assert len(config.secret_key) > 0

    def test_config_directories_creation(self):
        """Test création des répertoires."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_dir = Path(tmpdir) / "databases"
            config = Config(database_dir=db_dir)
            assert config.database_dir.exists()

    def test_get_database_path(self):
        """Test obtention chemin de base."""
        config = Config(database_dir="data")
        path = config.get_database_path("test")
        assert str(path).endswith("test.pickle")

        path = config.get_database_path("test.pickle")
        assert str(path).endswith("test.pickle")

    def test_list_databases(self):
        """Test liste des bases."""
        config = Config(database_dir="data")
        databases = config.list_databases()
        assert isinstance(databases, list)
        # Les bases doivent être triées
        assert databases == sorted(databases)

    def test_database_exists(self):
        """Test vérification existence base."""
        config = Config(database_dir="data")
        # Tester avec une base existante
        if config.list_databases():
            db_name = config.list_databases()[0]
            assert config.database_exists(db_name) is True

        # Tester avec une base inexistante
        assert config.database_exists("non_existent_db_xyz") is False


class TestConfigFromEnv:
    """Tests pour Config.from_env."""

    def test_from_env_default(self):
        """Test configuration depuis env (valeurs par défaut)."""
        # Sauvegarder les variables d'environnement actuelles
        original_env = {}
        env_vars = [
            "GENEWEB_PORT",
            "GENEWEB_HOST",
            "GENEWEB_DATABASE_DIR",
            "GENEWEB_DEBUG",
            "GENEWEB_SECRET_KEY",
            "GENEWEB_LOG_LEVEL",
        ]

        for var in env_vars:
            if var in os.environ:
                original_env[var] = os.environ[var]
                del os.environ[var]

        try:
            config = Config.from_env()
            assert config.port == 2317
            assert config.host == "localhost"
            assert config.debug is False
        finally:
            # Restaurer les variables d'environnement
            for var, value in original_env.items():
                os.environ[var] = value

    def test_from_env_custom(self):
        """Test configuration depuis env (valeurs personnalisées)."""
        # Définir des variables d'environnement
        os.environ["GENEWEB_PORT"] = "8080"
        os.environ["GENEWEB_HOST"] = "0.0.0.0"
        os.environ["GENEWEB_DEBUG"] = "true"
        os.environ["GENEWEB_LOG_LEVEL"] = "DEBUG"

        try:
            config = Config.from_env()
            assert config.port == 8080
            assert config.host == "0.0.0.0"
            assert config.debug is True
            assert config.log_level == "DEBUG"
        finally:
            # Nettoyer
            del os.environ["GENEWEB_PORT"]
            del os.environ["GENEWEB_HOST"]
            del os.environ["GENEWEB_DEBUG"]
            del os.environ["GENEWEB_LOG_LEVEL"]


class TestServerConfig:
    """Tests pour ServerConfig."""

    def test_server_config_default(self):
        """Test valeurs par défaut ServerConfig."""
        config = ServerConfig()
        assert config.frontend_dev is False
        assert config.max_workers == 10
        assert config.request_timeout == 30
        assert config.require_auth is False

    def test_server_config_custom(self):
        """Test valeurs personnalisées ServerConfig."""
        config = ServerConfig(frontend_dev=True, max_workers=20, require_auth=True)
        assert config.frontend_dev is True
        assert config.max_workers == 20
        assert config.require_auth is True

    def test_server_config_paths(self):
        """Test conversion chemins ServerConfig."""
        config = ServerConfig(frontend_dist="dist", auth_file="auth.txt")
        assert isinstance(config.frontend_dist, Path)
        assert isinstance(config.auth_file, Path)


class TestGlobalConfig:
    """Tests pour les fonctions globales de configuration."""

    def setup_method(self):
        """Setup avant chaque test."""
        reset_config()

    def teardown_method(self):
        """Cleanup après chaque test."""
        reset_config()

    def test_get_config_default(self):
        """Test récupération config par défaut."""
        config = get_config()
        assert config is not None
        assert isinstance(config, Config)

    def test_get_config_singleton(self):
        """Test que get_config retourne toujours la même instance."""
        config1 = get_config()
        config2 = get_config()
        assert config1 is config2

    def test_set_config(self):
        """Test définition config personnalisée."""
        custom_config = Config(port=9000)
        set_config(custom_config)

        config = get_config()
        assert config.port == 9000

    def test_reset_config(self):
        """Test réinitialisation config."""
        custom_config = Config(port=9000)
        set_config(custom_config)

        reset_config()

        # Après reset, on devrait obtenir une nouvelle instance
        config = get_config()
        assert config.port == 2317  # Valeur par défaut
