#!/usr/bin/env python3
"""
Core functionality for GenEWeb Admin Panel

This module implements the core admin panel functionality, similar to the
setup.ml file in the original OCaml implementation.
"""

import os
import socket
import threading
from dataclasses import dataclass
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Optional
from urllib.parse import parse_qs, urlparse


@dataclass
class AdminConfig:
    """Configuration for the admin server"""

    port: int = 2316
    gwd_port: int = 2317
    database_dir: str = "."
    setup_dir: str = "."
    bin_dir: str = "."
    daemon: bool = False
    default_lang: str = "fr"
    only_file: Optional[str] = None


class AdminRequestHandler(BaseHTTPRequestHandler):
    """Request handler for admin panel"""

    def __init__(self, config: AdminConfig, *args, **kwargs):
        self.config = config
        super().__init__(*args, **kwargs)

    def do_GET(self):
        """Handle GET requests"""
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        query = parse_qs(parsed_url.query)

        # Route requests
        if path == "/" or path == "/main.htm":
            self.serve_main_page()
        elif path == "/welcome.htm":
            self.serve_welcome_page()
        elif path.startswith("/css/"):
            self.serve_static_file(path)
        elif path.startswith("/images/"):
            self.serve_static_file(path)
        elif path.startswith("/js/"):
            self.serve_static_file(path)
        else:
            self.serve_admin_page(path, query)

    def do_POST(self):
        """Handle POST requests"""
        parsed_url = urlparse(self.path)
        path = parsed_url.path

        # Read POST data
        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length).decode("utf-8")
        query = parse_qs(post_data)

        # Handle admin operations
        self.handle_admin_operation(path, query)

    def serve_main_page(self):
        """Serve the main admin page"""
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>GenEWeb Admin Panel</title>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #2f6400; color: white; padding: 10px; }}
                .menu {{ margin: 20px 0; }}
                .menu a {{ margin-right: 20px; text-decoration: none; color: #2f6400; }}
                .menu a:hover {{ text-decoration: underline; }}
                .footer {{ margin-top: 50px; font-size: 0.9em; color: #666; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>GenEWeb Admin Panel</h1>
                <p>Database Administration Interface</p>
            </div>
            
            <div class="menu">
                <a href="/databases">Manage Databases</a>
                <a href="/import">Import Data</a>
                <a href="/export">Export Data</a>
                <a href="/users">User Management</a>
                <a href="/config">Configuration</a>
                <a href="/logs">View Logs</a>
            </div>
            
            <h2>System Status</h2>
            <p><strong>Admin Server:</strong> Running on port {self.config.port}</p>
            <p><strong>Main Server:</strong> Port {self.config.gwd_port}</p>
            <p><strong>Database Directory:</strong> {os.path.abspath(self.config.database_dir)}</p>
            
            <h2>Available Databases</h2>
            <ul>
                {self.get_databases_list()}
            </ul>
            
            <div class="footer">
                <hr>
                <p>GenEWeb Admin Panel - Python Modernization</p>
            </div>
        </body>
        </html>
        """
        self.wfile.write(html.encode("utf-8"))

    def serve_welcome_page(self):
        """Serve the welcome page"""
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()

        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Welcome to GenEWeb Admin</title>
            <meta charset="utf-8">
        </head>
        <body>
            <h1>Welcome to GenEWeb Admin Panel</h1>
            <p>This is the administration interface for GenEWeb Python.</p>
            <p><a href="/">Go to Main Panel</a></p>
        </body>
        </html>
        """
        self.wfile.write(html.encode("utf-8"))

    def serve_static_file(self, path: str):
        """Serve static files (CSS, images, JS)"""
        # Pour l'instant, on retourne une réponse 404
        # Dans une implémentation complète, on servirait les vrais fichiers
        self.send_response(404)
        self.end_headers()

    def serve_admin_page(self, path: str, query: dict):
        """Serve admin pages based on path"""
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()

        if path == "/databases":
            html = self.get_databases_page()
        elif path == "/import":
            html = self.get_import_page()
        elif path == "/export":
            html = self.get_export_page()
        elif path == "/users":
            html = self.get_users_page()
        elif path == "/config":
            html = self.get_config_page()
        elif path == "/logs":
            html = self.get_logs_page()
        else:
            html = self.get_404_page()

        self.wfile.write(html.encode("utf-8"))

    def handle_admin_operation(self, path: str, data: dict):
        """Handle admin operations (POST requests)"""
        # Pour l'instant, on retourne simplement à la page principale
        self.send_response(302)
        self.send_header("Location", "/")
        self.end_headers()

    def get_databases_list(self) -> str:
        """Get HTML list of available databases"""
        try:
            databases = []
            for item in os.listdir(self.config.database_dir):
                if item.endswith(".pickle") or item.endswith(".gwb"):
                    name = item.replace(".pickle", "").replace(".gwb", "")
                    databases.append(f'<li><a href="http://localhost:{self.config.gwd_port}/{name}">{name}</a></li>')
            
            return "\\n".join(databases) if databases else "<li>No databases found</li>"
        except Exception:
            return "<li>Error reading database directory</li>"

    def get_databases_page(self) -> str:
        """Get databases management page"""
        return """
        <!DOCTYPE html>
        <html>
        <head><title>Database Management</title></head>
        <body>
            <h1>Database Management</h1>
            <p>Here you can create, delete, and manage databases.</p>
            <p><a href="/">Back to Main Panel</a></p>
        </body>
        </html>
        """

    def get_import_page(self) -> str:
        """Get import page"""
        return """
        <!DOCTYPE html>
        <html>
        <head><title>Import Data</title></head>
        <body>
            <h1>Import Data</h1>
            <p>Import genealogy data from GEDCOM or GW files.</p>
            <p><a href="/">Back to Main Panel</a></p>
        </body>
        </html>
        """

    def get_export_page(self) -> str:
        """Get export page"""
        return """
        <!DOCTYPE html>
        <html>
        <head><title>Export Data</title></head>
        <body>
            <h1>Export Data</h1>
            <p>Export databases to GEDCOM or GW format.</p>
            <p><a href="/">Back to Main Panel</a></p>
        </body>
        </html>
        """

    def get_users_page(self) -> str:
        """Get users management page"""
        return """
        <!DOCTYPE html>
        <html>
        <head><title>User Management</title></head>
        <body>
            <h1>User Management</h1>
            <p>Manage user accounts and permissions.</p>
            <p><a href="/">Back to Main Panel</a></p>
        </body>
        </html>
        """

    def get_config_page(self) -> str:
        """Get configuration page"""
        return """
        <!DOCTYPE html>
        <html>
        <head><title>Configuration</title></head>
        <body>
            <h1>System Configuration</h1>
            <p>Configure server settings and options.</p>
            <p><a href="/">Back to Main Panel</a></p>
        </body>
        </html>
        """

    def get_logs_page(self) -> str:
        """Get logs page"""
        return """
        <!DOCTYPE html>
        <html>
        <head><title>System Logs</title></head>
        <body>
            <h1>System Logs</h1>
            <p>View server logs and activity.</p>
            <p><a href="/">Back to Main Panel</a></p>
        </body>
        </html>
        """

    def get_404_page(self) -> str:
        """Get 404 page"""
        return """
        <!DOCTYPE html>
        <html>
        <head><title>Page Not Found</title></head>
        <body>
            <h1>Page Not Found</h1>
            <p>The requested page was not found.</p>
            <p><a href="/">Back to Main Panel</a></p>
        </body>
        </html>
        """

    def log_message(self, format, *args):
        """Override to customize logging"""
        print(f"[{self.client_address[0]}] {format % args}")


class AdminHTTPServer(HTTPServer):
    """Custom HTTP server for admin panel"""

    def __init__(self, config: AdminConfig, *args, **kwargs):
        self.config = config
        super().__init__(*args, **kwargs)


def create_request_handler(config: AdminConfig):
    """Create request handler with config"""

    class ConfiguredHandler(AdminRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(config, *args, **kwargs)

    return ConfiguredHandler


def check_access_control(config: AdminConfig, client_address: str) -> bool:
    """Check if client address is allowed"""
    if not config.only_file:
        return True

    try:
        with open(config.only_file, "r") as f:
            allowed_address = f.read().strip()
            return client_address == allowed_address
    except Exception:
        return True  # Si erreur lecture fichier, on autorise


def start_admin_server(config: AdminConfig):
    """Start the admin server"""
    handler_class = create_request_handler(config)
    server = AdminHTTPServer(config, ("", config.port), handler_class)

    if config.daemon:
        # En mode daemon, on lance le serveur en arrière-plan
        server_thread = threading.Thread(target=server.serve_forever)
        server_thread.daemon = True
        server_thread.start()
        
        # En mode daemon, on garde le processus principal actif
        try:
            while True:
                threading.Event().wait(1)
        except KeyboardInterrupt:
            server.shutdown()
    else:
        # En mode normal, on lance le serveur dans le thread principal
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            server.shutdown()
        finally:
            server.server_close()