#!/usr/bin/env python3
"""
Serveur GenEWeb simple pour test
Version simplifiée qui utilise les modules HTTP standards de Python
"""

import http.server
import json
import os
import socketserver
from urllib.parse import parse_qs, urlparse

from ..geneweb.core.config import Config
from ..geneweb.db.driver import create_database_driver


class GeneWebHTTPHandler(http.server.BaseHTTPRequestHandler):
    """Handler HTTP simple pour GenEWeb"""

    def __init__(self, *args, database_dir=".", **kwargs):
        self.database_dir = database_dir
        super().__init__(*args, **kwargs)

    def do_GET(self):
        """Gérer les requêtes GET"""
        try:
            parsed_url = urlparse(self.path)
            path = parsed_url.path
            query = parse_qs(parsed_url.query)

            print(f"Requête: {self.path}")

            if path == "/":
                self.send_main_page()
            elif path.startswith("/") and len(path) > 1:
                # Page de base de données
                db_name = path[1:]  # Enlever le "/"
                self.send_database_page(db_name, query)
            else:
                self.send_404()

        except Exception as e:
            print(f"Erreur: {e}")
            self.send_error(500, f"Erreur interne: {e}")

    def send_main_page(self):
        """Envoyer la page principale avec la liste des bases"""
        try:
            # Chercher les bases de données
            databases = []
            for file in os.listdir(self.database_dir):
                if file.endswith(".pickle"):
                    db_name = file[:-7]  # Enlever .pickle
                    databases.append(db_name)

            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>GenEWeb - Bases de données</title>
                <meta charset="UTF-8">
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 40px; }}
                    h1 {{ color: #2c5aa0; }}
                    ul {{ list-style-type: none; padding: 0; }}
                    li {{ margin: 10px 0; }}
                    a {{ color: #2c5aa0; text-decoration: none; }}
                    a:hover {{ text-decoration: underline; }}
                    .info {{ background: #f0f8ff; padding: 15px; border-radius: 5px; }}
                </style>
            </head>
            <body>
                <h1>🌳 GenEWeb - Généalogie</h1>

                <div class="info">
                    <h2>Bases de données disponibles:</h2>
                    <ul>
            """

            for db in databases:
                html += f'<li>📊 <a href="/{db}">{db}</a></li>\\n'

            if not databases:
                html += "<li><em>Aucune base de données trouvée</em></li>"

            html += f"""
                    </ul>
                </div>

                <hr>
                <p><small>GenEWeb Python Modernization - Serveur simple de test</small></p>
            </body>
            </html>
            """

            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html.encode("utf-8"))

        except Exception as e:
            self.send_error(500, f"Erreur lors de la génération de la page: {e}")

    def send_database_page(self, db_name, query):
        """Envoyer la page d'une base de données"""
        try:
            db_path = os.path.join(self.database_dir, f"{db_name}.pickle")

            if not os.path.exists(db_path):
                self.send_404()
                return

            # Charger la base de données
            driver = create_database_driver(db_path, "pickle")
            if not driver.open_database(read_only=True):
                self.send_error(500, "Impossible d'ouvrir la base de données")
                return

            # Obtenir les informations
            info = driver.get_database_info()

            # Recherche si demandée
            search_results = []
            search_query = query.get("search", [""])[0]
            if search_query:
                search_results = driver.search_persons(search_query)

            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>{db_name} - GenEWeb</title>
                <meta charset="UTF-8">
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 40px; }}
                    h1 {{ color: #2c5aa0; }}
                    .info {{ background: #f0f8ff; padding: 15px; border-radius: 5px; margin: 20px 0; }}
                    .search {{ background: #fff8f0; padding: 15px; border-radius: 5px; margin: 20px 0; }}
                    .person {{ background: #f5f5f5; padding: 10px; margin: 10px 0; border-radius: 3px; }}
                    input[type="text"] {{ padding: 5px; width: 200px; }}
                    button {{ padding: 5px 10px; }}
                </style>
            </head>
            <body>
                <h1>🌳 Base: {db_name}</h1>

                <div class="info">
                    <h2>📊 Informations</h2>
                    <p><strong>Personnes:</strong> {info.number_of_persons}</p>
                    <p><strong>Familles:</strong> {info.number_of_families}</p>
                    <p><strong>Fichier:</strong> {info.path}</p>
                </div>

                <div class="search">
                    <h2>🔍 Recherche</h2>
                    <form method="GET">
                        <input type="text" name="search" value="{search_query}" placeholder="Nom ou prénom...">
                        <button type="submit">Chercher</button>
                    </form>
            """

            if search_query:
                html += f"<h3>Résultats pour '{search_query}':</h3>"
                if search_results:
                    for person_id, person in search_results:
                        birth_info = ""
                        if person.birth_date:
                            from geneweb.util.string_utils import geneweb_date_to_string

                            birth_info = f" (né le {geneweb_date_to_string(person.birth_date)})"

                        html += f"""
                        <div class="person">
                            <strong>{person.first_name} {person.surname}</strong>{birth_info}
                            {f"<br><em>{person.occupation}</em>" if person.occupation else ""}
                        </div>
                        """
                else:
                    html += "<p><em>Aucun résultat trouvé</em></p>"

            html += """
                </div>

                <hr>
                <p><a href="/">← Retour aux bases de données</a></p>
                <p><small>GenEWeb Python Modernization</small></p>
            </body>
            </html>
            """

            driver.close_database()

            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html.encode("utf-8"))

        except Exception as e:
            self.send_error(500, f"Erreur base de données: {e}")

    def send_404(self):
        """Envoyer une page 404"""
        html = """
        <!DOCTYPE html>
        <html>
        <head><title>404 - Non trouvé</title></head>
        <body>
            <h1>404 - Page non trouvée</h1>
            <p><a href="/">Retour à l'accueil</a></p>
        </body>
        </html>
        """
        self.send_response(404)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))


def run_simple_server(port=2317, database_dir="."):
    """Démarrer le serveur simple"""

    # Créer le handler avec le répertoire des bases
    def handler(*args, **kwargs):
        return GeneWebHTTPHandler(*args, database_dir=database_dir, **kwargs)

    print(f"🌳 GenEWeb Serveur Simple")
    print(f"📁 Répertoire des bases: {os.path.abspath(database_dir)}")
    print(f"🌐 URL: http://localhost:{port}/")
    print(f"⏹️  Arrêt: Ctrl+C")

    try:
        with socketserver.TCPServer(("", port), handler) as httpd:
            print(f"✅ Serveur démarré sur le port {port}")
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\\n🛑 Serveur arrêté")
    except Exception as e:
        print(f"❌ Erreur: {e}")


if __name__ == "__main__":
    import sys

    port = 2317
    database_dir = "."

    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    if len(sys.argv) > 2:
        database_dir = sys.argv[2]

    run_simple_server(port, database_dir)
