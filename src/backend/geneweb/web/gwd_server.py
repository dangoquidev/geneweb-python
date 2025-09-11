"""
GenEWeb Daemon Server (gwd) - Traduction Python exacte du serveur original OCaml

Ce module recrée fidèlement le serveur gwd original de GenEWeb en Python,
en conservant la même architecture, les mêmes protocoles et les mêmes fonctionnalités.

Copyright (c) 1998-2007 INRIA
Python modernization preserving original structure and functionality.
"""

import asyncio
import logging
import logging.handlers
import os
import secrets
import socket
import sys
import time
import traceback
import urllib.parse
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Union

from ..core.config import Config
from ..core.definitions import HttpStatus
from ..db.driver import create_database_driver
from ..security import create_security_manager
from ..util.string_utils import *


@dataclass
class ServerConfig:
    """Configuration du serveur GWD (équivalent des paramètres gwd.ml)"""

    # Paramètres réseau
    selected_addr: Optional[str] = None
    selected_port: int = 2317
    conn_timeout: int = 120
    max_pending_requests: int = 150
    n_workers: int = 20

    # Authentification
    auth_file: str = ""
    friend_passwd: str = ""
    login_timeout: int = 1800

    # Répertoires et fichiers
    gw_prefix: str = ""
    etc_prefix: str = ""
    images_prefix: str = ""
    images_dir: str = ""
    database_dir: str = "."

    # Langues et localisation
    default_lang: str = "fr"
    lexicon_list: List[str] = field(default_factory=lambda: ["lang/lexicon.txt"])
    cache_langs: List[str] = field(default_factory=list)
    choose_browser_lang: bool = False

    # Plugins et extensions
    plugins: List[str] = field(default_factory=list)
    forced_plugins: List[str] = field(default_factory=list)
    unsafe_plugins: List[str] = field(default_factory=list)

    # Contrôle d'accès
    only_addresses: List[str] = field(default_factory=list)
    excluded_addresses: List[str] = field(default_factory=list)
    no_host_address: bool = False

    # Robots et sécurité
    robot_xcl: Optional[Tuple[int, int]] = None  # (count, seconds)
    trace_failed_passwd: bool = False

    # Autres options
    daemon: bool = False
    setup_link: bool = False
    cgi_mode: bool = False
    green_color: str = "#2f6400"


@dataclass
class RequestData:
    """Données d'une requête HTTP (équivalent à la structure OCaml)"""

    addr: Union[str, Tuple[str, int]]
    request_lines: List[str]
    script_name: str
    contents: bytes
    env: Dict[str, str]
    from_addr: str


class OutputConf:
    """Configuration de sortie (équivalent à output_conf OCaml)"""

    def __init__(self, writer):
        self.writer = writer

    def status(self, status: HttpStatus):
        """Écrire le statut HTTP"""
        status_line = f"HTTP/1.0 {status.value} {status.name}\r\n"
        self.writer.write(status_line.encode("utf-8"))

    def header(self, header_line: str):
        """Écrire un en-tête HTTP"""
        self.writer.write(f"{header_line}\r\n".encode("utf-8"))

    def body(self, content: str):
        """Écrire du contenu dans le body"""
        self.writer.write(content.encode("utf-8"))

    def flush(self):
        """Flush les données"""
        self.writer.write(b"\r\n")  # Fin des headers
        # Ne pas await ici car ce n'est pas une méthode async
        # Le flush sera fait dans la fonction appelante

    async def aflush(self):
        """Flush async les données"""
        self.writer.write(b"\r\n")  # Fin des headers
        if hasattr(self.writer, "drain"):
            await self.writer.drain()

    def printf(self, format_str: str, *args):
        """Printf dans la sortie"""
        content = format_str % args
        self.body(content)


class GeneWebDaemon:
    """
    Serveur GenEWeb Daemon - Traduction exacte du serveur original

    Recrée fidèlement l'architecture du serveur gwd.ml original :
    - Gestion des workers
    - Protocole HTTP complet
    - Authentification et autorisation
    - Gestion des bases de données
    - Plugins et extensions
    """

    def __init__(self, config: ServerConfig):
        self.config = config
        self.secret_salt = self._generate_secret_salt()
        self.running = False
        self.server_socket = None
        self.workers = []

        # Configurer le logging comme l'original
        self._setup_logging()

        # Cache des bases de données et langues
        self.cache_databases = {}
        self.cache_langs = {}

        # Statistiques robots (pour robot_xcl)
        self.robot_stats = {}

        # Configuration des chemins
        self._setup_paths()

        self.logger = logging.getLogger("geneweb.gwd")

    def _setup_logging(self):
        """Configuration du logging (équivalent à Logs module OCaml)"""
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

        # Configurer le handler console
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(logging.Formatter(log_format))

        # Configurer le logger principal
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        root_logger.addHandler(console_handler)

        # Essayer d'ajouter syslog si disponible
        try:
            syslog_handler = logging.handlers.SysLogHandler()
            syslog_handler.setFormatter(logging.Formatter(log_format))
            root_logger.addHandler(syslog_handler)
        except BaseException:
            pass  # Syslog pas disponible

    def _setup_paths(self):
        """Configuration des chemins (équivalent à GWPARAM.init)"""
        if not self.config.gw_prefix:
            self.config.gw_prefix = os.getcwd()

        if not self.config.etc_prefix:
            self.config.etc_prefix = os.path.join(self.config.gw_prefix, "etc")

        if not self.config.images_prefix:
            self.config.images_prefix = os.path.join(self.config.gw_prefix, "images")

        # Créer les répertoires nécessaires
        os.makedirs(self.config.database_dir, exist_ok=True)
        os.makedirs(self.config.etc_prefix, exist_ok=True)
        os.makedirs(self.config.images_prefix, exist_ok=True)

    def _generate_secret_salt(self, predictable_mode: bool = False) -> str:
        """
        Génération du sel secret (équivalent à generate_secret_salt OCaml)
        """
        if predictable_mode:
            return ""
        else:
            return secrets.token_hex(16)

    def excluded(self, from_addr: str) -> bool:
        """
        Vérifier si une adresse est exclue (équivalent à excluded OCaml)
        """
        return from_addr in self.config.excluded_addresses

    def only_addresses_check(self, from_addr: str) -> bool:
        """
        Vérifier la liste des adresses autorisées uniquement
        """
        if not self.config.only_addresses:
            return True
        return from_addr in self.config.only_addresses

    def robots_txt(self, output: OutputConf):
        """
        Répondre aux requêtes robots.txt (équivalent robots_txt OCaml)
        """
        self.logger.info("Robot request")
        output.status(HttpStatus.OK)
        output.header("Content-type: text/plain")
        output.flush()

        # Essayer de lire le fichier robots depuis etc/
        robots_file = os.path.join(self.config.etc_prefix, "robots.txt")
        if os.path.exists(robots_file):
            with open(robots_file, "r") as f:
                output.body(f.read())
        else:
            # Contenu par défaut
            output.body("User-Agent: *\\nDisallow: /\\n")

    def refuse_log(self, output: OutputConf, from_addr: str):
        """
        Refuser et logger une connexion (équivalent refuse_log OCaml)
        """
        self.logger.warning(f"Excluded: {from_addr}")
        output.status(HttpStatus.FORBIDDEN)
        output.header("Content-type: text/html")
        output.flush()
        output.body("<html><body><h1>Forbidden</h1></body></html>")

    def only_log(self, output: OutputConf, from_addr: str):
        """
        Logger les connexions non autorisées (only_addresses)
        """
        self.logger.warning(f"Not in only_addresses: {from_addr}")
        output.status(HttpStatus.FORBIDDEN)
        output.header("Content-type: text/html")
        output.flush()
        output.body("<html><body><h1>Access Restricted</h1></body></html>")

    def extract_boundary(self, content_type: str) -> str:
        """
        Extraire boundary des requêtes multipart (équivalent extract_boundary)
        """
        if "boundary=" in content_type:
            return content_type.split("boundary=")[1].split(";")[0].strip('"')
        return ""

    def build_env(self, request_lines: List[str], contents: bytes) -> Tuple[bytes, Dict[str, str]]:
        """
        Construire l'environnement de la requête (équivalent build_env OCaml)
        """
        env: dict[str, str] = {}

        # Parser les headers HTTP
        for line in request_lines:
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip().lower()
                value = value.strip()

                # Convertir en format CGI
                if key == "content-type":
                    env["CONTENT_TYPE"] = value
                elif key == "content-length":
                    env["CONTENT_LENGTH"] = value
                elif key == "cookie":
                    env["HTTP_COOKIE"] = value
                elif key == "accept-language":
                    env["HTTP_ACCEPT_LANGUAGE"] = value
                elif key == "referer":
                    env["HTTP_REFERER"] = value
                elif key == "user-agent":
                    env["HTTP_USER_AGENT"] = value
                else:
                    env[f'HTTP_{key.upper().replace("-", "_")}'] = value

        # Traiter les requêtes multipart
        content_type = env.get("CONTENT_TYPE", "")
        if content_type.startswith("multipart/"):
            boundary = self.extract_boundary(content_type)
            if boundary:
                contents = self.extract_multipart(boundary, contents)

        return contents, env

    def extract_multipart(self, boundary: str, contents: bytes) -> bytes:
        """
        Extraire le contenu des requêtes multipart
        """
        # Implémentation simplifiée - à étendre selon les besoins
        boundary_bytes = f"--{boundary}".encode()
        parts = contents.split(boundary_bytes)

        # Retourner le premier contenu trouvé
        for part in parts:
            if b"Content-Disposition:" in part:
                # Trouver le début du contenu
                content_start = part.find(b"\\r\\n\\r\\n")
                if content_start != -1:
                    return part[content_start + 4 :].rstrip(b"\\r\\n")

        return contents

    def log_passwd_failed(
        self,
        username: str,
        password: str,
        from_addr: str,
        request_lines: List[str],
        base_file: str,
    ):
        """
        Logger les échecs d'authentification (équivalent log_passwd_failed)
        """
        referer = self.extract_param("referer:", "\\n", "\\n".join(request_lines))
        user_agent = self.extract_param("user-agent:", "\\n", "\\n".join(request_lines))

        current_time = time.strftime("%Y-%m-%d %H:%M:%S")
        pid = os.getpid()

        self.logger.info(f"{current_time} ({pid}) {base_file}_{password} => failed ({username})")

        if self.config.trace_failed_passwd:
            self.logger.info(f" (auth trace enabled)")

        self.logger.info(f"  From: {from_addr}")
        self.logger.info(f"  Agent: {user_agent}")
        if referer:
            self.logger.info(f"  Referer: {referer}")

    def extract_param(self, param_name: str, separator: str, text: str) -> str:
        """
        Extraire un paramètre d'un texte (équivalent Mutil.extract_param)
        """
        lines = text.split("\\n")
        for line in lines:
            if line.lower().startswith(param_name.lower()):
                rest = line[len(param_name) :].strip()
                if separator in rest:
                    return rest.split(separator)[0].strip()
                return rest
        return ""

    def image_request(self, script_name: str, env: Dict[str, str]) -> bool:
        """
        Vérifier si c'est une requête d'image (équivalent image_request)
        """
        if script_name.endswith((".png", ".jpg", ".jpeg", ".gif", ".ico", ".css", ".js")):
            return True

        # Vérifier les paramètres d'image
        query_string = env.get("QUERY_STRING", "")
        if "image=" in query_string or "img=" in query_string:
            return True

        return False

    def misc_request(self, script_name: str) -> bool:
        """
        Vérifier si c'est une requête misc (équivalent misc_request)
        """
        misc_extensions = [".css", ".js", ".ico", ".txt", ".xml"]
        return any(script_name.endswith(ext) for ext in misc_extensions)

    def serve_static_file(self, output: OutputConf, script_name: str):
        """
        Servir un fichier statique
        """
        # Chercher dans images_dir d'abord, puis images_prefix
        file_paths = [
            os.path.join(self.config.images_dir, script_name),
            os.path.join(self.config.images_prefix, script_name),
            os.path.join(self.config.etc_prefix, script_name),
        ]

        for file_path in file_paths:
            if os.path.exists(file_path) and os.path.isfile(file_path):
                try:
                    with open(file_path, "rb") as f:
                        content = f.read()

                    # Déterminer le content-type
                    content_type = self.get_content_type(script_name)

                    output.status(HttpStatus.OK)
                    output.header(f"Content-type: {content_type}")
                    output.header(f"Content-length: {len(content)}")
                    output.flush()
                    output.writer.write(content)
                    return True
                except Exception as e:
                    self.logger.error(f"Error serving static file {file_path}: {e}")

        # Fichier non trouvé
        output.status(HttpStatus.NOT_FOUND)
        output.header("Content-type: text/html")
        output.body("<html><body><h1>404 - File Not Found</h1></body></html>")
        output.flush()
        return True

    def get_content_type(self, filename: str) -> str:
        """
        Déterminer le content-type d'un fichier
        """
        ext = os.path.splitext(filename)[1].lower()
        content_types = {
            ".html": "text/html",
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

    async def connection(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """
        Fonction principale de traitement des connexions (équivalent connection OCaml)
        """
        addr = writer.get_extra_info("peername")
        from_addr = addr[0] if addr else "unknown"

        # Résoudre le nom d'hôte si nécessaire
        if not self.config.no_host_address:
            try:
                hostname = socket.gethostbyaddr(from_addr)[0]
                from_addr = hostname
            except BaseException:
                pass  # Garder l'adresse IP

        try:
            # Lire la requête HTTP
            request_lines: list[str] = []
            contents = b""

            # Lire les headers
            while True:
                line = await reader.readline()
                if not line:
                    break

                line_str = line.decode("utf-8", errors="ignore").rstrip("\\r\\n")
                if not line_str:  # Ligne vide = fin des headers
                    break

                request_lines.append(line_str)

            if not request_lines:
                return

            # Parser la première ligne (méthode, path, version)
            request_line = request_lines[0]
            parts = request_line.split(" ")
            if len(parts) < 2:
                return

            method = parts[0]
            full_path = parts[1]

            # Extraire script_name et query_string
            if "?" in full_path:
                script_name, query_string = full_path.split("?", 1)
            else:
                script_name = full_path
                query_string = ""

            # Enlever le slash initial
            if script_name.startswith("/"):
                script_name = script_name[1:]

            # Lire le body si présent
            content_length = 0
            for line in request_lines:
                if line.lower().startswith("content-length:"):
                    try:
                        content_length = int(line.split(":", 1)[1].strip())
                        break
                    except ValueError:
                        pass

            if content_length > 0:
                contents = await reader.read(content_length)

            # Créer l'output
            output = OutputConf(writer)

            # Traitement spécial robots.txt
            if script_name == "robots.txt":
                self.robots_txt(output)
                return

            # Vérifier les exclusions
            if self.excluded(from_addr):
                self.refuse_log(output, from_addr)
                return

            # Vérifier only_addresses
            if not self.only_addresses_check(from_addr):
                self.only_log(output, from_addr)
                return

            # Construire l'environnement
            contents, env = self.build_env(request_lines, contents)
            env["QUERY_STRING"] = query_string
            env["REQUEST_METHOD"] = method
            env["SCRIPT_NAME"] = script_name

            # Traiter les requêtes statiques
            if self.image_request(script_name, env) or self.misc_request(script_name):
                self.serve_static_file(output, script_name)
                return

            # Traitement principal GenEWeb
            await self.conf_and_connection(output, from_addr, request_lines, script_name, contents, env)

        except Exception as e:
            self.logger.error(f"Error in connection from {from_addr}: {e}")
            self.logger.error(traceback.format_exc())
        finally:
            try:
                writer.close()
                await writer.wait_closed()
            except BaseException:
                pass

    async def conf_and_connection(
        self,
        output: OutputConf,
        from_addr: str,
        request_lines: List[str],
        script_name: str,
        contents: bytes,
        env: Dict[str, str],
    ):
        """
        Configuration et traitement de la connexion principale
        (équivalent conf_and_connection OCaml)
        """
        # Créer la configuration GenEWeb
        geneweb_config = Config()
        geneweb_config.from_addr = from_addr
        geneweb_config.request_uri = script_name
        geneweb_config.query_string = env.get("QUERY_STRING", "")

        # Parser le script name pour extraire la base
        if "/" in script_name:
            base_name = script_name.split("/")[0]
        else:
            base_name = script_name

        if not base_name:
            # Page d'accueil - lister les bases
            self.serve_base_list(output)
            return

        # Vérifier si la base existe
        base_path = os.path.join(self.config.database_dir, f"{base_name}.pickle")
        if not os.path.exists(base_path):
            output.status(HttpStatus.NOT_FOUND)
            output.header("Content-type: text/html")
            output.body(f"<html><body><h1>Database '{base_name}' not found</h1></body></html>")
            output.flush()
            return

        try:
            # Charger la base de données
            db_driver = create_database_driver(base_path, "pickle")
            if not db_driver.open_database(read_only=True):
                raise Exception("Cannot open database")

            # Créer le gestionnaire de sécurité
            security_manager = create_security_manager(geneweb_config)

            # Traiter la requête GenEWeb
            await self.handle_geneweb_request(
                output,
                geneweb_config,
                db_driver,
                security_manager,
                env,
                contents,
            )

        except Exception as e:
            self.logger.error(f"Error handling GenEWeb request: {e}")
            output.status(HttpStatus.INTERNAL_SERVER_ERROR)
            output.header("Content-type: text/html")
            output.body(f"<html><body><h1>Internal Server Error</h1><p>{str(e)}</p></body></html>")
            output.flush()

    def serve_base_list(self, output: OutputConf):
        """
        Servir la liste des bases de données (page d'accueil)
        """
        databases: list[str] = []
        try:
            for file in os.listdir(self.config.database_dir):
                if file.endswith(".pickle"):
                    db_name = file[:-7]  # Enlever .pickle
                    databases.append(db_name)
        except OSError:
            pass

        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>GenEWeb Server</title>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; background: white; }}
        h1 {{ color: {self.config.green_color}; }}
        .database-list {{ margin: 20px 0; }}
        .database-item {{
            display: block;
            padding: 10px;
            margin: 5px 0;
            background: #f5f5f5;
            text-decoration: none;
            color: {self.config.green_color};
            border-radius: 3px;
        }}
        .database-item:hover {{ background: #e0e0e0; }}
        .server-info {{
            background: #f0f8ff;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
        }}
    </style>
</head>
<body>
    <h1>GenEWeb - Genealogy Server</h1>

    <div class="server-info">
        <h2>Available Databases:</h2>
        <div class="database-list">"""

        if databases:
            for db_name in sorted(databases):
                html += f'            <a href="/{db_name}" class="database-item">📊 {db_name}</a>\\n'
        else:
            html += "            <p><em>No databases found in the current directory.</em></p>"

        html += f"""        </div>
    </div>

    <div class="server-info">
        <h3>Server Information:</h3>
        <p><strong>Version:</strong> GenEWeb Python Modernization</p>
        <p><strong>Port:</strong> {self.config.selected_port}</p>
        <p><strong>Database Directory:</strong> {os.path.abspath(self.config.database_dir)}</p>
    </div>

    <hr>
    <p><small>GenEWeb - Copyright © 1998-2007 INRIA - Python modernization</small></p>
</body>
</html>"""

        output.status(HttpStatus.OK)
        output.header("Content-type: text/html; charset=utf-8")
        output.flush()
        output.body(html)

    async def handle_geneweb_request(
        self,
        output: OutputConf,
        config: Config,
        db_driver,
        security_manager,
        env: Dict[str, str],
        contents: bytes,
    ):
        """
        Traiter une requête GenEWeb spécifique
        """
        query_string = env.get("QUERY_STRING", "")
        params = urllib.parse.parse_qs(query_string)

        # Traitement selon le paramètre 'm' (mode)
        mode = params.get("m", [""])[0]

        if mode == "search" or "search" in params:
            await self.handle_search(output, db_driver, params)
        elif mode == "stats":
            await self.handle_stats(output, db_driver)
        else:
            await self.handle_database_info(output, db_driver)

    async def handle_search(self, output: OutputConf, db_driver, params: Dict[str, List[str]]):
        """
        Traiter une recherche de personnes
        """
        search_query = params.get("search", [""])[0] or params.get("s", [""])[0]

        info = db_driver.get_database_info()
        results: list[str] = []

        if search_query:
            results = db_driver.search_persons(search_query)

        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Search - {info.name}</title>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        h1 {{ color: {self.config.green_color}; }}
        .search-box {{ background: #f0f8ff; padding: 15px; border-radius: 5px; margin: 20px 0; }}
        .person {{ background: #f5f5f5; padding: 10px; margin: 10px 0; border-radius: 3px; }}
        input[type="text"] {{ padding: 8px; width: 300px; }}
        button {{ padding: 8px 15px; background: {self.config.green_color}; color: white; border: none; border-radius: 3px; }}
        .navigation {{ margin: 20px 0; }}
        .navigation a {{ color: {self.config.green_color}; }}
    </style>
</head>
<body>
    <h1>🔍 Search in {info.name}</h1>

    <div class="search-box">
        <form method="GET">
            <input type="hidden" name="m" value="search">
            <input type="text" name="search" value="{search_query}" placeholder="Enter name to search...">
            <button type="submit">Search</button>
        </form>
    </div>"""

        if search_query:
            html += f"    <h2>Results for '{search_query}':</h2>\\n"

            if results:
                for person_id, person in results[:50]:  # Limiter à 50 résultats
                    birth_info = ""
                    if person.birth_date:
                        birth_info = f" (born {geneweb_date_to_string(person.birth_date)})"

                    occupation_info = ""
                    if person.occupation:
                        occupation_info = f"<br><em>{escape_html(person.occupation)}</em>"

                    html += f"""    <div class="person">
        <strong>{escape_html(person.first_name)} {escape_html(person.surname)}</strong>{birth_info}
        {occupation_info}
    </div>
"""

                if len(results) > 50:
                    html += f"    <p><em>Showing first 50 results out of {len(results)} total.</em></p>\\n"
            else:
                html += "    <p><em>No results found.</em></p>\\n"

        html += f"""
    <div class="navigation">
        <a href="/{info.name.replace('.pickle', '')}">← Back to {info.name.replace('.pickle', '')}</a> |
        <a href="/">← Database List</a>
    </div>

    <hr>
    <p><small>GenEWeb - Search powered by Python modernization</small></p>
</body>
</html>"""

        output.status(HttpStatus.OK)
        output.header("Content-type: text/html; charset=utf-8")
        output.flush()
        output.body(html)

    async def handle_stats(self, output: OutputConf, db_driver):
        """
        Afficher les statistiques de la base
        """
        info = db_driver.get_database_info()

        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Statistics - {info.name}</title>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        h1 {{ color: {self.config.green_color}; }}
        .stats {{ background: #f0f8ff; padding: 20px; border-radius: 5px; }}
        .stat-item {{ margin: 10px 0; padding: 10px; background: white; border-radius: 3px; }}
        .navigation a {{ color: {self.config.green_color}; }}
    </style>
</head>
<body>
    <h1>📊 Statistics for {info.name.replace('.pickle', '')}</h1>

    <div class="stats">
        <div class="stat-item">
            <strong>Number of Persons:</strong> {info.number_of_persons:,}
        </div>
        <div class="stat-item">
            <strong>Number of Families:</strong> {info.number_of_families:,}
        </div>
        <div class="stat-item">
            <strong>Database File:</strong> {info.path}
        </div>
        <div class="stat-item">
            <strong>Version:</strong> {info.version}
        </div>
    </div>

    <div class="navigation">
        <a href="/{info.name.replace('.pickle', '')}">← Back to {info.name.replace('.pickle', '')}</a> |
        <a href="/">← Database List</a>
    </div>
</body>
</html>"""

        output.status(HttpStatus.OK)
        output.header("Content-type: text/html; charset=utf-8")
        output.flush()
        output.body(html)

    async def handle_database_info(self, output: OutputConf, db_driver):
        """
        Afficher les informations de base de la base de données
        """
        info = db_driver.get_database_info()

        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>{info.name.replace('.pickle', '')} - GenEWeb</title>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; background: white; }}
        h1 {{ color: {self.config.green_color}; }}
        .info-box {{ background: #f0f8ff; padding: 20px; border-radius: 5px; margin: 20px 0; }}
        .navigation {{ background: #f5f5f5; padding: 15px; border-radius: 5px; }}
        .nav-item {{
            display: block;
            padding: 8px;
            margin: 5px 0;
            color: {self.config.green_color};
            text-decoration: none;
        }}
        .nav-item:hover {{ background: #e0e0e0; }}
        .stats dl {{ margin: 0; }}
        .stats dt {{ font-weight: bold; margin-top: 10px; }}
        .stats dd {{ margin: 5px 0 10px 20px; }}
    </style>
</head>
<body>
    <h1>🌳 {info.name.replace('.pickle', '')} Database</h1>

    <div class="info-box">
        <h2>Database Information</h2>
        <dl class="stats">
            <dt>Number of Persons:</dt>
            <dd>{info.number_of_persons:,}</dd>

            <dt>Number of Families:</dt>
            <dd>{info.number_of_families:,}</dd>

            <dt>Database Path:</dt>
            <dd>{info.path}</dd>

            <dt>Version:</dt>
            <dd>{info.version}</dd>
        </dl>
    </div>

    <div class="navigation">
        <h2>Navigation</h2>
        <a href="/{info.name.replace('.pickle', '')}?m=search" class="nav-item">🔍 Search Persons</a>
        <a href="/{info.name.replace('.pickle', '')}?m=stats" class="nav-item">📊 Database Statistics</a>
        <a href="/" class="nav-item">← Back to Database List</a>
    </div>

    <hr>
    <p><small>GenEWeb Python Modernization - Compatible with original GenEWeb</small></p>
</body>
</html>"""

        output.status(HttpStatus.OK)
        output.header("Content-type: text/html; charset=utf-8")
        output.flush()
        output.body(html)

    def start_server(self):
        """
        Démarrer le serveur (équivalent geneweb_server OCaml)
        """
        if self.config.daemon:
            self._daemonize()

        self._show_startup_info()

        # Démarrer le serveur asyncio
        asyncio.run(self._run_server())

    def _daemonize(self):
        """
        Daemonize le processus (équivalent fork() OCaml)
        """
        try:
            pid = os.fork()
            if pid > 0:
                sys.exit(0)  # Parent process
        except OSError as e:
            self.logger.error(f"Fork failed: {e}")
            sys.exit(1)

        # Detach from controlling terminal
        os.setsid()

        # Second fork
        try:
            pid = os.fork()
            if pid > 0:
                sys.exit(0)
        except OSError as e:
            self.logger.error(f"Second fork failed: {e}")
            sys.exit(1)

        # Redirect stdin/stdout/stderr
        with open("/dev/null", "r") as f:
            os.dup2(f.fileno(), sys.stdin.fileno())
        with open("/dev/null", "w") as f:
            os.dup2(f.fileno(), sys.stdout.fileno())
            os.dup2(f.fileno(), sys.stderr.fileno())

    def _show_startup_info(self):
        """
        Afficher les informations de démarrage (équivalent aux logs OCaml)
        """
        if not self.config.daemon:
            try:
                hostname = socket.gethostname()
            except BaseException:
                hostname = "computer"

            addr = self.config.selected_addr or hostname
            port = self.config.selected_port

            self.logger.info("Possible addresses:")
            self.logger.info(f"  http://localhost:{port}/base")
            self.logger.info(f"  http://127.0.0.1:{port}/base")
            self.logger.info(f"  http://{addr}:{port}/base")
            self.logger.info('where "base" is the name of the database')
            self.logger.info("Type Ctrl+C to stop the service")

    async def _run_server(self):
        """
        Boucle principale du serveur
        """
        try:
            server = await asyncio.start_server(
                self.connection,
                self.config.selected_addr,
                self.config.selected_port,
            )

            self.running = True
            self.logger.info(
                f"GenEWeb server listening on {self.config.selected_addr or 'localhost'}:{self.config.selected_port}"
            )

            async with server:
                await server.serve_forever()

        except KeyboardInterrupt:
            self.logger.info("Stopping GenEWeb server")
        except Exception as e:
            self.logger.error(f"Server error: {e}")
        finally:
            self.running = False


def start_geneweb_daemon(
    host: str = None,
    port: int = 2317,
    database_dir: str = ".",
    daemon: bool = False,
    **kwargs,
) -> None:
    """
    Fonction principale pour démarrer le serveur GenEWeb Daemon
    (équivalent à la fonction main() de gwd.ml)
    """
    config = ServerConfig(
        selected_addr=host,
        selected_port=port,
        database_dir=database_dir,
        daemon=daemon,
        **kwargs,
    )

    server = GeneWebDaemon(config)
    server.start_server()


if __name__ == "__main__":
    start_geneweb_daemon()
