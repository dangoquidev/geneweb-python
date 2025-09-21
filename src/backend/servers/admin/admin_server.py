#!/usr/bin/env python3
"""
Admin Panel Server for GenEWeb Python - Équivalent du serveur 'setup' d'OCaml

Ce script lance le panel d'administration GenEWeb, séparé du serveur principal.
Il reproduit les fonctionnalités du serveur 'setup' de l'implémentation OCaml.

Usage: python admin_server.py [options]
   ou: python -m geneweb.admin [options]
"""

import argparse
import os
import signal
import sys
from typing import Optional

from .admin_core import AdminConfig, start_admin_server


def parse_arguments():
    """
    Parser les arguments en ligne de commande pour le serveur admin
    """
    parser = argparse.ArgumentParser(
        prog="gwsetup",
        description="GenEWeb Admin Panel - Database Administration Interface (Python modernization)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                          # Start admin panel on port 2316
  %(prog)s -p 8080                  # Start admin panel on port 8080
  %(prog)s -bd /path/to/databases   # Set database directory
  %(prog)s -daemon                  # Run as daemon
  %(prog)s -only 127.0.0.1          # Only accept from localhost
  %(prog)s -gwd_p 2317              # Set main server port (for redirects)

The admin panel will be accessible at:
  http://localhost:PORT/

where PORT is the port number (default 2316).

This server provides:
- Database creation and management
- Import/export tools (GED, GW formats)
- Database maintenance tools
- User management
- System configuration
        """,
    )

    # Options de réseau
    parser.add_argument(
        "-p",
        "-port",
        type=int,
        default=2316,
        dest="port",
        help="Port number for admin panel (default: 2316)",
    )
    parser.add_argument(
        "-gwd_p",
        type=int,
        default=2317,
        dest="gwd_port",
        help="Port number of main server (default: 2317)",
    )

    # Répertoires et fichiers
    parser.add_argument(
        "-bd",
        type=str,
        default=".",
        dest="database_dir",
        help="Database directory (default: current directory)",
    )
    parser.add_argument(
        "-gd",
        type=str,
        dest="setup_dir",
        default=".",
        help="Setup directory (default: current directory)",
    )
    parser.add_argument(
        "-bindir",
        type=str,
        dest="bin_dir",
        help="Binary directory (default: same as setup directory)",
    )

    # Contrôle d'accès
    parser.add_argument(
        "-only",
        type=str,
        dest="only_file",
        help="File containing authorized IP address",
    )

    # Options serveur
    parser.add_argument(
        "-daemon",
        action="store_true",
        help="Run as daemon (background process)",
    )

    # Langue
    parser.add_argument(
        "-lang",
        type=str,
        default="fr",
        dest="default_lang",
        help="Default language (default: fr)",
    )

    return parser.parse_args()


def setup_signal_handlers():
    """
    Configuration des gestionnaires de signaux
    """

    def signal_handler(signum, frame):
        print(f"\\nReceived signal {signum}, shutting down admin server...")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


def validate_arguments(args):
    """
    Valider les arguments
    """
    errors: list[str] = []

    # Vérifier le port
    if not (1 <= args.port <= 65535):
        errors.append(f"Invalid port number: {args.port}")

    # Vérifier le port gwd
    if not (1 <= args.gwd_port <= 65535):
        errors.append(f"Invalid gwd port number: {args.gwd_port}")

    # Vérifier le répertoire des bases
    if not os.path.isdir(args.database_dir):
        errors.append(f"Database directory not found: {args.database_dir}")

    # Vérifier le répertoire de setup
    if not os.path.isdir(args.setup_dir):
        errors.append(f"Setup directory not found: {args.setup_dir}")

    # Vérifier le fichier only
    if args.only_file and not os.path.isfile(args.only_file):
        errors.append(f"Only file not found: {args.only_file}")

    if errors:
        print("Error(s) in command line arguments:", file=sys.stderr)
        for error in errors:
            print(f"  {error}", file=sys.stderr)
        sys.exit(1)


def show_startup_message(config: AdminConfig):
    """
    Afficher le message de démarrage
    """
    print("GenEWeb Admin Panel - Python Modernization")
    print("==========================================")
    print(f"Admin port: {config.port}")
    print(f"Main server port: {config.gwd_port}")
    print(f"Database directory: {os.path.abspath(config.database_dir)}")
    print(f"Setup directory: {os.path.abspath(config.setup_dir)}")

    if config.daemon:
        print("Running as daemon")
    else:
        print("\\nAccess the admin panel at:")
        print(f"  http://localhost:{config.port}/")
        print("\\nPress Ctrl+C to stop the admin server")


def main():
    """
    Fonction principale du serveur admin
    """
    # Parser les arguments
    args = parse_arguments()

    # Valider les arguments
    validate_arguments(args)

    # Configurer les gestionnaires de signaux
    setup_signal_handlers()

    # Si bin_dir n'est pas spécifié, utiliser setup_dir
    if not args.bin_dir:
        args.bin_dir = args.setup_dir

    # Créer la configuration du serveur admin
    config = AdminConfig(
        port=args.port,
        gwd_port=args.gwd_port,
        database_dir=args.database_dir,
        setup_dir=args.setup_dir,
        bin_dir=args.bin_dir,
        daemon=args.daemon,
        default_lang=args.default_lang,
        only_file=args.only_file,
    )

    # Afficher le message de démarrage
    if not config.daemon:
        show_startup_message(config)

    # Démarrer le serveur admin
    try:
        start_admin_server(config)
    except KeyboardInterrupt:
        print("\\nAdmin server stopped by user")
    except Exception as e:
        print(f"Admin server error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()