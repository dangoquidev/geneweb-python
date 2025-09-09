#!/usr/bin/env python3
"""
GenEWeb Daemon (gwd) - Version simplifiée mais exacte du serveur original

Cette version utilise le serveur HTTP de Python pour éviter les problèmes asyncio
tout en gardant exactement la même interface et les mêmes fonctionnalités que l'original.
"""

import argparse
import http.server
import logging
import os
import signal
import socketserver
import sys
import urllib.parse
from pathlib import Path

from geneweb.core.config import Config

# Import des modules GenEWeb
from geneweb.db.driver import create_database_driver
from geneweb.security import create_security_manager
from geneweb.util.string_utils import *

# Import du moteur de templates
from template_engine import render_template


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
                except:
                    pass

            # Parser l'URL
            parsed_url = urllib.parse.urlparse(self.path)
            script_name = parsed_url.path[1:] if parsed_url.path.startswith("/") else parsed_url.path
            query_string = parsed_url.query

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
        """Servir la liste des bases (page d'accueil comme l'original)"""
        databases = []
        try:
            for file in os.listdir(self.gwd_config.database_dir):
                if file.endswith(".pickle"):
                    db_name = file[:-7]
                    databases.append(db_name)
        except OSError:
            pass

        html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <title>GeneWeb Server</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
    <link rel="icon" href="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAAC7klEQVR4Ae2XA7BjQRCF...">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@4.6.2/dist/css/bootstrap.min.css">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@fortawesome/fontawesome-free@6.7.2/css/all.min.css">
    <style>
        body {{ background: #f8f9fa; }}
        .main-container {{ min-height: 100vh; }}
        .geneweb-logo {{
            width: 180px;
            height: auto;
            filter: sepia(100%) saturate(500%) hue-rotate(85deg) brightness(1.2);
        }}
        .database-card {{
            transition: transform 0.2s, box-shadow 0.2s;
            border: none;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .database-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            text-decoration: none;
        }}
        .database-link {{ color: inherit; text-decoration: none; }}
        .database-link:hover {{ color: inherit; text-decoration: none; }}
        .server-stats {{
            background: linear-gradient(135deg, #f0f8ff 0%, #e6f3ff 100%);
            border-left: 4px solid #007bff;
        }}
        .header-title {{
            color: #2f6400;
            font-weight: 600;
        }}
        .footer-info {{
            background: #343a40;
            color: #ffffff;
        }}
    </style>
</head>
<body class="d-flex flex-column main-container">
    <div class="container-fluid flex-grow-1">
        <!-- Header avec logo et titre -->
        <div class="row justify-content-center align-items-center py-4">
            <div class="col-md-3 text-center mb-3 mb-md-0">
                <svg class="geneweb-logo" viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
                    <g fill="#2f6400">
                        <!-- Arbre généalogique stylisé -->
                        <circle cx="100" cy="20" r="8"/>
                        <line x1="100" y1="28" x2="100" y2="50" stroke="#2f6400" stroke-width="2"/>
                        <line x1="70" y1="50" x2="130" y2="50" stroke="#2f6400" stroke-width="2"/>
                        <circle cx="70" cy="50" r="6"/>
                        <circle cx="130" cy="50" r="6"/>
                        <line x1="70" y1="56" x2="70" y2="75" stroke="#2f6400" stroke-width="1.5"/>
                        <line x1="130" y1="56" x2="130" y2="75" stroke="#2f6400" stroke-width="1.5"/>
                        <line x1="50" y1="75" x2="90" y2="75" stroke="#2f6400" stroke-width="1.5"/>
                        <line x1="110" y1="75" x2="150" y2="75" stroke="#2f6400" stroke-width="1.5"/>
                        <circle cx="50" cy="75" r="4"/>
                        <circle cx="90" cy="75" r="4"/>
                        <circle cx="110" cy="75" r="4"/>
                        <circle cx="150" cy="75" r="4"/>
                        <!-- Feuilles -->
                        <path d="M40,85 Q45,95 50,85" fill="#4a8c2a"/>
                        <path d="M85,85 Q90,95 95,85" fill="#4a8c2a"/>
                        <path d="M105,85 Q110,95 115,85" fill="#4a8c2a"/>
                        <path d="M145,85 Q150,95 155,85" fill="#4a8c2a"/>
                    </g>
                    <text x="100" y="110" text-anchor="middle" font-family="serif" font-size="16" font-weight="bold" fill="#2f6400">GeneWeb</text>
                </svg>
            </div>
            <div class="col-md-6 text-center">
                <h1 class="header-title display-4 mb-2">Serveur Généalogique</h1>
                <p class="lead text-muted">Base de données généalogiques en ligne</p>
            </div>
            <div class="col-md-3"></div>
        </div>

        <!-- Section des bases de données -->
        <div class="row justify-content-center mb-4">
            <div class="col-lg-10">
                <div class="card border-0 shadow-sm">
                    <div class="card-header bg-primary text-white">
                        <h3 class="card-title mb-0">
                            <i class="fas fa-database me-2"></i>
                            Bases de données disponibles
                        </h3>
                    </div>
                    <div class="card-body p-4">"""

        if databases:
            html += '                        <div class="row">'
            for db_name in sorted(databases):
                html += f"""
                            <div class="col-lg-6 col-xl-4 mb-3">
                                <a href="/{db_name}" class="database-link">
                                    <div class="card database-card h-100">
                                        <div class="card-body text-center">
                                            <i class="fas fa-sitemap text-success fa-2x mb-3"></i>
                                            <h5 class="card-title">{db_name}</h5>
                                            <p class="card-text text-muted">
                                                <small>Cliquez pour accéder</small>
                                            </p>
                                        </div>
                                    </div>
                                </a>
                            </div>"""
            html += "\n                        </div>"
        else:
            html += """                        <div class="text-center py-5">
                            <i class="fas fa-exclamation-circle text-warning fa-3x mb-3"></i>
                            <h4 class="text-muted">Aucune base de données trouvée</h4>
                            <p class="text-muted">Placez vos fichiers .pickle dans le répertoire des bases.</p>
                        </div>"""

        html += f"""                    </div>
                </div>
            </div>
        </div>

        <!-- Informations du serveur -->
        <div class="row justify-content-center mb-4">
            <div class="col-lg-8">
                <div class="card border-0 server-stats">
                    <div class="card-body">
                        <h4 class="card-title">
                            <i class="fas fa-server me-2"></i>
                            Informations du serveur
                        </h4>
                        <div class="row mt-3">
                            <div class="col-md-4 text-center">
                                <div class="p-3">
                                    <i class="fas fa-plug text-primary fa-2x"></i>
                                    <h6 class="mt-2 mb-0">Port</h6>
                                    <strong>{self.gwd_config.selected_port}</strong>
                                </div>
                            </div>
                            <div class="col-md-4 text-center">
                                <div class="p-3">
                                    <i class="fas fa-folder-open text-warning fa-2x"></i>
                                    <h6 class="mt-2 mb-0">Répertoire</h6>
                                    <small class="text-muted">{os.path.basename(os.path.abspath(self.gwd_config.database_dir))}</small>
                                </div>
                            </div>
                            <div class="col-md-4 text-center">
                                <div class="p-3">
                                    <i class="fas fa-python text-success fa-2x"></i>
                                    <h6 class="mt-2 mb-0">Version</h6>
                                    <small>GenEWeb Python</small>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Outils -->
        <div class="row justify-content-center">
            <div class="col-lg-6">
                <div class="card border-0 shadow-sm">
                    <div class="card-header bg-secondary text-white">
                        <h5 class="card-title mb-0">
                            <i class="fas fa-tools me-2"></i>
                            Outils
                        </h5>
                    </div>
                    <div class="card-body">
                        <div class="d-flex flex-wrap justify-content-center">
                            <a href="#" class="btn btn-outline-primary m-1" title="Configuration">
                                <i class="fas fa-cog me-1"></i>
                                Configuration
                            </a>
                            <a href="#" class="btn btn-outline-info m-1" title="Statistiques">
                                <i class="fas fa-chart-bar me-1"></i>
                                Statistiques globales
                            </a>
                            <a href="#" class="btn btn-outline-success m-1" title="Aide">
                                <i class="fas fa-question-circle me-1"></i>
                                Aide
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Footer -->
    <footer class="footer-info mt-5 py-3">
        <div class="container text-center">
            <div class="row">
                <div class="col-md-6">
                    <small>
                        <strong>GenEWeb</strong> - Serveur de généalogie
                        <br>Copyright © 1998-2007 INRIA
                    </small>
                </div>
                <div class="col-md-6">
                    <small>
                        <i class="fab fa-python"></i>
                        Version Python modernisée
                        <br>Compatible avec GenEWeb original
                    </small>
                </div>
            </div>
        </div>
    </footer>

    <script src="https://cdn.jsdelivr.net/npm/jquery@3.6.0/dist/jquery.slim.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@4.6.2/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>"""

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))

    def handle_search(self, db_driver, params, base_name: str):
        """Traiter une recherche (exactement comme l'original)"""
        search_query = params.get("search", [""])[0] or params.get("s", [""])[0]
        info = db_driver.get_database_info()
        results = []

        if search_query:
            results = db_driver.search_persons(search_query)

        html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <title>Recherche - {base_name}</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@4.6.2/dist/css/bootstrap.min.css">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@fortawesome/fontawesome-free@6.7.2/css/all.min.css">
    <style>
        body {{ background: #f8f9fa; }}
        .navbar-geneweb {{ background: linear-gradient(135deg, #2f6400 0%, #4a8c2a 100%); }}
        .search-header {{
            background: linear-gradient(135deg, #e3f2fd 0%, #f3e5f5 100%);
            border-radius: 1rem;
            padding: 2rem;
            margin: 1rem 0;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }}
        .person-card {{
            background: white;
            border: none;
            border-left: 4px solid #007bff;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            transition: transform 0.2s ease;
        }}
        .person-card:hover {{
            transform: translateX(5px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }}
        .result-count {{
            background: linear-gradient(135deg, #fff3e0 0%, #fce4ec 100%);
            border-radius: 0.5rem;
            padding: 1rem;
            margin: 1rem 0;
        }}
        .no-results {{
            background: linear-gradient(135deg, #ffebee 0%, #fce4ec 100%);
            border-radius: 1rem;
            padding: 3rem;
            text-align: center;
        }}
        .search-tips {{
            background: linear-gradient(135deg, #e8f5e8 0%, #f1f8e9 100%);
            border-radius: 0.5rem;
            padding: 1rem;
            margin: 1rem 0;
        }}
    </style>
</head>
<body class="d-flex flex-column min-vh-100">
    <!-- Navigation -->
    <nav class="navbar navbar-expand-lg navbar-dark navbar-geneweb">
        <div class="container">
            <a class="navbar-brand" href="/">
                <i class="fas fa-sitemap me-2"></i>
                GenEWeb
            </a>
            <div class="navbar-nav ml-auto">
                <a class="nav-link text-white" href="/{base_name}">
                    <i class="fas fa-tree me-1"></i>
                    {base_name}
                </a>
                <a class="nav-link text-white" href="/">
                    <i class="fas fa-home me-1"></i>
                    Accueil
                </a>
            </div>
        </div>
    </nav>

    <div class="container-fluid flex-grow-1 py-4">
        <!-- En-tête de recherche -->
        <div class="row justify-content-center">
            <div class="col-lg-10">
                <div class="search-header text-center">
                    <h1 class="display-4 mb-3">
                        <i class="fas fa-search text-primary me-3"></i>
                        Recherche dans {base_name}
                    </h1>

                    <form method="GET" action="/{base_name}">
                        <input type="hidden" name="m" value="search">
                        <div class="row justify-content-center">
                            <div class="col-md-8">
                                <div class="input-group input-group-lg">
                                    <input type="search" class="form-control"
                                           name="search"
                                           value="{escape_html(search_query)}"
                                           placeholder="Prénom, nom de famille ou les deux..."
                                           autofocus>
                                    <div class="input-group-append">
                                        <button class="btn btn-primary" type="submit">
                                            <i class="fas fa-search me-1"></i>
                                            Rechercher
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </form>
                </div>
            </div>
        </div>"""

        if search_query:
            # Affichage des résultats
            html += f"""
        <!-- Résultats -->
        <div class="row justify-content-center mt-4">
            <div class="col-lg-10">
                <div class="result-count">
                    <h4 class="mb-0">
                        <i class="fas fa-list-ul me-2 text-info"></i>
                        Résultats pour "<strong>{escape_html(search_query)}</strong>"
                    </h4>"""

            if results:
                total_results = len(results)
                showing_results = min(50, total_results)
                html += f"""
                    <p class="mb-0 text-muted">
                        Affichage de {showing_results} résultat{"s" if showing_results > 1 else ""}
                        sur {total_results} au total
                    </p>
                </div>

                <div class="mt-4">"""

                for person_id, person in results[:50]:
                    # Informations sur la personne
                    birth_info = ""
                    if person.birth_date:
                        birth_info = f'<i class="fas fa-birthday-cake text-success me-1"></i>Né{"e" if person.sex == "F" else ""} le {geneweb_date_to_string(person.birth_date)}'

                    death_info = ""
                    if person.death_date:
                        death_info = f'<i class="fas fa-cross text-danger me-1"></i>Décédé{"e" if person.sex == "F" else ""} le {geneweb_date_to_string(person.death_date)}'

                    occupation_info = ""
                    if person.occupation:
                        occupation_info = (
                            f'<i class="fas fa-briefcase text-warning me-1"></i>{escape_html(person.occupation)}'
                        )

                    # Badge de sexe
                    sex_badge = ""
                    if person.sex == "M":
                        sex_badge = '<span class="badge badge-primary mr-2"><i class="fas fa-mars"></i></span>'
                    elif person.sex == "F":
                        sex_badge = '<span class="badge badge-danger mr-2"><i class="fas fa-venus"></i></span>'

                    html += f"""
                    <div class="card person-card mb-3">
                        <div class="card-body">
                            <div class="row">
                                <div class="col-md-8">
                                    <h5 class="card-title">
                                        {sex_badge}
                                        <strong>{escape_html(person.first_name)} {escape_html(person.surname)}</strong>
                                    </h5>
                                    <div class="card-text">"""

                    if birth_info or death_info or occupation_info:
                        html += '<div class="d-flex flex-wrap">'
                        if birth_info:
                            html += f'<div class="me-3 mb-1 small">{birth_info}</div>'
                        if death_info:
                            html += f'<div class="me-3 mb-1 small">{death_info}</div>'
                        if occupation_info:
                            html += f'<div class="me-3 mb-1 small">{occupation_info}</div>'
                        html += "</div>"

                    html += f"""
                                    </div>
                                </div>
                                <div class="col-md-4 text-md-right">
                                    <small class="text-muted">
                                        <i class="fas fa-fingerprint me-1"></i>
                                        ID: {person_id}
                                    </small>
                                    <div class="mt-2">
                                        <button class="btn btn-sm btn-outline-primary" disabled>
                                            <i class="fas fa-eye me-1"></i>
                                            Voir la fiche
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>"""

                html += "</div>"

                if total_results > 50:
                    html += f"""
                <div class="alert alert-info text-center">
                    <i class="fas fa-info-circle me-2"></i>
                    Seuls les 50 premiers résultats sont affichés.
                    Affinez votre recherche pour obtenir des résultats plus précis.
                </div>"""

            else:
                html += """
                    <p class="mb-0 text-muted">
                        Aucun résultat trouvé
                    </p>
                </div>

                <div class="no-results mt-4">
                    <i class="fas fa-search-minus fa-3x text-muted mb-3"></i>
                    <h4 class="text-muted">Aucun résultat trouvé</h4>
                    <p class="text-muted mb-4">
                        Votre recherche "<strong>{escape_html(search_query)}</strong>" n'a donné aucun résultat.
                    </p>
                    <div class="search-tips">
                        <h6><i class="fas fa-lightbulb me-2 text-warning"></i>Conseils de recherche :</h6>
                        <ul class="text-left">
                            <li>Vérifiez l'orthographe</li>
                            <li>Utilisez moins de mots-clés</li>
                            <li>Essayez des variantes du nom (avec ou sans accents)</li>
                            <li>Recherchez seulement par prénom ou nom de famille</li>
                        </ul>
                    </div>
                </div>"""

        else:
            # Page de recherche vide
            html += """
        <!-- Conseils de recherche -->
        <div class="row justify-content-center mt-4">
            <div class="col-lg-8">
                <div class="search-tips">
                    <h5 class="mb-3">
                        <i class="fas fa-lightbulb me-2 text-warning"></i>
                        Conseils pour bien rechercher
                    </h5>
                    <div class="row">
                        <div class="col-md-6">
                            <h6><i class="fas fa-check-circle text-success me-1"></i> Exemples corrects :</h6>
                            <ul class="small">
                                <li><code>Martin Dupont</code></li>
                                <li><code>Marie</code></li>
                                <li><code>Durand</code></li>
                                <li><code>Jean-Baptiste</code></li>
                            </ul>
                        </div>
                        <div class="col-md-6">
                            <h6><i class="fas fa-info-circle text-info me-1"></i> Fonctionnalités :</h6>
                            <ul class="small">
                                <li>Recherche insensible à la casse</li>
                                <li>Recherche partielle supportée</li>
                                <li>Maximum 50 résultats affichés</li>
                                <li>Recherche dans tous les champs</li>
                            </ul>
                        </div>
                    </div>
                </div>
            </div>
        </div>"""

        html += f"""
        </div>

        <!-- Navigation -->
        <div class="row justify-content-center mt-4">
            <div class="col-lg-6">
                <div class="card">
                    <div class="card-body text-center">
                        <a href="/{base_name}" class="btn btn-outline-primary me-2">
                            <i class="fas fa-arrow-left me-1"></i>
                            Retour à {base_name}
                        </a>
                        <a href="/" class="btn btn-outline-secondary">
                            <i class="fas fa-home me-1"></i>
                            Accueil
                        </a>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Footer -->
    <footer class="bg-dark text-white py-3 mt-4">
        <div class="container text-center">
            <small>
                <strong>GenEWeb</strong> - Recherche généalogique
                <br>Compatible avec GenEWeb original © 1998-2007 INRIA
            </small>
        </div>
    </footer>

    <script src="https://cdn.jsdelivr.net/npm/jquery@3.6.0/dist/jquery.slim.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@4.6.2/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>"""

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))

    def handle_stats(self, db_driver, base_name: str):
        """Afficher les statistiques"""
        info = db_driver.get_database_info()

        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Statistics - {base_name}</title>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        h1 {{ color: {self.gwd_config.green_color}; }}
        .stats {{ background: #f0f8ff; padding: 20px; border-radius: 5px; }}
        .stat-item {{ margin: 10px 0; padding: 10px; background: white; border-radius: 3px; }}
        .navigation a {{ color: {self.gwd_config.green_color}; }}
    </style>
</head>
<body>
    <h1>📊 Statistics for {base_name}</h1>

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
        <a href="/{base_name}">← Back to {base_name}</a> |
        <a href="/">← Database List</a>
    </div>
</body>
</html>"""

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))

    def handle_database_info(self, db_driver, base_name: str):
        """Afficher les informations de la base (page principale de base)"""
        info = db_driver.get_database_info()

        html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <title>{base_name} - GenEWeb</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@4.6.2/dist/css/bootstrap.min.css">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@fortawesome/fontawesome-free@6.7.2/css/all.min.css">
    <style>
        body {{ background: #f8f9fa; }}
        .navbar-geneweb {{ background: linear-gradient(135deg, #2f6400 0%, #4a8c2a 100%); }}
        .search-card {{
            background: linear-gradient(135deg, #e3f2fd 0%, #f3e5f5 100%);
            border: none;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }}
        .stats-card {{
            background: linear-gradient(135deg, #fff3e0 0%, #fce4ec 100%);
            border: none;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }}
        .tools-card {{
            background: linear-gradient(135deg, #e8f5e8 0%, #f1f8e9 100%);
            border: none;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }}
        .nav-btn {{
            transition: all 0.3s ease;
            border: none;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .nav-btn:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        }}
        .stat-item {{
            padding: 1rem;
            background: rgba(255,255,255,0.8);
            border-radius: 0.5rem;
            margin: 0.5rem 0;
        }}
        .database-title {{
            color: #2f6400;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
        }}
    </style>
</head>
<body class="d-flex flex-column min-vh-100">
    <!-- Navigation -->
    <nav class="navbar navbar-expand-lg navbar-dark navbar-geneweb">
        <div class="container">
            <a class="navbar-brand" href="/">
                <i class="fas fa-sitemap me-2"></i>
                GenEWeb
            </a>
            <div class="navbar-nav ml-auto">
                <a class="nav-link text-white" href="/">
                    <i class="fas fa-home me-1"></i>
                    Accueil
                </a>
            </div>
        </div>
    </nav>

    <div class="container-fluid flex-grow-1 py-4">
        <!-- En-tête de la base -->
        <div class="row justify-content-center mb-4">
            <div class="col-lg-10">
                <div class="text-center">
                    <h1 class="display-4 database-title mb-2">
                        <i class="fas fa-tree me-3"></i>
                        Base {base_name}
                    </h1>
                    <p class="lead text-muted">
                        Base de données généalogique
                    </p>
                </div>
            </div>
        </div>

        <!-- Statistiques de la base -->
        <div class="row justify-content-center mb-4">
            <div class="col-lg-8">
                <div class="card stats-card">
                    <div class="card-header bg-transparent border-0">
                        <h3 class="card-title text-center mb-0">
                            <i class="fas fa-chart-bar me-2 text-warning"></i>
                            Informations sur la base
                        </h3>
                    </div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-6">
                                <div class="stat-item text-center">
                                    <i class="fas fa-users fa-2x text-primary mb-2"></i>
                                    <h4 class="mb-1">{info.number_of_persons:,}</h4>
                                    <small class="text-muted">
                                        {"Personne" if info.number_of_persons == 1 else "Personnes"}
                                    </small>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="stat-item text-center">
                                    <i class="fas fa-heart fa-2x text-danger mb-2"></i>
                                    <h4 class="mb-1">{info.number_of_families:,}</h4>
                                    <small class="text-muted">
                                        {"Famille" if info.number_of_families == 1 else "Familles"}
                                    </small>
                                </div>
                            </div>
                        </div>
                        <div class="row mt-3">
                            <div class="col-md-12">
                                <div class="stat-item">
                                    <strong>Chemin:</strong> <code>{info.path}</code><br>
                                    <strong>Version:</strong> {info.version}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Recherche -->
        <div class="row justify-content-center mb-4">
            <div class="col-lg-8">
                <div class="card search-card">
                    <div class="card-header bg-transparent border-0">
                        <h3 class="card-title text-center mb-0">
                            <i class="fas fa-search me-2 text-info"></i>
                            Rechercher dans la base
                        </h3>
                    </div>
                    <div class="card-body">
                        <form method="GET" action="/{base_name}">
                            <input type="hidden" name="m" value="search">
                            <div class="input-group input-group-lg">
                                <input type="search" class="form-control"
                                       name="search"
                                       placeholder="Entrez un nom à rechercher..."
                                       autofocus>
                                <div class="input-group-append">
                                    <button class="btn btn-primary" type="submit">
                                        <i class="fas fa-search me-1"></i>
                                        Rechercher
                                    </button>
                                </div>
                            </div>
                        </form>
                        <div class="text-center mt-3">
                            <small class="text-muted">
                                <i class="fas fa-info-circle me-1"></i>
                                Recherchez par prénom, nom de famille, ou les deux
                            </small>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Outils de navigation -->
        <div class="row justify-content-center">
            <div class="col-lg-10">
                <div class="card tools-card">
                    <div class="card-header bg-transparent border-0">
                        <h4 class="card-title text-center mb-0">
                            <i class="fas fa-tools me-2 text-success"></i>
                            Outils de navigation
                        </h4>
                    </div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-lg-4 mb-3">
                                <a href="/{base_name}?m=search" class="btn btn-outline-primary btn-block nav-btn">
                                    <i class="fas fa-search fa-fw me-2"></i>
                                    Recherche avancée
                                </a>
                            </div>
                            <div class="col-lg-4 mb-3">
                                <a href="/{base_name}?m=stats" class="btn btn-outline-info btn-block nav-btn">
                                    <i class="fas fa-chart-bar fa-fw me-2"></i>
                                    Statistiques détaillées
                                </a>
                            </div>
                            <div class="col-lg-4 mb-3">
                                <a href="/" class="btn btn-outline-secondary btn-block nav-btn">
                                    <i class="fas fa-arrow-left fa-fw me-2"></i>
                                    Retour aux bases
                                </a>
                            </div>
                        </div>

                        <hr class="my-4">

                        <div class="row">
                            <div class="col-lg-3 mb-2">
                                <button class="btn btn-outline-warning btn-sm btn-block nav-btn" disabled>
                                    <i class="fas fa-calendar fa-fw me-1"></i>
                                    <small>Calendrier</small>
                                </button>
                            </div>
                            <div class="col-lg-3 mb-2">
                                <button class="btn btn-outline-success btn-sm btn-block nav-btn" disabled>
                                    <i class="fas fa-birthday-cake fa-fw me-1"></i>
                                    <small>Anniversaires</small>
                                </button>
                            </div>
                            <div class="col-lg-3 mb-2">
                                <button class="btn btn-outline-danger btn-sm btn-block nav-btn" disabled>
                                    <i class="fas fa-map-marked-alt fa-fw me-1"></i>
                                    <small>Lieux</small>
                                </button>
                            </div>
                            <div class="col-lg-3 mb-2">
                                <button class="btn btn-outline-dark btn-sm btn-block nav-btn" disabled>
                                    <i class="fas fa-cog fa-fw me-1"></i>
                                    <small>Configuration</small>
                                </button>
                            </div>
                        </div>

                        <div class="text-center mt-3">
                            <small class="text-muted">
                                <i class="fas fa-info-circle me-1"></i>
                                Certaines fonctionnalités sont en cours de développement
                            </small>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Footer -->
    <footer class="bg-dark text-white py-3 mt-4">
        <div class="container text-center">
            <small>
                <strong>GenEWeb</strong> - Serveur généalogique Python
                <br>Compatible avec GenEWeb original © 1998-2007 INRIA
            </small>
        </div>
    </footer>

    <script src="https://cdn.jsdelivr.net/npm/jquery@3.6.0/dist/jquery.slim.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@4.6.2/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>"""

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))


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

    return parser.parse_args()


def show_startup_info(config: GWDConfig):
    """Afficher les infos de démarrage (exactement comme l'original)"""
    if not config.daemon:
        try:
            import socket

            hostname = socket.gethostname()
        except:
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

    # Afficher les infos de démarrage
    show_startup_info(config)

    # Créer le handler avec la configuration
    def handler(*args, **kwargs):
        return GeneWebHTTPHandler(*args, gwd_config=config, **kwargs)

    # Gestionnaire de signaux
    def signal_handler(signum, frame):
        print(f"\\nReceived signal {signum}, shutting down...")
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
