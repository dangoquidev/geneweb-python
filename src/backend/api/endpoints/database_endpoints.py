"""
Database information endpoints
Handles database listing and information retrieval
"""

import json
import logging
import os
from typing import Dict, Any, List
from http.server import BaseHTTPRequestHandler

from ...geneweb.db.driver import create_database_driver, DatabaseInfo


class DatabaseEndpoints:
    """Handles database-related API endpoints"""
    
    def __init__(self, database_dir: str):
        self.database_dir = database_dir
        self.logger = logging.getLogger("geneweb.api.database")
    
    def handle_databases_list(self, handler: BaseHTTPRequestHandler) -> None:
        """
        GET /api/databases -> {"databases": ["name1", ...]}
        List all available databases
        """
        try:
            databases: List[str] = []
            try:
                for file in os.listdir(self.database_dir):
                    if file.endswith(".pickle"):
                        databases.append(file[:-7])  # Remove .pickle extension
            except OSError as e:
                self.logger.warning(f"Error reading database directory: {e}")
                pass
            
            payload = {"databases": sorted(databases)}
            self._send_json_response(handler, 200, payload)
            
        except Exception as e:
            self.logger.error(f"Error listing databases: {e}")
            handler.send_error(500, "Internal Server Error")
    
    def handle_database_info(self, handler: BaseHTTPRequestHandler, base_name: str) -> None:
        """
        GET /api/{base}/info -> database information
        Get detailed information about a specific database
        """
        try:
            base_path = os.path.join(self.database_dir, f"{base_name}.pickle")
            if not os.path.exists(base_path):
                handler.send_error(404, f"Database '{base_name}' not found")
                return
            
            # Open the database
            db_driver = create_database_driver(base_path, "pickle")
            if not db_driver.open_database(read_only=True):
                handler.send_error(500, "Cannot open database")
                return
            
            try:
                info = db_driver.get_database_info()
                payload = {
                    "base_name": base_name,
                    "persons": info.number_of_persons,
                    "families": info.number_of_families,
                    "path": info.path,
                    "version": info.version,
                    "created_date": info.created_date,
                    "modified_date": info.modified_date,
                }
                self._send_json_response(handler, 200, payload)
                
            finally:
                db_driver.close_database()
                
        except Exception as e:
            self.logger.error(f"Error getting database info for '{base_name}': {e}")
            handler.send_error(500, "Internal Server Error")
    
    def _send_json_response(self, handler: BaseHTTPRequestHandler, status_code: int, data: Dict[str, Any]) -> None:
        """Send a JSON response"""
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        handler.send_response(status_code)
        handler.send_header("Content-Type", "application/json; charset=utf-8")
        handler.send_header("Cache-Control", "no-store")
        handler.send_header("Content-Length", str(len(body)))
        handler.end_headers()
        handler.wfile.write(body)
