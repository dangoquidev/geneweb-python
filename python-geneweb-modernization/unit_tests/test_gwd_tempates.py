"""
Unit tests for gwd_templates.py
"""

import os
import pytest
import io
import tempfile
from unittest.mock import MagicMock
from gwd_templates import GeneWebHTTPHandler, GWDConfig

class TestGeneWebHTTPHandler:
    @pytest.fixture
    def config(self):
        """Create a test configuration"""
        config = GWDConfig()
        config.database_dir = tempfile.mkdtemp()
        config.selected_port = 8080
        config.etc_prefix = tempfile.mkdtemp()
        config.images_prefix = tempfile.mkdtemp()
        return config

    @pytest.fixture
    def cleanup(self, config):
        """Cleanup temporary directories after tests"""
        yield
        for directory in [config.database_dir, config.etc_prefix, config.images_prefix]:
            try:
                os.rmdir(directory)
            except:
                pass

    @pytest.fixture
    def handler(self, config):
        """Create a mock GeneWebHTTPHandler"""
        request = MagicMock()
        request.makefile = MagicMock(return_value=io.BytesIO())
        request.requestline = "GET /robots.txt HTTP/1.1"  # Ajout de l'attribut requestline
        client_address = ('127.0.0.1', 8080)
        server = MagicMock()
        return GeneWebHTTPHandler(request, client_address, server, gwd_config=config)

    def test_get_content_type(self, handler):
        """Test content type detection"""
        assert handler.get_content_type('test.html') == 'text/html; charset=utf-8'
        assert handler.get_content_type('style.css') == 'text/css'
        assert handler.get_content_type('script.js') == 'application/javascript'
        assert handler.get_content_type('image.png') == 'image/png'
        assert handler.get_content_type('photo.jpg') == 'image/jpeg'
        assert handler.get_content_type('icon.ico') == 'image/x-icon'
        assert handler.get_content_type('unknown.xyz') == 'application/octet-stream'

class TestGWDConfig:
    def test_default_config(self):
        """Test default configuration values"""
        config = GWDConfig()
        
        assert config.selected_port == 2317
        assert config.database_dir == "."
        assert config.daemon is False
        assert isinstance(config.excluded_addresses, list)

        # assert isinstance(config.excluded_addresses, list)
        # assert isinstance(config.only_addresses, list)
        # assert config.no_host_address is False

if __name__ == "__main__":
    pytest.main(["-v"])