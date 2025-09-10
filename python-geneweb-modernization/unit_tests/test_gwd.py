import pytest
import sys
import os
import signal
from unittest.mock import patch, MagicMock
from gwd import parse_arguments, validate_arguments, setup_signal_handlers, main


def test_parse_arguments_default():
    """Test parsing arguments with default values"""
    test_args = ["gwd.py"]
    with patch.object(sys, 'argv', test_args):
        args = parse_arguments()
        assert args.port == 2317
        assert args.database_dir == "."
        assert args.conn_timeout == 120
        assert args.max_pending_requests == 150
        assert args.n_workers == 20
        assert args.daemon is False
        assert args.default_lang == "fr"


def test_parse_arguments_custom():
    """Test parsing arguments with custom values"""
    test_args = [
        "gwd.py", "-p", "8080", "-hd", "/path/to/databases", "-daemon",
        "-only", "127.0.0.1", "-auth", "auth.txt"
    ]
    with patch.object(sys, 'argv', test_args):
        args = parse_arguments()
        assert args.port == 8080
        assert args.database_dir == "/path/to/databases"
        assert args.daemon is True
        assert args.only_addresses == ["127.0.0.1"]
        assert args.auth_file == "auth.txt"


def test_validate_arguments_valid():
    """Test validate_arguments with valid arguments"""
    args = MagicMock()
    args.port = 8080
    args.database_dir = "."
    args.auth_file = None
    args.robot_xcl = "10,60"
    with patch("os.path.isdir", return_value=True):
        validate_arguments(args)  # Should not raise any exception


def test_validate_arguments_invalid_port():
    """Test validate_arguments with an invalid port"""
    args = MagicMock()
    args.port = 70000  # Invalid port
    args.database_dir = "."
    args.auth_file = None
    args.robot_xcl = None
    with pytest.raises(SystemExit):
        validate_arguments(args)


def test_validate_arguments_invalid_database_dir():
    """Test validate_arguments with an invalid database directory"""
    args = MagicMock()
    args.port = 8080
    args.database_dir = "/invalid/path"
    args.auth_file = None
    args.robot_xcl = None
    with patch("os.path.isdir", return_value=False), pytest.raises(SystemExit):
        validate_arguments(args)


def test_validate_arguments_invalid_robot_xcl():
    """Test validate_arguments with an invalid robot_xcl format"""
    args = MagicMock()
    args.port = 8080
    args.database_dir = "."
    args.auth_file = None
    args.robot_xcl = "invalid_format"
    with pytest.raises(SystemExit):
        validate_arguments(args)


def test_main():
    """Test main function"""
    test_args = ["gwd.py", "-p", "8080", "-hd", "/path/to/databases"]
    with patch.object(sys, 'argv', test_args), \
         patch("gwd.parse_arguments") as mock_parse_arguments, \
         patch("gwd.validate_arguments") as mock_validate_arguments, \
         patch("gwd.setup_signal_handlers") as mock_setup_signal_handlers, \
         patch("gwd.start_geneweb_daemon") as mock_start_geneweb_daemon:
        mock_parse_arguments.return_value = MagicMock(
            port=8080,
            database_dir="/path/to/databases",
            daemon=False
        )
        main()
        mock_parse_arguments.assert_called_once()
        mock_validate_arguments.assert_called_once()
        mock_setup_signal_handlers.assert_called_once()
        mock_start_geneweb_daemon.assert_called_once()