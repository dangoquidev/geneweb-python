"""
Unit tests for gwd_templates.py
"""

import os
import pytest
import tempfile
from gwd_templates import GeneWebHTTPHandler, GWDConfig

class TestGeneWebHTTPHandler:
    @pytest.fixture
    def config(self):
        """Create a test configuration"""
        config = GWDConfig()
        # Use temporary directories for testing
        config.database_dir = tempfile.mkdtemp()
        config.selected_port = 8080
        config.etc_prefix = tempfile.mkdtemp()
        config.images_prefix = tempfile.mkdtemp()
        config.gw_prefix = tempfile.mkdtemp()
        return config

    @pytest.fixture
    def cleanup(self, config):
        """Cleanup temporary directories after tests"""
        yield
        for directory in [config.database_dir, config.etc_prefix, 
                         config.images_prefix, config.gw_prefix]:
            try:
                os.rmdir(directory)
            except:
                pass

    def test_serve_base_list(self, config, cleanup):
        """Test serving database list"""
        handler = GeneWebHTTPHandler(None, None, None, gwd_config=config)
        
        # Create mock response handler
        class MockResponse:
            def __init__(self):
                self.headers = {}
                self.status_code = None
                self.data = []
            
            def send_response(self, code):
                self.status_code = code
            
            def send_header(self, name, value):
                self.headers[name] = value
            
            def end_headers(self):
                pass
            
            def write(self, data):
                self.data.append(data)
        
        mock_response = MockResponse()
        handler.wfile = mock_response
        handler.send_response = mock_response.send_response
        handler.send_header = mock_response.send_header
        handler.end_headers = mock_response.end_headers
        
        # Create test database files
        test_db = os.path.join(config.database_dir, "test_db.pickle")
        with open(test_db, "w") as f:
            f.write("")
        
        # Test base list
        handler.serve_base_list()
        
        assert mock_response.status_code == 200
        assert mock_response.headers['Content-Type'] == 'text/html; charset=utf-8'
        
        # Check if response contains database name
        response_data = b''.join(mock_response.data).decode('utf-8')
        assert "test_db" in response_data
        
        # Cleanup test database
        os.remove(test_db)

    def test_get_content_type(self, config):
        """Test content type detection"""
        handler = GeneWebHTTPHandler(None, None, None, gwd_config=config)
        
        assert handler.get_content_type('test.html') == 'text/html; charset=utf-8'
        assert handler.get_content_type('style.css') == 'text/css'
        assert handler.get_content_type('script.js') == 'application/javascript'
        assert handler.get_content_type('image.png') == 'image/png'
        assert handler.get_content_type('photo.jpg') == 'image/jpeg'
        assert handler.get_content_type('icon.ico') == 'image/x-icon'
        assert handler.get_content_type('unknown.xyz') == 'application/octet-stream'

    def test_is_static_request(self, config):
        """Test static file detection"""
        handler = GeneWebHTTPHandler(None, None, None, gwd_config=config)
        
        assert handler.is_static_request('style.css') is True
        assert handler.is_static_request('image.png') is True
        assert handler.is_static_request('script.js') is True
        assert handler.is_static_request('database.gwb') is False
        assert handler.is_static_request('index.html') is True

class TestGWDConfig:
    def test_default_config(self):
        """Test default configuration values"""
        config = GWDConfig()
        
        assert config.selected_port == 2317
        assert config.database_dir == "."
        assert config.daemon is False
        assert config.green_color == "#2f6400"
        assert isinstance(config.excluded_addresses, list)
        assert isinstance(config.only_addresses, list)
        assert config.no_host_address is False

if __name__ == "__main__":
    pytest.main(["-v"])