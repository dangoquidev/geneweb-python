#!/usr/bin/env python3
"""
GenEWeb Daemon (gwd) - Version simplifiée mais exacte du serveur original

Cette version utilise le serveur HTTP de Python pour éviter les problèmes asyncio
tout en gardant exactement la même interface et les mêmes fonctionnalités que l'original.
"""

import argparse
import json
import http.server
import logging
import os
import subprocess
import signal
import socketserver
import sys
import time
import urllib.parse
import urllib.request

# Import des modules GenEWeb
from ..geneweb.db.driver import create_database_driver
from ..geneweb.util.string_utils import *

# Import du moteur de templates


class GeneWebHTTPHandler(http.server.BaseHTTPRequestHandler):
    """Handler HTTP pour GenEWeb - comportement identique à l'original"""

    def __init__(self, *args, gwd_config=None, **kwargs):
        self.gwd_config = gwd_config
        super().__init__(*args, **kwargs)

    def log_message(self, format_str, *args):
        """Logging personnalisé (équivalent aux logs OCaml)"""
        remote_addr = self.client_address[0]
        message = format_str % args
        logging.getLogger("geneweb.gwd").info(f"{remote_addr} - {message}")

    def do_GET(self):
        """Traiter les requêtes GET (équivalent à la fonction connection OCaml)"""
        self.handle_request()

    def do_POST(self):
        """Traiter les requêtes POST"""
        self.handle_request()

    def handle_request(self):
        """Fonction principale de traitement des requêtes"""
        try:
            # Obtenir l'adresse client
            from_addr = self.client_address[0]

            # Résoudre le nom d'hôte si nécessaire
            if not self.gwd_config.no_host_address:
                try:
                    import socket

                    hostname = socket.gethostbyaddr(from_addr)[0]
                    from_addr = hostname
                except BaseException:
                    pass

            # Parser l'URL
            parsed_url = urllib.parse.urlparse(self.path)
            script_name = parsed_url.path[1:] if parsed_url.path.startswith("/") else parsed_url.path
            query_string = parsed_url.query

            # API JSON (pour frontend React)
            if script_name.startswith("api/"):
                self.handle_api_request(script_name, query_string)
                return

            # Frontend React (dev or prod)
            if self.gwd_config.frontend_dev:
                self.serve_frontend_dev(script_name, query_string)
                return
            if self.gwd_config.frontend_dist:
                self.serve_frontend_prod(script_name)
                return

            # Traitement spécial pour les fichiers statiques
            if script_name.startswith("static/"):
                self.serve_static_file(script_name)
                return

            # Traitement spécial robots.txt (exactement comme l'original)
            if script_name == "robots.txt":
                self.handle_robots_txt()
                return

            # Vérifier les exclusions (exactement comme l'original)
            if from_addr in self.gwd_config.excluded_addresses:
                self.refuse_log(from_addr)
                return

            # Vérifier only_addresses (exactement comme l'original)
            if self.gwd_config.only_addresses and from_addr not in self.gwd_config.only_addresses:
                self.only_log(from_addr)
                return

            # Traiter les fichiers statiques (images, css, js)
            if self.is_static_request(script_name):
                self.serve_static_file(script_name)
                return

            # Traitement principal GenEWeb
            self.handle_geneweb_request(script_name, query_string, from_addr)

        except Exception as e:
            logging.getLogger("geneweb.gwd").error(f"Error handling request: {e}")
            self.send_error(500, "Internal Server Error")

    # ===== Frontend (React) integration =====
    def serve_frontend_dev(self, script_name: str, query_string: str) -> None:
        """Proxy les requêtes vers le serveur Vite en dev, fallback index.html (SPA)."""
        base = getattr(self.gwd_config, "frontend_dev_url", "http://localhost:5173").rstrip("/")
        path = f"/{script_name}" if script_name else "/"
        url = f"{base}{path}"
        if query_string:
            url = f"{url}?{query_string}"
        try:
            req = urllib.request.Request(url, headers={"Accept": "*/*"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                body = resp.read()
                status = resp.getcode() or 200
                content_type = resp.headers.get("Content-Type", self.get_content_type(path))
                self.send_response(status)
                self.send_header("Content-Type", content_type)
                self.send_header("Cache-Control", "no-store")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
        except Exception:
            # Fallback SPA
            try:
                req = urllib.request.Request(f"{base}/index.html")
                with urllib.request.urlopen(req, timeout=5) as resp:
                    body = resp.read()
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.send_header("Cache-Control", "no-store")
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
                    return
            except Exception as e:
                logging.getLogger("geneweb.gwd").error(f"Dev proxy error: {e}")
                self.send_error(502, "Bad Gateway")

    def serve_frontend_prod(self, script_name: str) -> None:
        """Servir les fichiers générés (dist). Fallback SPA index.html pour routes inconnues."""
        dist_dir = self.gwd_config.frontend_dist
        if not dist_dir:
            self.send_error(404, "Frontend not configured")
            return
        requested = script_name if script_name else "index.html"
        candidate = os.path.join(dist_dir, requested)
        # Routes sans extension => SPA index.html
        if not os.path.splitext(requested)[1]:
            candidate = os.path.join(dist_dir, "index.html")
        if not os.path.exists(candidate) or not os.path.isfile(candidate):
            candidate = os.path.join(dist_dir, "index.html")
        try:
            with open(candidate, "rb") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", self.get_content_type(candidate))
            self.send_header("Content-Length", str(len(content)))
            if candidate.endswith(".html"):
                self.send_header("Cache-Control", "no-store")
            else:
                self.send_header("Cache-Control", "public, max-age=31536000, immutable")
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            logging.getLogger("geneweb.gwd").error(f"Error serving frontend file {candidate}: {e}")
            self.send_error(500, "Internal Server Error")

    def handle_api_request(self, script_name: str, query_string: str) -> None:
        """Endpoints JSON simples pour le frontend moderne.

        - GET /api/databases -> {"databases": ["name1", ...]}
        - GET /api/{base}/info -> infos base
        - GET /api/{base}/search?q=term -> résultats de recherche
        """
        try:
            parts = script_name.split("/")  # ["api", ...]
            if len(parts) == 2 and parts[1] == "databases":
                # Liste des bases disponibles (.pickle)
                databases: list[str] = []
                try:
                    for file in os.listdir(self.gwd_config.database_dir):
                        if file.endswith(".pickle"):
                            databases.append(file[:-7])
                except OSError:
                    pass

                payload = {"databases": sorted(databases)}
                body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Cache-Control", "no-store")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return

            if len(parts) >= 3:
                base_name = parts[1]
                action = parts[2]

                base_path = os.path.join(self.gwd_config.database_dir, f"{base_name}.pickle")
                if not os.path.exists(base_path):
                    self.send_error(404, f"Database '{base_name}' not found")
                    return

                # Ouvrir la base
                db_driver = create_database_driver(base_path, "pickle")
                if not db_driver.open_database(read_only=True):
                    self.send_error(500, "Cannot open database")
                    return

                try:
                    if action == "info":
                        info = db_driver.get_database_info()
                        payload = {
                            "base_name": base_name,
                            "persons": info.number_of_persons,
                            "families": info.number_of_families,
                            "path": info.path,
                            "version": info.version,
                        }
                        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
                        self.send_response(200)
                        self.send_header("Content-Type", "application/json; charset=utf-8")
                        self.send_header("Cache-Control", "no-store")
                        self.send_header("Content-Length", str(len(body)))
                        self.end_headers()
                        self.wfile.write(body)
                        return

                    if action == "search":
                        params = urllib.parse.parse_qs(query_string)
                        q = params.get("q", [""])[0] or params.get("search", [""])[0]
                        results: list[dict[str, str]] = []
                        if q:
                            for person_id, person in db_driver.search_persons(q, max_results=50):
                                birth_text = geneweb_date_to_string(person.birth_date) if getattr(person, "birth_date", None) else ""
                                death_text = ""
                                # Compat: death_date peut exister en attribut direct
                                if getattr(person, "death_date", None):
                                    death_text = geneweb_date_to_string(person.death_date)  # type: ignore[arg-type]
                                elif getattr(person, "death", None) and getattr(person.death, "date", None):
                                    death_text = geneweb_date_to_string(person.death.date)

                                results.append(
                                    {
                                        "id": str(person_id),
                                        "first_name": str(getattr(person, "first_name", "")),
                                        "surname": str(getattr(person, "surname", "")),
                                        "occupation": str(getattr(person, "occupation", "")),
                                        "sex": str(getattr(person, "sex", "")),
                                        "birth_date": birth_text,
                                        "death_date": death_text,
                                    }
                                )

                        payload = {"base": base_name, "query": q, "results": results}
                        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
                        self.send_response(200)
                        self.send_header("Content-Type", "application/json; charset=utf-8")
                        self.send_header("Cache-Control", "no-store")
                        self.send_header("Content-Length", str(len(body)))
                        self.end_headers()
                        self.wfile.write(body)
                        return

                finally:
                    db_driver.close_database()

            # Endpoint non trouvé
            self.send_error(404, "API endpoint not found")
        except Exception as e:
            logging.getLogger("geneweb.gwd").error(f"API error: {e}")
            self.send_error(500, "Internal Server Error")

    def handle_robots_txt(self):
        """Traiter robots.txt (exactement comme l'original OCaml)"""
        logging.getLogger("geneweb.gwd").info("Robot request")

        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()

        # Essayer de lire le fichier robots
        robots_file = os.path.join(self.gwd_config.etc_prefix, "robots.txt")
        if os.path.exists(robots_file):
            with open(robots_file, "r") as f:
                self.wfile.write(f.read().encode("utf-8"))
        else:
            # Contenu par défaut (exactement comme l'original)
            self.wfile.write(b"User-Agent: *\\nDisallow: /\\n")

    def refuse_log(self, from_addr: str):
        """Refuser une connexion (exactement comme refuse_log OCaml)"""
        logging.getLogger("geneweb.gwd").warning(f"Excluded: {from_addr}")

        self.send_response(403)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(b"<html><body><h1>Forbidden</h1></body></html>")

    def only_log(self, from_addr: str):
        """Logger les connexions non autorisées"""
        logging.getLogger("geneweb.gwd").warning(f"Not in only_addresses: {from_addr}")

        self.send_response(403)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(b"<html><body><h1>Access Restricted</h1></body></html>")

    def is_static_request(self, script_name: str) -> bool:
        """Vérifier si c'est une requête de fichier statique"""
        static_extensions = [".png", ".jpg", ".jpeg", ".gif", ".ico", ".css", ".js", ".txt", ".xml"]
        return any(script_name.endswith(ext) for ext in static_extensions)

    def serve_static_file(self, script_name: str):
        """Servir un fichier statique (équivalent à image_request + misc_request)"""
        # Si c'est un fichier dans /static/, le servir depuis notre dossier static
        if script_name.startswith("static/"):
            static_path = os.path.join(os.path.dirname(__file__), script_name)
            if os.path.exists(static_path) and os.path.isfile(static_path):
                try:
                    with open(static_path, "rb") as f:
                        content = f.read()

                    self.send_response(200)
                    self.send_header("Content-Type", self.get_content_type(script_name))
                    self.send_header("Content-Length", str(len(content)))
                    self.send_header("Cache-Control", "max-age=3600")  # Cache 1 heure
                    self.end_headers()
                    self.wfile.write(content)
                    return
                except Exception as e:
                    logging.getLogger("geneweb.gwd").error(f"Error serving static file {static_path}: {e}")

        # Sinon, chercher dans les répertoires traditionnels GenEWeb
        file_paths = [
            os.path.join(self.gwd_config.images_dir, script_name),
            os.path.join(self.gwd_config.images_prefix, script_name),
            os.path.join(self.gwd_config.etc_prefix, script_name),
        ]

        for file_path in file_paths:
            if os.path.exists(file_path) and os.path.isfile(file_path):
                try:
                    with open(file_path, "rb") as f:
                        content = f.read()

                    self.send_response(200)
                    self.send_header("Content-Type", self.get_content_type(script_name))
                    self.send_header("Content-Length", str(len(content)))
                    self.end_headers()
                    self.wfile.write(content)
                    return
                except Exception as e:
                    logging.getLogger("geneweb.gwd").error(f"Error serving static file {file_path}: {e}")

        # Fichier non trouvé
        self.send_error(404, "File Not Found")

    def get_content_type(self, filename: str) -> str:
        """Déterminer le content-type"""
        ext = os.path.splitext(filename)[1].lower()
        content_types = {
            ".html": "text/html; charset=utf-8",
            ".css": "text/css",
            ".js": "application/javascript",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".ico": "image/x-icon",
            ".txt": "text/plain",
            ".xml": "application/xml",
        }
        return content_types.get(ext, "application/octet-stream")

    def handle_geneweb_request(self, script_name: str, query_string: str, from_addr: str):
        """Traiter une requête GenEWeb (équivalent conf_and_connection OCaml)"""
        try:
            # Si pas de script_name, afficher la liste des bases
            if not script_name:
                self.serve_base_list()
                return

            # Extraire le nom de la base
            if "/" in script_name:
                base_name = script_name.split("/")[0]
            else:
                base_name = script_name

            # Vérifier si la base existe
            base_path = os.path.join(self.gwd_config.database_dir, f"{base_name}.pickle")
            if not os.path.exists(base_path):
                self.send_error(404, f"Database '{base_name}' not found")
                return

            # Charger la base de données
            db_driver = create_database_driver(base_path, "pickle")
            if not db_driver.open_database(read_only=True):
                self.send_error(500, "Cannot open database")
                return

            try:
                # Parser les paramètres de la requête
                params = urllib.parse.parse_qs(query_string)

                # Traitement selon le mode
                mode = params.get("m", [""])[0]

                if mode == "search" or "search" in params:
                    self.handle_search(db_driver, params, base_name)
                elif mode == "stats":
                    self.handle_stats(db_driver, base_name)
                else:
                    self.handle_database_info(db_driver, base_name)

            finally:
                db_driver.close_database()

        except Exception as e:
            logging.getLogger("geneweb.gwd").error(f"Error in GenEWeb request: {e}")
            self.send_error(500, "Internal Server Error")

    def serve_base_list(self):
        """Redirect to frontend - no HTML generation needed"""
        # Redirect to frontend or serve a simple JSON response
        self.send_response(302)
        self.send_header("Location", "/")
        self.end_headers()


    def handle_search(self, db_driver, params, base_name: str):
        """Handle search - redirect to frontend or return JSON"""
        # This should be handled by the React frontend
        self.send_response(302)
        self.send_header("Location", "/")
        self.end_headers()

    def handle_stats(self, db_driver, base_name: str):
        """Handle stats - redirect to frontend or return JSON"""
        # This should be handled by the React frontend
        self.send_response(302)
        self.send_header("Location", "/")
        self.end_headers()

    def handle_database_info(self, db_driver, base_name: str):
        """Handle database info - redirect to frontend or return JSON"""
        # This should be handled by the React frontend
        self.send_response(302)
        self.send_header("Location", "/")
        self.end_headers()


class GWDConfig:
    """Configuration du serveur GWD"""

    def __init__(self):
        # Paramètres par défaut (exactement comme l'original gwd.ml)
        self.selected_addr = None
        self.selected_port = 2317
        self.database_dir = "."
        self.daemon = False
        self.green_color = "#2f6400"
        self.etc_prefix = "etc"
        self.images_prefix = "images"
        self.images_dir = "images"
        self.gw_prefix = ""
        self.excluded_addresses = []
        self.only_addresses = []
        self.no_host_address = False
        self.auth_file = ""
        self.friend_passwd = ""
        self.login_timeout = 1800
        self.trace_failed_passwd = False
        self.conn_timeout = 120
        self.max_pending_requests = 150
        self.n_workers = 20
        # Frontend integration
        self.frontend_dev = False
        self.frontend_dist = None
        self.frontend_dev_url = "http://localhost:5173"
        self.frontend_dir = os.path.join(os.getcwd(), "src", "frontend")
        self.frontend_dev_cmd = None
        self.frontend_dev_autostart = True
        self._vite_process = None


def setup_logging():
    """Configuration du logging (exactement comme l'original)"""
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    logging.basicConfig(level=logging.INFO, format=log_format, handlers=[logging.StreamHandler(sys.stdout)])


def parse_arguments():
    """Parser les arguments (exactement comme l'original gwd)"""
    parser = argparse.ArgumentParser(
        prog="gwd",
        description="GenEWeb Daemon - Genealogy Web Server (Python version)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                          # Start server on port 2317
  %(prog)s -p 8080                  # Start server on port 8080
  %(prog)s -hd /path/to/databases   # Set database directory
  %(prog)s -daemon                  # Run as daemon
  %(prog)s -only 127.0.0.1          # Only accept from localhost

The server will be accessible at:
  http://localhost:PORT/DATABASE_NAME
        """,
    )

    parser.add_argument("-addr", type=str, help="IP address to bind to")
    parser.add_argument("-p", "-port", type=int, default=2317, dest="port", help="Port number (default: 2317)")
    parser.add_argument(
        "-hd", type=str, default=".", dest="database_dir", help="Database directory (default: current directory)"
    )
    parser.add_argument("-daemon", action="store_true", help="Run as daemon (background process)")
    parser.add_argument(
        "-only", type=str, action="append", dest="only_addresses", help="Only accept connections from these addresses"
    )
    parser.add_argument(
        "-exclude", type=str, action="append", dest="excluded_addresses", help="Exclude these addresses"
    )
    parser.add_argument("-no_host_address", action="store_true", help="Do not resolve IP addresses to hostnames")
    parser.add_argument("-auth", type=str, dest="auth_file", help="Authentication file")
    parser.add_argument("-trace_failed_passwd", action="store_true", help="Trace failed password attempts")

    parser.add_argument("--frontend-dev", action="store_true", help="Proxy frontend to Vite dev server and auto-start it")
    parser.add_argument("--frontend-dist", type=str, help="Path to React build directory (dist)")
    parser.add_argument("--frontend-dev-url", type=str, default="http://localhost:5173", help="Vite dev server URL")
    parser.add_argument("--frontend-dir", type=str, help="Path to frontend project root (for dev auto-start)")
    parser.add_argument("--frontend-dev-cmd", type=str, help="Dev command to run (pnpm dev | npm run dev | yarn dev)")
    return parser.parse_args()


def show_startup_info(config: GWDConfig):
    """Afficher les infos de démarrage (exactement comme l'original)"""
    if not config.daemon:
        try:
            import socket

            hostname = socket.gethostname()
        except BaseException:
            hostname = "computer"

        addr = config.selected_addr or hostname
        port = config.selected_port

        print("Possible addresses:")
        print(f"  http://localhost:{port}/base")
        print(f"  http://127.0.0.1:{port}/base")
        print(f"  http://{addr}:{port}/base")
        print('where "base" is the name of the database')
        print("Type Ctrl+C to stop the service")


def daemonize():
    """Daemonize le processus (comme l'original)"""
    try:
        pid = os.fork()
        if pid > 0:
            sys.exit(0)
    except OSError as e:
        print(f"Fork failed: {e}", file=sys.stderr)
        sys.exit(1)

    os.setsid()

    try:
        pid = os.fork()
        if pid > 0:
            sys.exit(0)
    except OSError as e:
        print(f"Second fork failed: {e}", file=sys.stderr)
        sys.exit(1)


def start_frontend_dev_server(config: GWDConfig):
    """Start the frontend development server (Vite)"""
    if not config.frontend_dev_cmd:
        logging.getLogger("geneweb.gwd").warning("Frontend dev command not configured, skipping auto-start")
        return

    frontend_dir = config.frontend_dir
    if not os.path.exists(frontend_dir):
        logging.getLogger("geneweb.gwd").error(f"Frontend directory not found: {frontend_dir}")
        return

    # Check if Vite is already running
    try:
        import urllib.request
        req = urllib.request.Request(config.frontend_dev_url)
        with urllib.request.urlopen(req, timeout=2) as resp:
            if resp.getcode() == 200:
                logging.getLogger("geneweb.gwd").info(f"Frontend dev server already running at {config.frontend_dev_url}")
                return
    except Exception:
        pass  # Server not running, we'll start it

    try:
        logging.getLogger("geneweb.gwd").info(f"Starting frontend dev server in {frontend_dir}")
        logging.getLogger("geneweb.gwd").info(f"Command: {config.frontend_dev_cmd}")
        
        # Start the frontend development server
        cmd_parts = config.frontend_dev_cmd.split()
        config._vite_process = subprocess.Popen(
            cmd_parts,
            cwd=frontend_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )
        
        # Give it a moment to start
        time.sleep(2)
        
        # Check if it started successfully
        if config._vite_process.poll() is None:
            logging.getLogger("geneweb.gwd").info(f"Frontend dev server started successfully (PID: {config._vite_process.pid})")
        else:
            logging.getLogger("geneweb.gwd").error("Frontend dev server failed to start")
            config._vite_process = None
            
    except Exception as e:
        logging.getLogger("geneweb.gwd").error(f"Failed to start frontend dev server: {e}")
        config._vite_process = None


def main():
    """Fonction principale (exactement comme gwd.ml)"""
    args = parse_arguments()

    # Créer la configuration
    config = GWDConfig()
    config.selected_addr = args.addr
    config.selected_port = args.port
    config.database_dir = args.database_dir
    config.daemon = args.daemon
    config.only_addresses = args.only_addresses or []
    config.excluded_addresses = args.excluded_addresses or []
    config.no_host_address = args.no_host_address
    config.auth_file = args.auth_file or ""
    config.trace_failed_passwd = args.trace_failed_passwd

    # Frontend configuration
    config.frontend_dev = args.frontend_dev
    config.frontend_dist = args.frontend_dist
    if args.frontend_dev_url:
        config.frontend_dev_url = args.frontend_dev_url
    if args.frontend_dir:
        config.frontend_dir = args.frontend_dir
    if args.frontend_dev_cmd:
        config.frontend_dev_cmd = args.frontend_dev_cmd

    # Auto-detect frontend dev command if not specified
    if config.frontend_dev and not config.frontend_dev_cmd:
        frontend_dir = config.frontend_dir
        if os.path.exists(os.path.join(frontend_dir, "pnpm-lock.yaml")):
            config.frontend_dev_cmd = "pnpm dev"
        elif os.path.exists(os.path.join(frontend_dir, "yarn.lock")):
            config.frontend_dev_cmd = "yarn dev"
        elif os.path.exists(os.path.join(frontend_dir, "package-lock.json")):
            config.frontend_dev_cmd = "npm run dev"
        else:
            config.frontend_dev_cmd = "npm run dev"  # fallback

    # Configurer les chemins
    if not config.gw_prefix:
        config.gw_prefix = os.getcwd()
    config.etc_prefix = os.path.join(config.gw_prefix, "etc")
    config.images_prefix = os.path.join(config.gw_prefix, "images")
    config.images_dir = config.images_prefix

    # Créer les répertoires
    os.makedirs(config.database_dir, exist_ok=True)
    os.makedirs(config.etc_prefix, exist_ok=True)
    os.makedirs(config.images_prefix, exist_ok=True)

    # Configuration du logging
    setup_logging()

    # Daemonize si nécessaire
    if config.daemon:
        daemonize()

    # Start frontend development server if enabled
    if config.frontend_dev and config.frontend_dev_autostart:
        start_frontend_dev_server(config)

    # Afficher les infos de démarrage
    show_startup_info(config)

    # Créer le handler avec la configuration
    def handler(*args, **kwargs):
        return GeneWebHTTPHandler(*args, gwd_config=config, **kwargs)

    # Gestionnaire de signaux
    def signal_handler(signum, frame):
        print(f"\nReceived signal {signum}, shutting down...")
        try:
            if getattr(config, "_vite_process", None) and config._vite_process.poll() is None:
                config._vite_process.terminate()
        except Exception:
            pass
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Démarrer le serveur
    try:
        with socketserver.TCPServer((config.selected_addr or "", config.selected_port), handler) as httpd:
            logging.getLogger("geneweb.gwd").info(
                f"GenEWeb server listening on {config.selected_addr or 'localhost'}:{config.selected_port}"
            )
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\\nServer stopped by user")
    except Exception as e:
        print(f"Server error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
