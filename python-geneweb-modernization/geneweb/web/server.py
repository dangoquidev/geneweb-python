"""
Web server module for GenEWeb

This module implements the HTTP web server functionality,
handling requests, responses, and routing. Translated from
the original OCaml gwd (GenEWeb Daemon) implementation.

Copyright (c) 1998-2007 INRIA
Python modernization preserving original structure and functionality.
"""

import asyncio
import socket
import threading
import time
import logging
from typing import Optional, Dict, List, Callable, Tuple, Any
from dataclasses import dataclass
from datetime import datetime
from urllib.parse import urlparse, parse_qs, unquote
import mimetypes
import os
import sys

from ..core.config import Config, create_default_output_config
from ..core.definitions import HttpStatus
from ..db.driver import DatabaseDriver, create_database_driver, get_available_databases
from ..security import SecurityManager, create_security_manager, AccessLevel
from ..util.string_utils import extract_parameter, create_environment


@dataclass
class ServerConfig:
    """Configuration for the web server"""
    host: str = "localhost"
    port: int = 2317
    database_directory: str = "databases"
    max_connections: int = 100
    timeout: int = 30
    debug: bool = False
    daemon: bool = False
    log_level: str = "INFO"
    static_files_dir: str = "static"
    templates_dir: str = "templates"
    plugins_dir: str = "plugins"


class HTTPRequest:
    """Represents an HTTP request"""
    
    def __init__(self, method: str, path: str, query_string: str, headers: Dict[str, str], body: bytes):
        self.method = method
        self.path = path
        self.query_string = query_string
        self.headers = headers
        self.body = body
        self.remote_addr = ""
        self.timestamp = time.time()
        
        # Parse components
        self.parsed_path = unquote(path)
        self.query_params = parse_qs(query_string)
        self.form_data = {}
        
        # Parse form data if present
        content_type = headers.get('content-type', '').lower()
        if content_type.startswith('application/x-www-form-urlencoded'):
            self.form_data = parse_qs(body.decode('utf-8', errors='ignore'))
        elif content_type.startswith('multipart/form-data'):
            # Handle multipart form data
            self._parse_multipart_form_data(content_type, body)
    
    def _parse_multipart_form_data(self, content_type: str, body: bytes) -> None:
        """Parse multipart form data"""
        # Extract boundary
        boundary = None
        for part in content_type.split(';'):
            part = part.strip()
            if part.startswith('boundary='):
                boundary = part[9:].strip('"')
                break
        
        if not boundary:
            return
        
        # Simple multipart parsing (production code would use a proper parser)
        boundary_bytes = ('--' + boundary).encode()
        parts = body.split(boundary_bytes)
        
        for part in parts[1:-1]:  # Skip first and last empty parts
            if not part.strip():
                continue
            
            # Find double CRLF separating headers from content
            header_end = part.find(b'\r\n\r\n')
            if header_end == -1:
                continue
            
            headers_data = part[:header_end].decode('utf-8', errors='ignore')
            content = part[header_end + 4:]
            
            # Parse Content-Disposition header
            name = None
            for line in headers_data.split('\r\n'):
                if line.lower().startswith('content-disposition:'):
                    # Extract name parameter
                    if 'name="' in line:
                        start = line.find('name="') + 6
                        end = line.find('"', start)
                        name = line[start:end]
                    break
            
            if name:
                self.form_data[name] = content.decode('utf-8', errors='ignore').strip()
    
    def get_query_param(self, key: str, default: str = "") -> str:
        """Get query parameter value"""
        values = self.query_params.get(key, [])
        return values[0] if values else default
    
    def get_form_param(self, key: str, default: str = "") -> str:
        """Get form parameter value"""
        if isinstance(self.form_data.get(key), list):
            values = self.form_data[key]
            return values[0] if values else default
        return self.form_data.get(key, default)
    
    def get_header(self, key: str, default: str = "") -> str:
        """Get header value"""
        return self.headers.get(key.lower(), default)


class HTTPResponse:
    """Represents an HTTP response"""
    
    def __init__(self):
        self.status = HttpStatus.OK
        self.headers: Dict[str, str] = {}
        self.content = b""
        self.content_type = "text/html; charset=utf-8"
    
    def set_status(self, status: HttpStatus) -> None:
        """Set response status"""
        self.status = status
    
    def add_header(self, name: str, value: str) -> None:
        """Add response header"""
        self.headers[name] = value
    
    def set_content(self, content: str, content_type: str = "text/html; charset=utf-8") -> None:
        """Set response content"""
        self.content = content.encode('utf-8')
        self.content_type = content_type
        self.add_header('Content-Type', content_type)
        self.add_header('Content-Length', str(len(self.content)))
    
    def set_binary_content(self, content: bytes, content_type: str) -> None:
        """Set binary response content"""
        self.content = content
        self.content_type = content_type
        self.add_header('Content-Type', content_type)
        self.add_header('Content-Length', str(len(content)))
    
    def redirect(self, url: str, permanent: bool = False) -> None:
        """Set redirect response"""
        self.status = HttpStatus.MOVED_TEMPORARILY if not permanent else HttpStatus.MOVED_TEMPORARILY
        self.add_header('Location', url)
    
    def to_bytes(self) -> bytes:
        """Convert response to bytes for sending"""
        status_line = f"HTTP/1.1 {self.status.value} {self.status.name}\r\n"
        
        headers_lines = []
        for name, value in self.headers.items():
            headers_lines.append(f"{name}: {value}\r\n")
        
        response = status_line.encode() + b"".join(line.encode() for line in headers_lines) + b"\r\n" + self.content
        return response


class RequestHandler:
    """Base class for handling HTTP requests"""
    
    def __init__(self, server_config: ServerConfig, geneweb_config: Config, 
                 db_driver: DatabaseDriver, security_manager: SecurityManager):
        self.server_config = server_config
        self.geneweb_config = geneweb_config
        self.db_driver = db_driver
        self.security_manager = security_manager
    
    async def handle_request(self, request: HTTPRequest) -> HTTPResponse:
        """Handle an HTTP request"""
        try:
            # Log the request
            logging.info(f"{request.method} {request.path} from {request.remote_addr}")
            
            # Route the request
            if request.path == "/":
                return await self.handle_index(request)
            elif request.path.startswith("/static/"):
                return await self.handle_static_file(request)
            elif request.path == "/robots.txt":
                return await self.handle_robots_txt(request)
            elif request.path.startswith("/api/"):
                return await self.handle_api_request(request)
            else:
                return await self.handle_geneweb_request(request)
        
        except Exception as e:
            logging.error(f"Error handling request {request.path}: {e}")
            return self.create_error_response(HttpStatus.INTERNAL_SERVER_ERROR, str(e))
    
    async def handle_index(self, request: HTTPRequest) -> HTTPResponse:
        """Handle index page request"""
        response = HTTPResponse()
        
        # Get list of available databases
        databases = get_available_databases(self.server_config.database_directory)
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>GenEWeb Server</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .database-list {{ list-style-type: none; }}
                .database-list li {{ margin: 10px 0; }}
                .database-list a {{ text-decoration: none; color: #2c5aa0; }}
                .database-list a:hover {{ text-decoration: underline; }}
            </style>
        </head>
        <body>
            <h1>GenEWeb Genealogy Server</h1>
            <p>Available databases:</p>
            <ul class="database-list">
        """
        
        for db in databases:
            html_content += f'<li><a href="/{db}">{db}</a></li>'
        
        html_content += """
            </ul>
            <hr>
            <p><small>GenEWeb Python Modernization - Preserving genealogical history</small></p>
        </body>
        </html>
        """
        
        response.set_content(html_content)
        return response
    
    async def handle_static_file(self, request: HTTPRequest) -> HTTPResponse:
        """Handle static file requests"""
        response = HTTPResponse()
        
        # Extract filename from path
        filename = request.path[8:]  # Remove "/static/"
        file_path = os.path.join(self.server_config.static_files_dir, filename)
        
        # Security check - prevent directory traversal
        if ".." in filename or filename.startswith("/"):
            return self.create_error_response(HttpStatus.FORBIDDEN, "Access denied")
        
        try:
            if not os.path.exists(file_path):
                return self.create_error_response(HttpStatus.NOT_FOUND, "File not found")
            
            # Determine content type
            content_type, _ = mimetypes.guess_type(file_path)
            if not content_type:
                content_type = "application/octet-stream"
            
            # Read and serve file
            with open(file_path, 'rb') as f:
                content = f.read()
            
            response.set_binary_content(content, content_type)
            return response
        
        except Exception as e:
            logging.error(f"Error serving static file {file_path}: {e}")
            return self.create_error_response(HttpStatus.INTERNAL_SERVER_ERROR, "Server error")
    
    async def handle_robots_txt(self, request: HTTPRequest) -> HTTPResponse:
        """Handle robots.txt request"""
        response = HTTPResponse()
        robots_content = "User-Agent: *\\nDisallow: /\\n"
        response.set_content(robots_content, "text/plain")
        return response
    
    async def handle_api_request(self, request: HTTPRequest) -> HTTPResponse:
        """Handle API requests"""
        response = HTTPResponse()
        response.set_content('{"error": "API not implemented"}', "application/json")
        response.set_status(HttpStatus.NOT_FOUND)
        return response
    
    async def handle_geneweb_request(self, request: HTTPRequest) -> HTTPResponse:
        """Handle GenEWeb-specific requests"""
        # Extract database name from path
        path_parts = request.path.strip('/').split('/')
        if not path_parts or not path_parts[0]:
            return await self.handle_index(request)
        
        database_name = path_parts[0]
        
        # Check if database exists
        available_dbs = get_available_databases(self.server_config.database_directory)
        if database_name not in available_dbs:
            return self.create_error_response(HttpStatus.NOT_FOUND, f"Database '{database_name}' not found")
        
        # Create GenEWeb configuration for this request
        geneweb_config = self.create_geneweb_config(request, database_name)
        
        # Handle authentication if required
        auth_result = await self.authenticate_request(request, geneweb_config)
        if not auth_result.success and self.requires_authentication(request, database_name):
            return self.create_auth_required_response(auth_result)
        
        # Load database
        db_path = os.path.join(self.server_config.database_directory, database_name)
        db_driver = create_database_driver(db_path)
        
        if not db_driver.open_database():
            return self.create_error_response(HttpStatus.INTERNAL_SERVER_ERROR, "Failed to open database")
        
        try:
            # Process the GenEWeb request
            return await self.process_geneweb_request(request, geneweb_config, db_driver)
        finally:
            db_driver.close_database()
    
    def create_geneweb_config(self, request: HTTPRequest, database_name: str) -> Config:
        """Create GenEWeb configuration from HTTP request"""
        config = Config()
        config.database_name = database_name
        config.from_address = request.remote_addr
        config.debug = self.server_config.debug
        
        # Extract environment from query parameters and form data
        env_list = []
        
        # Add query parameters
        for key, values in request.query_params.items():
            if values:
                env_list.append((key, values[0]))
        
        # Add form parameters
        for key, value in request.form_data.items():
            if isinstance(value, list) and value:
                env_list.append((key, value[0]))
            elif isinstance(value, str):
                env_list.append((key, value))
        
        config.environment = env_list
        
        # Set language from headers or parameters
        lang = request.get_query_param('lang') or request.get_form_param('lang')
        if not lang:
            # Try to extract from Accept-Language header
            accept_lang = request.get_header('Accept-Language')
            if accept_lang:
                # Simple language extraction
                lang = accept_lang.split(',')[0].split('-')[0].strip()
        
        config.language = lang or "en"
        config.default_language = "en"
        
        # Set other request-specific settings
        config.update_timestamp()
        
        return config
    
    async def authenticate_request(self, request: HTTPRequest, config: Config) -> Any:
        """Authenticate the request"""
        # Check for Authorization header
        auth_header = request.get_header('Authorization')
        
        if auth_header:
            if auth_header.startswith('Basic '):
                # Handle Basic authentication
                import base64
                try:
                    encoded_creds = auth_header[6:]  # Remove "Basic "
                    decoded_creds = base64.b64decode(encoded_creds).decode('utf-8')
                    username, password = decoded_creds.split(':', 1)
                    return self.security_manager.authenticate_basic(username, password, request.remote_addr)
                except Exception as e:
                    logging.warning(f"Invalid Basic auth header: {e}")
            
            elif auth_header.startswith('Digest '):
                # Handle Digest authentication
                return self.security_manager.authenticate_digest(
                    auth_header, request.method, request.path, request.remote_addr
                )
        
        # Check for session token
        session_token = request.get_query_param('token') or request.get_form_param('token')
        if session_token:
            username = self.security_manager.verify_session_token(session_token)
            if username:
                user = self.security_manager.get_user_info(username)
                from ..security import AuthResult
                return AuthResult(success=True, user=user)
        
        # No authentication provided
        from ..security import AuthResult
        return AuthResult(success=False, error_message="Authentication required")
    
    def requires_authentication(self, request: HTTPRequest, database_name: str) -> bool:
        """Check if request requires authentication"""
        # Public pages that don't require authentication
        if request.path.endswith('.css') or request.path.endswith('.js') or request.path.endswith('.png'):
            return False
        
        # Check database configuration for authentication requirements
        # This would be expanded based on database settings
        return True
    
    def create_auth_required_response(self, auth_result: Any) -> HTTPResponse:
        """Create authentication required response"""
        response = HTTPResponse()
        response.set_status(HttpStatus.UNAUTHORIZED)
        
        if auth_result.requires_digest_auth:
            challenge = self.security_manager.create_digest_challenge("GenEWeb")
            response.add_header('WWW-Authenticate', challenge)
        else:
            response.add_header('WWW-Authenticate', 'Basic realm="GenEWeb"')
        
        response.set_content("""
        <html>
        <head><title>Authentication Required</title></head>
        <body>
            <h1>Authentication Required</h1>
            <p>You need to authenticate to access this resource.</p>
        </body>
        </html>
        """)
        
        return response
    
    async def process_geneweb_request(self, request: HTTPRequest, config: Config, db_driver: DatabaseDriver) -> HTTPResponse:
        """Process a GenEWeb-specific request"""
        response = HTTPResponse()
        
        # This is where the main GenEWeb logic would be implemented
        # For now, show a basic database info page
        
        db_info = db_driver.get_database_info()
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{db_info.name} - GenEWeb</title>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .info {{ background-color: #f5f5f5; padding: 20px; border-radius: 5px; }}
                .stats {{ margin: 20px 0; }}
                .stats dt {{ font-weight: bold; }}
                .stats dd {{ margin: 5px 0 15px 20px; }}
            </style>
        </head>
        <body>
            <h1>Database: {db_info.name}</h1>
            
            <div class="info">
                <h2>Database Information</h2>
                <dl class="stats">
                    <dt>Number of Persons:</dt>
                    <dd>{db_info.number_of_persons:,}</dd>
                    
                    <dt>Number of Families:</dt>
                    <dd>{db_info.number_of_families:,}</dd>
                    
                    <dt>Database Path:</dt>
                    <dd>{db_info.path}</dd>
                    
                    <dt>Version:</dt>
                    <dd>{db_info.version}</dd>
                </dl>
            </div>
            
            <div class="navigation">
                <h2>Navigation</h2>
                <ul>
                    <li><a href="/{db_info.name}?m=search">Search Persons</a></li>
                    <li><a href="/{db_info.name}?m=stats">Database Statistics</a></li>
                    <li><a href="/">Back to Database List</a></li>
                </ul>
            </div>
            
            <hr>
            <p><small>GenEWeb Python Modernization - Database loaded successfully</small></p>
        </body>
        </html>
        """
        
        response.set_content(html_content)
        return response
    
    def create_error_response(self, status: HttpStatus, message: str) -> HTTPResponse:
        """Create an error response"""
        response = HTTPResponse()
        response.set_status(status)
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Error {status.value}</title>
        </head>
        <body>
            <h1>Error {status.value} - {status.name}</h1>
            <p>{message}</p>
            <hr>
            <p><a href="/">Return to Home</a></p>
        </body>
        </html>
        """
        
        response.set_content(html_content)
        return response


class GeneWebServer:
    """Main GenEWeb HTTP server"""
    
    def __init__(self, server_config: ServerConfig):
        self.config = server_config
        self.running = False
        self.server_socket = None
        self.request_handler = None
        
        # Set up logging
        log_level = getattr(logging, server_config.log_level.upper())
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        self.logger = logging.getLogger('geneweb.server')
    
    def start(self) -> None:
        """Start the server"""
        self.logger.info(f"Starting GenEWeb server on {self.config.host}:{self.config.port}")
        
        # Create request handler
        geneweb_config = Config()  # Default config
        db_driver = None  # Will be created per request
        security_manager = create_security_manager(geneweb_config)
        
        self.request_handler = RequestHandler(
            self.config, geneweb_config, db_driver, security_manager
        )
        
        # Start server loop
        asyncio.run(self._server_loop())
    
    async def _server_loop(self) -> None:
        """Main server loop"""
        # Create server socket
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.config.host, self.config.port))
        self.server_socket.listen(self.config.max_connections)
        self.server_socket.setblocking(False)
        
        self.running = True
        self.logger.info(f"Server listening on {self.config.host}:{self.config.port}")
        
        try:
            while self.running:
                try:
                    # Accept connection
                    client_socket, addr = await asyncio.get_event_loop().sock_accept(self.server_socket)
                    
                    # Handle request in background
                    asyncio.create_task(self._handle_client(client_socket, addr))
                
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    self.logger.error(f"Error accepting connection: {e}")
        
        finally:
            if self.server_socket:
                self.server_socket.close()
    
    async def _handle_client(self, client_socket: socket.socket, addr: Tuple[str, int]) -> None:
        """Handle individual client connection"""
        try:
            # Ne pas utiliser settimeout avec asyncio - ça cause des conflits
            # client_socket.settimeout(self.config.timeout)
            
            # Read request with better error handling
            request_data = b""
            try:
                # Utiliser asyncio.wait_for pour gérer les timeouts proprement
                while True:
                    try:
                        data = await asyncio.wait_for(
                            asyncio.get_event_loop().sock_recv(client_socket, 4096),
                            timeout=self.config.timeout
                        )
                        if not data:
                            break
                        request_data += data
                        
                        # Check if we have complete headers
                        if b"\\r\\n\\r\\n" in request_data or b"\\n\\n" in request_data:
                            # Parse Content-Length to see if we need more data
                            header_text = request_data.decode('utf-8', errors='ignore')
                            
                            content_length = 0
                            for line in header_text.split('\\n'):
                                line = line.strip()
                                if line.lower().startswith('content-length:'):
                                    try:
                                        content_length = int(line.split(':', 1)[1].strip())
                                    except (ValueError, IndexError):
                                        content_length = 0
                                    break
                            
                            # Calculate how much body we have
                            if b"\\r\\n\\r\\n" in request_data:
                                header_end = request_data.find(b"\\r\\n\\r\\n") + 4
                            else:
                                header_end = request_data.find(b"\\n\\n") + 2
                            
                            body_received = len(request_data) - header_end
                            if body_received >= content_length:
                                break
                        
                        # Prevent too large requests
                        if len(request_data) > 1024 * 1024:  # 1MB limit
                            break
                    
                    except asyncio.TimeoutError:
                        # Timeout normal - traiter ce qu'on a reçu
                        if request_data:
                            break
                        else:
                            return  # Rien reçu, abandonner
                
                if not request_data:
                    return  # Empty request
                
            except Exception as e:
                self.logger.error(f"Error reading request from {addr}: {e}")
                return
            
            # Parse request with better error handling
            try:
                request = self._parse_http_request(request_data, addr[0])
            except Exception as e:
                self.logger.error(f"Error parsing HTTP request from {addr}: {e}")
                # Send 400 Bad Request
                error_response = HTTPResponse()
                error_response.set_status(HttpStatus.BAD_REQUEST)
                error_response.set_content("Bad Request")
                try:
                    await asyncio.get_event_loop().sock_sendall(client_socket, error_response.to_bytes())
                except:
                    pass
                return
            
            # Handle request
            response = await self.request_handler.handle_request(request)
            
            # Send response
            try:
                await asyncio.wait_for(
                    asyncio.get_event_loop().sock_sendall(client_socket, response.to_bytes()),
                    timeout=self.config.timeout
                )
            except asyncio.TimeoutError:
                self.logger.warning(f"Timeout sending response to {addr}")
            except Exception as e:
                self.logger.error(f"Error sending response to {addr}: {e}")
        
        except Exception as e:
            self.logger.error(f"Error handling client {addr}: {e}")
            
            # Send error response
            try:
                error_response = HTTPResponse()
                error_response.set_status(HttpStatus.INTERNAL_SERVER_ERROR)
                error_response.set_content("Internal Server Error")
                await asyncio.wait_for(
                    asyncio.get_event_loop().sock_sendall(client_socket, error_response.to_bytes()),
                    timeout=5.0  # Plus court timeout pour les erreurs
                )
            except:
                pass
        
        finally:
            # Fermer le socket proprement
            try:
                client_socket.close()
            except:
                pass
    
    def _parse_http_request(self, request_data: bytes, remote_addr: str) -> HTTPRequest:
        """Parse raw HTTP request data"""
        if not request_data:
            raise ValueError("Empty HTTP request")
        
        # Split headers and body
        header_end = request_data.find(b"\\r\\n\\r\\n")
        if header_end == -1:
            # No body, try just \n\n
            header_end = request_data.find(b"\\n\\n")
            if header_end == -1:
                headers_data = request_data.decode('utf-8', errors='ignore')
                body = b""
            else:
                headers_data = request_data[:header_end].decode('utf-8', errors='ignore')
                body = request_data[header_end + 2:]
        else:
            headers_data = request_data[:header_end].decode('utf-8', errors='ignore')
            body = request_data[header_end + 4:]
        
        # Handle different line endings
        lines = headers_data.replace('\\r\\n', '\\n').split('\\n')
        lines = [line.strip() for line in lines if line.strip()]
        
        if not lines:
            raise ValueError("Invalid HTTP request - no lines")
        
        # Parse request line
        request_line = lines[0]
        parts = request_line.split(' ')
        
        if len(parts) < 2:
            raise ValueError(f"Invalid HTTP request line: '{request_line}'")
        elif len(parts) == 2:
            # Missing HTTP version, add default
            method, path = parts
            version = "HTTP/1.0"
        else:
            method, path, version = parts[0], parts[1], ' '.join(parts[2:])
        
        # Validate method and path
        if not method or not path:
            raise ValueError(f"Invalid method or path: method='{method}', path='{path}'")
        
        # Extract path and query string
        if '?' in path:
            path, query_string = path.split('?', 1)
        else:
            query_string = ""
        
        # Parse headers
        headers = {}
        for line in lines[1:]:
            if ':' in line:
                key, value = line.split(':', 1)
                headers[key.strip().lower()] = value.strip()
        
        # Create request object
        request = HTTPRequest(method, path, query_string, headers, body)
        request.remote_addr = remote_addr
        
        return request
    
    def stop(self) -> None:
        """Stop the server"""
        self.logger.info("Stopping GenEWeb server")
        self.running = False


def start_server(host: str = "localhost", port: int = 2317, database_dir: str = "databases", 
                debug: bool = False, daemon: bool = False) -> None:
    """Start the GenEWeb server"""
    config = ServerConfig(
        host=host,
        port=port,
        database_directory=database_dir,
        debug=debug,
        daemon=daemon
    )
    
    if daemon:
        # Fork to background (Unix only)
        if hasattr(os, 'fork'):
            pid = os.fork()
            if pid > 0:
                # Parent process - exit
                sys.exit(0)
            
            # Child process continues
            os.setsid()  # Create new session
    
    server = GeneWebServer(config)
    
    try:
        server.start()
    except KeyboardInterrupt:
        logging.info("Server interrupted by user")
    finally:
        server.stop()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="GenEWeb Python Server")
    parser.add_argument("--host", default="localhost", help="Host to bind to")
    parser.add_argument("--port", type=int, default=2317, help="Port to bind to")
    parser.add_argument("--database-dir", default="databases", help="Directory containing databases")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--daemon", action="store_true", help="Run as daemon")
    
    args = parser.parse_args()
    
    start_server(
        host=args.host,
        port=args.port,
        database_dir=args.database_dir,
        debug=args.debug,
        daemon=args.daemon
    )
