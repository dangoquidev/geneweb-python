#!/usr/bin/env python3
"""
GenEWeb Daemon (gwd) - Version avec templates séparés
"""

import http.server
import socketserver
import os
import sys
import signal
import logging
import urllib.parse
import argparse
from pathlib import Path

# Import des modules GenEWeb
from geneweb.db.driver import create_database_driver
from geneweb.core.config import Config
from geneweb.security import create_security_manager
from geneweb.util.string_utils import *

# Import du moteur de templates
from template_engine import render_template


class GeneWebHTTPHandler(http.server.BaseHTTPRequestHandler):
    """Handler HTTP pour GenEWeb avec templates"""
    
    def __init__(self, *args, gwd_config=None, **kwargs):
        self.gwd_config = gwd_config
        super().__init__(*args, **kwargs)
    
    def log_message(self, format_str, *args):
        """Logging personnalisé"""
        remote_addr = self.client_address[0]
        message = format_str % args
        logging.getLogger('geneweb.gwd').info(f"{remote_addr} - {message}")
    
    def do_GET(self):
        """Traiter les requêtes GET"""
        self.handle_request()
    
    def do_POST(self):
        """Traiter les requêtes POST"""
        self.handle_request()
    
    def handle_request(self):
        """Fonction principale de traitement des requêtes"""
        try:
            # Obtenir l'adresse client
            from_addr = self.client_address[0]
            
            # Parser l'URL
            parsed_url = urllib.parse.urlparse(self.path)
            script_name = parsed_url.path[1:] if parsed_url.path.startswith('/') else parsed_url.path
            query_string = parsed_url.query
            
            # Traitement spécial pour les fichiers statiques
            if script_name.startswith('static/'):
                self.serve_static_file(script_name)
                return
            
            # Traitement spécial robots.txt
            if script_name == "robots.txt":
                self.handle_robots_txt()
                return
            
            # Traiter les fichiers statiques
            if self.is_static_request(script_name):
                self.serve_static_file(script_name)
                return
            
            # Traitement principal GenEWeb
            self.handle_geneweb_request(script_name, query_string, from_addr)
            
        except Exception as e:
            logging.getLogger('geneweb.gwd').error(f"Error handling request: {e}")
            self.send_error(500, "Internal Server Error")
    
    def handle_robots_txt(self):
        """Traiter robots.txt"""
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        self.wfile.write(b"User-Agent: *\\nDisallow: /\\n")
    
    def is_static_request(self, script_name: str) -> bool:
        """Vérifier si c'est une requête de fichier statique"""
        static_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.ico', '.css', '.js', '.txt', '.xml']
        return any(script_name.endswith(ext) for ext in static_extensions)
    
    def serve_static_file(self, script_name: str):
        """Servir un fichier statique"""
        # Si c'est un fichier dans /static/, le servir depuis notre dossier static
        if script_name.startswith('static/'):
            static_path = os.path.join(os.path.dirname(__file__), script_name)
            if os.path.exists(static_path) and os.path.isfile(static_path):
                try:
                    with open(static_path, 'rb') as f:
                        content = f.read()
                    
                    self.send_response(200)
                    self.send_header('Content-Type', self.get_content_type(script_name))
                    self.send_header('Content-Length', str(len(content)))
                    self.send_header('Cache-Control', 'max-age=3600')
                    self.end_headers()
                    self.wfile.write(content)
                    return
                except Exception as e:
                    logging.getLogger('geneweb.gwd').error(f"Error serving static file: {e}")
        
        # Fichier non trouvé
        self.send_error(404, "File Not Found")
    
    def get_content_type(self, filename: str) -> str:
        """Déterminer le content-type"""
        ext = os.path.splitext(filename)[1].lower()
        content_types = {
            '.html': 'text/html; charset=utf-8',
            '.css': 'text/css',
            '.js': 'application/javascript',
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.ico': 'image/x-icon',
            '.txt': 'text/plain',
            '.xml': 'application/xml'
        }
        return content_types.get(ext, 'application/octet-stream')
    
    def handle_geneweb_request(self, script_name: str, query_string: str, from_addr: str):
        """Traiter une requête GenEWeb"""
        try:
            # Si pas de script_name, afficher la liste des bases
            if not script_name:
                self.serve_base_list()
                return
            
            # Extraire le nom de la base
            if '/' in script_name:
                base_name = script_name.split('/')[0]
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
                mode = params.get('m', [''])[0]
                
                if mode == 'search' or 'search' in params:
                    self.handle_search(db_driver, params, base_name)
                elif mode == 'stats':
                    self.handle_stats(db_driver, base_name)
                else:
                    self.handle_database_info(db_driver, base_name)
            
            finally:
                db_driver.close_database()
        
        except Exception as e:
            logging.getLogger('geneweb.gwd').error(f"Error in GenEWeb request: {e}")
            self.send_error(500, "Internal Server Error")
    
    def serve_base_list(self):
        """Servir la liste des bases avec template"""
        databases = []
        try:
            for file in os.listdir(self.gwd_config.database_dir):
                if file.endswith('.pickle'):
                    db_name = file[:-7]
                    databases.append(db_name)
        except OSError:
            pass
        
        # Contexte pour le template
        context = {
            'databases': sorted(databases),
            'server_port': self.gwd_config.selected_port,
            'database_dir': os.path.basename(os.path.abspath(self.gwd_config.database_dir))
        }
        
        try:
            html = render_template('home.html', **context)
        except Exception as e:
            # Fallback simple si templates ne marchent pas
            logging.getLogger('geneweb.gwd').error(f"Template error: {e}")
            html = self._fallback_home_html(databases)
        
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))
    
    def _fallback_home_html(self, databases):
        """HTML de fallback simple"""
        db_list = ''.join([f'<li><a href="/{db}">{db}</a></li>' for db in databases])
        return f"""<!DOCTYPE html>
<html><head><title>GenEWeb Server</title>
<link rel="stylesheet" href="/static/css/geneweb.css">
</head><body>
<h1>GenEWeb Server</h1>
<h2>Bases disponibles:</h2>
<ul>{db_list}</ul>
<p>Port: {self.gwd_config.selected_port}</p>
</body></html>"""
    
    def handle_database_info(self, db_driver, base_name: str):
        """Afficher les informations de la base avec template"""
        info = db_driver.get_database_info()
        
        context = {
            'base_name': base_name,
            'db_info': info,
            'show_navbar': True
        }
        
        try:
            html = render_template('database_info.html', **context)
        except Exception as e:
            logging.getLogger('geneweb.gwd').error(f"Template error: {e}")
            html = f"""<!DOCTYPE html>
<html><head><title>{base_name}</title>
<link rel="stylesheet" href="/static/css/geneweb.css">
</head><body>
<h1>{base_name}</h1>
<p>Personnes: {info.number_of_persons}</p>
<p>Familles: {info.number_of_families}</p>
<a href="/{base_name}?m=search">Rechercher</a>
<a href="/">Accueil</a>
</body></html>"""
        
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))
    
    def handle_search(self, db_driver, params, base_name: str):
        """Traiter une recherche avec template"""
        search_query = params.get('search', [''])[0] or params.get('s', [''])[0]
        results = []
        
        if search_query:
            results = db_driver.search_persons(search_query)
        
        context = {
            'base_name': base_name,
            'search_query': search_query,
            'results': results,
            'show_navbar': True
        }
        
        try:
            html = render_template('search.html', **context)
        except Exception as e:
            logging.getLogger('geneweb.gwd').error(f"Template error: {e}")
            # Fallback simple
            results_html = ''
            if results:
                results_html = '<ul>'
                for person_id, person in results[:10]:
                    results_html += f'<li>{escape_html(person.first_name)} {escape_html(person.surname)}</li>'
                results_html += '</ul>'
            
            html = f"""<!DOCTYPE html>
<html><head><title>Recherche - {base_name}</title>
<link rel="stylesheet" href="/static/css/geneweb.css">
</head><body>
<h1>Recherche dans {base_name}</h1>
<form method="GET">
<input type="hidden" name="m" value="search">
<input type="search" name="search" value="{escape_html(search_query)}" placeholder="Nom à rechercher">
<button type="submit">Rechercher</button>
</form>
{results_html}
<a href="/{base_name}">Retour</a>
</body></html>"""
        
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))
    
    def handle_stats(self, db_driver, base_name: str):
        """Afficher les statistiques"""
        info = db_driver.get_database_info()
        
        html = f"""<!DOCTYPE html>
<html><head><title>Statistiques - {base_name}</title>
<link rel="stylesheet" href="/static/css/geneweb.css">
</head><body>
<h1>Statistiques de {base_name}</h1>
<p><strong>Personnes:</strong> {info.number_of_persons:,}</p>
<p><strong>Familles:</strong> {info.number_of_families:,}</p>
<p><strong>Chemin:</strong> {info.path}</p>
<p><strong>Version:</strong> {info.version}</p>
<a href="/{base_name}">Retour</a>
</body></html>"""
        
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))


class GWDConfig:
    """Configuration du serveur GWD"""
    def __init__(self):
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


def setup_logging():
    """Configuration du logging"""
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[logging.StreamHandler(sys.stdout)]
    )


def parse_arguments():
    """Parser les arguments"""
    parser = argparse.ArgumentParser(
        prog='gwd_templates',
        description='GenEWeb Daemon - Version avec templates séparés'
    )
    
    parser.add_argument('-addr', type=str, help='IP address to bind to')
    parser.add_argument('-p', '-port', type=int, default=2317, dest='port',
                       help='Port number (default: 2317)')
    parser.add_argument('-hd', type=str, default='.', dest='database_dir',
                       help='Database directory (default: current directory)')
    parser.add_argument('-daemon', action='store_true',
                       help='Run as daemon (background process)')
    
    return parser.parse_args()


def main():
    """Fonction principale"""
    args = parse_arguments()
    
    # Créer la configuration
    config = GWDConfig()
    config.selected_addr = args.addr
    config.selected_port = args.port
    config.database_dir = args.database_dir
    config.daemon = args.daemon
    
    # Configurer les chemins
    config.gw_prefix = os.getcwd()
    config.etc_prefix = os.path.join(config.gw_prefix, "etc")
    config.images_prefix = os.path.join(config.gw_prefix, "images")
    config.images_dir = config.images_prefix
    
    # Créer les répertoires
    os.makedirs(config.database_dir, exist_ok=True)
    
    # Configuration du logging
    setup_logging()
    
    print(f"GenEWeb server starting on port {config.selected_port}")
    print("Templates et CSS dans des fichiers séparés")
    print("Ctrl+C pour arrêter")
    
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
            logging.getLogger('geneweb.gwd').info(f"GenEWeb server listening on {config.selected_addr or 'localhost'}:{config.selected_port}")
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\\nServer stopped by user")
    except Exception as e:
        print(f"Server error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
