#!/usr/bin/env python3
"""
Script de lancement du serveur GenEWeb Daemon (gwd) - Équivalent exact du gwd original

Ce script recrée fidèlement l'interface en ligne de commande du serveur gwd original,
avec toutes ses options et son comportement.

Usage: python gwd.py [options]
   ou: python -m geneweb.gwd [options]
"""

import argparse
import os
import signal
import sys
from pathlib import Path

# Import du serveur GenEWeb
from geneweb.web.gwd_server import ServerConfig, start_geneweb_daemon


def parse_arguments():
    """
    Parser les arguments en ligne de commande exactement comme l'original gwd
    """
    parser = argparse.ArgumentParser(
        prog="gwd",
        description="GenEWeb Daemon - Genealogy Web Server (Python modernization)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                          # Start server on port 2317
  %(prog)s -p 8080                  # Start server on port 8080
  %(prog)s -hd /path/to/databases   # Set database directory
  %(prog)s -daemon                  # Run as daemon
  %(prog)s -only 127.0.0.1          # Only accept from localhost
  %(prog)s -auth auth.txt           # Use authentication file

The server will be accessible at:
  http://localhost:PORT/DATABASE_NAME

where PORT is the port number (default 2317) and DATABASE_NAME
is the name of your GenEWeb database (without .pickle extension).
        """,
    )

    # Options de réseau
    parser.add_argument(
        "-addr",
        type=str,
        help="IP address to bind to (default: all interfaces)",
    )
    parser.add_argument(
        "-p",
        "-port",
        type=int,
        default=2317,
        dest="port",
        help="Port number (default: 2317)",
    )
    parser.add_argument(
        "-conn_tmout",
        type=int,
        default=120,
        dest="conn_timeout",
        help="Connection timeout in seconds (default: 120)",
    )
    parser.add_argument(
        "-max_pending_requests",
        type=int,
        default=150,
        help="Maximum pending requests (default: 150)",
    )
    parser.add_argument(
        "-n_workers",
        type=int,
        default=20,
        help="Number of worker processes (default: 20)",
    )

    # Répertoires et fichiers
    parser.add_argument(
        "-hd",
        type=str,
        default=".",
        dest="database_dir",
        help="Database directory (default: current directory)",
    )
    parser.add_argument(
        "-gw",
        type=str,
        dest="gw_prefix",
        help="GenEWeb installation directory prefix",
    )
    parser.add_argument(
        "-etc",
        type=str,
        dest="etc_prefix",
        help="Configuration files directory",
    )
    parser.add_argument("-images", type=str, dest="images_dir", help="Images directory")
    parser.add_argument("-images_prefix", type=str, help="Images URL prefix")

    # Authentification et sécurité
    parser.add_argument("-auth", type=str, dest="auth_file", help="Authentication file")
    parser.add_argument("-friend_passwd", type=str, help="Friend password")
    parser.add_argument(
        "-login_tmout",
        type=int,
        default=1800,
        dest="login_timeout",
        help="Login timeout in seconds (default: 1800)",
    )
    parser.add_argument(
        "-trace_failed_passwd",
        action="store_true",
        help="Trace failed password attempts",
    )

    # Contrôle d'accès
    parser.add_argument(
        "-only",
        type=str,
        action="append",
        dest="only_addresses",
        help="Only accept connections from these addresses (can be repeated)",
    )
    parser.add_argument(
        "-exclude",
        type=str,
        action="append",
        dest="excluded_addresses",
        help="Exclude these addresses (can be repeated)",
    )
    parser.add_argument(
        "-no_host_address",
        action="store_true",
        help="Do not resolve IP addresses to hostnames",
    )

    # Langues et localisation
    parser.add_argument(
        "-lang",
        type=str,
        default="fr",
        dest="default_lang",
        help="Default language (default: fr)",
    )
    parser.add_argument(
        "-choose_browser_lang",
        action="store_true",
        help="Choose language based on browser preference",
    )

    # Robots et statistiques
    parser.add_argument(
        "-robot_xcl",
        type=str,
        dest="robot_xcl",
        help="Robot exclusion (format: count,seconds)",
    )

    # Options serveur
    parser.add_argument(
        "-daemon",
        action="store_true",
        help="Run as daemon (background process)",
    )
    parser.add_argument("-setup_link", action="store_true", help="Allow setup links")

    # Options avancées (pour compatibilité)
    parser.add_argument(
        "-plugins",
        type=str,
        action="append",
        help="Load plugins (can be repeated)",
    )
    parser.add_argument(
        "-forced_plugins",
        type=str,
        action="append",
        help="Force load plugins (can be repeated)",
    )
    parser.add_argument(
        "-unsafe_plugins",
        type=str,
        action="append",
        help="Load unsafe plugins (can be repeated)",
    )

    # Options cachées/de développement
    parser.add_argument(
        "-green",
        type=str,
        default="#2f6400",
        dest="green_color",
        help=argparse.SUPPRESS,
    )  # Caché mais disponible

    return parser.parse_args()


def setup_signal_handlers():
    """
    Configuration des gestionnaires de signaux (comme l'original)
    """

    def signal_handler(signum, frame):
        print(f"\\nReceived signal {signum}, shutting down...")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


def validate_arguments(args):
    """
    Valider les arguments (comme l'original gwd)
    """
    errors = []

    # Vérifier le port
    if not (1 <= args.port <= 65535):
        errors.append(f"Invalid port number: {args.port}")

    # Vérifier le répertoire des bases
    if not os.path.isdir(args.database_dir):
        errors.append(f"Database directory not found: {args.database_dir}")

    # Vérifier le fichier d'authentification
    if args.auth_file and not os.path.isfile(args.auth_file):
        errors.append(f"Authentication file not found: {args.auth_file}")

    # Vérifier robot_xcl format
    if args.robot_xcl:
        try:
            parts = args.robot_xcl.split(",")
            if len(parts) != 2:
                raise ValueError
            int(parts[0])
            int(parts[1])
        except ValueError:
            errors.append(f"Invalid robot_xcl format: {args.robot_xcl} (expected: count,seconds)")

    if errors:
        print("Error(s) in command line arguments:", file=sys.stderr)
        for error in errors:
            print(f"  {error}", file=sys.stderr)
        sys.exit(1)


def show_startup_message(config: ServerConfig):
    """
    Afficher le message de démarrage (comme l'original)
    """
    print("GenEWeb Daemon - Python Modernization")
    print("=====================================")
    print(f"Port: {config.selected_port}")
    print(f"Database directory: {os.path.abspath(config.database_dir)}")

    if config.selected_addr:
        print(f"Bind address: {config.selected_addr}")

    if config.daemon:
        print("Running as daemon")
    else:
        print("\\nAccess your databases at:")
        addr = config.selected_addr or "localhost"
        print(f"  http://{addr}:{config.selected_port}/DATABASE_NAME")
        print("\\nPress Ctrl+C to stop the server")


def main():
    """
    Fonction principale (équivalent à main() de gwd.ml)
    """
    # Parser les arguments
    args = parse_arguments()

    # Valider les arguments
    validate_arguments(args)

    # Configurer les gestionnaires de signaux
    setup_signal_handlers()

    # Créer la configuration du serveur
    config_dict = {
        "selected_addr": args.addr,
        "selected_port": args.port,
        "conn_timeout": args.conn_timeout,
        "max_pending_requests": args.max_pending_requests,
        "n_workers": args.n_workers,
        "database_dir": args.database_dir,
        "daemon": args.daemon,
        "green_color": args.green_color,
    }

    # Ajouter les options optionnelles
    optional_fields = [
        "gw_prefix",
        "etc_prefix",
        "images_dir",
        "images_prefix",
        "auth_file",
        "friend_passwd",
        "login_timeout",
        "default_lang",
        "choose_browser_lang",
        "trace_failed_passwd",
        "only_addresses",
        "excluded_addresses",
        "no_host_address",
        "setup_link",
        "plugins",
        "forced_plugins",
        "unsafe_plugins",
    ]

    for field in optional_fields:
        value = getattr(args, field, None)
        if value is not None:
            if isinstance(value, list) and not value:
                continue  # Ignorer les listes vides
            config_dict[field] = value

    # Traiter robot_xcl
    if args.robot_xcl:
        parts = args.robot_xcl.split(",")
        config_dict["robot_xcl"] = (int(parts[0]), int(parts[1]))

    # Créer la configuration
    config = ServerConfig(**config_dict)

    # Afficher le message de démarrage
    if not config.daemon:
        show_startup_message(config)

    # Démarrer le serveur
    try:
        start_geneweb_daemon(
            host=config.selected_addr,
            port=config.selected_port,
            database_dir=config.database_dir,
            daemon=config.daemon,
            **{
                k: v
                for k, v in config_dict.items()
                if k
                not in [
                    "selected_addr",
                    "selected_port",
                    "database_dir",
                    "daemon",
                ]
            },
        )
    except KeyboardInterrupt:
        print("\\nServer stopped by user")
    except Exception as e:
        print(f"Server error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
