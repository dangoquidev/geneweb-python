#!/usr/bin/env python3
"""
Core functionality for GenEWeb Admin Panel

This module implements the core admin panel functionality, similar to the
setup.ml file in the original OCaml implementation.
"""

import json
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

        # API routes for React frontend
        if path.startswith("/api/"):
            self.handle_api_request("GET", path, query)
        else:
            # For now, return a simple message
            # React frontend will be served by the main app
            self.serve_simple_response()

    def do_POST(self):
        """Handle POST requests"""
        parsed_url = urlparse(self.path)
        path = parsed_url.path

        # Read POST data
        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length).decode("utf-8")
        query = parse_qs(post_data)

        # API routes for React frontend
        if path.startswith("/api/"):
            self.handle_api_request("POST", path, query)
        else:
            self.serve_simple_response()

    def serve_simple_response(self):
        """Serve a simple response for admin panel"""
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

        response = {
            "message": "GenEWeb Admin Panel API",
            "status": "running",
            "port": self.config.port,
            "gwd_port": self.config.gwd_port,
            "database_dir": os.path.abspath(self.config.database_dir)
        }
        
        self.wfile.write(json.dumps(response, indent=2).encode("utf-8"))

    def handle_api_request(self, method: str, path: str, data: dict):
        """Handle API requests for React frontend"""
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

        # API endpoint routing
        try:
            # Home / Status routes
            if path == "/api/status":
                response = self.get_status_data()
            elif path == "/api/home":
                response = self.get_home_data()
            
            # Consult routes
            elif path == "/api/consult/databases":
                response = self.get_databases_data()
            elif path == "/api/consult/errors":
                response = self.get_error_history_data()
            elif path == "/api/consult/traces":
                response = self.get_traces_data()
            
            # Save routes
            elif path == "/api/save/gedcom":
                response = self.handle_save_gedcom(method, data)
            elif path == "/api/save/geneweb":
                response = self.handle_save_geneweb(method, data)
            
            # Create routes
            elif path == "/api/create/from-gedcom":
                response = self.handle_create_from_gedcom(method, data)
            elif path == "/api/create/from-geneweb":
                response = self.handle_create_from_geneweb(method, data)
            elif path == "/api/create/empty":
                response = self.handle_create_empty(method, data)
            
            # Advanced Options routes
            elif path == "/api/advanced/cleanup":
                response = self.handle_cleanup(method, data)
            elif path == "/api/advanced/rename":
                response = self.handle_rename(method, data)
            elif path == "/api/advanced/delete":
                response = self.handle_delete(method, data)
            elif path == "/api/advanced/merge":
                response = self.handle_merge(method, data)
            elif path == "/api/advanced/consang":
                response = self.handle_consang(method, data)
            elif path == "/api/advanced/update-nldb":
                response = self.handle_update_nldb(method, data)
            elif path == "/api/advanced/connex":
                response = self.handle_connex(method, data)
            elif path == "/api/advanced/gwdiff":
                response = self.handle_gwdiff(method, data)
            elif path == "/api/advanced/fixbase":
                response = self.handle_fixbase(method, data)
            
            # Configure routes
            elif path == "/api/config":
                response = self.get_config_data()
            elif path == "/api/config/gwd":
                response = self.handle_config_gwd(method, data)
            elif path == "/api/config/gwf":
                response = self.handle_config_gwf(method, data)
            elif path == "/api/config/cache-files":
                response = self.handle_config_cache_files(method, data)
            
            # Documentation and Languages routes
            elif path == "/api/documentation":
                response = self.get_documentation_data()
            elif path == "/api/languages":
                response = self.get_languages_data()
            elif path == "/api/set-language":
                response = self.handle_set_language(method, data)
            
            # Logs route (moved here for better organization)
            elif path == "/api/logs":
                response = self.get_logs_data()
            
            else:
                response = {"error": "API endpoint not found", "path": path, "method": method}
                
        except Exception as e:
            response = {"error": f"Server error: {str(e)}", "path": path, "method": method}

        self.wfile.write(json.dumps(response, indent=2).encode("utf-8"))

    def get_status_data(self) -> dict:
        """Get system status data"""
        return {
            "admin_server": {
                "port": self.config.port,
                "status": "running"
            },
            "main_server": {
                "port": self.config.gwd_port,
                "status": "configured"  # TODO: Check if actually running
            },
            "database_dir": os.path.abspath(self.config.database_dir),
            "setup_dir": os.path.abspath(self.config.setup_dir),
            "bin_dir": os.path.abspath(self.config.bin_dir),
            "default_lang": self.config.default_lang
        }

    def get_databases_data(self) -> dict:
        """Get databases information"""
        try:
            databases = []
            for item in os.listdir(self.config.database_dir):
                if item.endswith(".pickle") or item.endswith(".gwb"):
                    name = item.replace(".pickle", "").replace(".gwb", "")
                    databases.append({
                        "name": name,
                        "filename": item,
                        "url": f"http://localhost:{self.config.gwd_port}/{name}"
                    })
            
            return {
                "databases": databases,
                "count": len(databases),
                "directory": os.path.abspath(self.config.database_dir)
            }
        except Exception as e:
            return {
                "error": f"Error reading database directory: {str(e)}",
                "databases": [],
                "count": 0
            }

    def get_config_data(self) -> dict:
        """Get configuration data"""
        return {
            "port": self.config.port,
            "gwd_port": self.config.gwd_port,
            "database_dir": self.config.database_dir,
            "setup_dir": self.config.setup_dir,
            "bin_dir": self.config.bin_dir,
            "daemon": self.config.daemon,
            "default_lang": self.config.default_lang,
            "only_file": self.config.only_file
        }

    def get_logs_data(self) -> dict:
        """Get logs data"""
        # TODO: Implement actual log reading
        return {
            "logs": [
                {"timestamp": "2024-01-01T00:00:00", "level": "INFO", "message": "Admin server started"},
                {"timestamp": "2024-01-01T00:01:00", "level": "INFO", "message": "System ready"}
            ],
            "message": "Log functionality to be implemented"
        }

    # ========================================================================
    # HOME / STATUS ROUTES
    # ========================================================================
    
    def get_home_data(self) -> dict:
        """Get home page data with all categories"""
        return {
            "categories": {
                "consult": {
                    "title": "Consult",
                    "items": ["Family Trees (list)", "Error history and statistics"]
                },
                "save": {
                    "title": "Save",
                    "items": ["GEDCOM source file (gwb2ged)", "GeneWeb source file (gwu)"]
                },
                "create": {
                    "title": "Create Family Tree",
                    "items": ["From GEDCOM source file (ged2gwb)", "From GeneWeb source file (gwc)", "From empty file (gwc)"]
                },
                "advanced": {
                    "title": "Advanced Options",
                    "items": ["Clean up", "Renaming", "Deletion", "Merging", "Consanguinities", "Update links", "Connected components", "Diff between bases", "Fix problems"]
                },
                "configure": {
                    "title": "Configure",
                    "items": ["Database parameters (.gwf)", "GWD service parameters", "Cache files"]
                },
                "documentation": {
                    "title": "Documentation",
                    "items": ["Complete GeneWeb documentation"]
                },
                "languages": {
                    "title": "Display Languages",
                    "items": ["Corsu", "Deutsch", "English", "Español", "Français", "Italiano", "Latviesu", "Svenska"]
                }
            }
        }

    # ========================================================================
    # CONSULT ROUTES
    # ========================================================================
    
    def get_error_history_data(self) -> dict:
        """Get error history and statistics"""
        # TODO: Implement error history reading
        return {
            "error_history": [],
            "statistics": {
                "total_errors": 0,
                "last_24h": 0,
                "last_week": 0
            },
            "message": "Error history functionality to be implemented"
        }
    
    def get_traces_data(self) -> dict:
        """Get traces of the latest command (comm.log content)"""
        try:
            comm_log_path = os.path.join(self.config.database_dir, "comm.log")
            gwsetup_log_path = os.path.join(self.config.database_dir, "gwsetup.log")
            
            traces = {"comm_log": "", "gwsetup_log": ""}
            
            if os.path.exists(comm_log_path):
                with open(comm_log_path, "r", encoding="utf-8") as f:
                    traces["comm_log"] = f.read()
            else:
                traces["comm_log"] = "no traces"
                
            if os.path.exists(gwsetup_log_path):
                with open(gwsetup_log_path, "r", encoding="utf-8") as f:
                    traces["gwsetup_log"] = f.read()
            else:
                traces["gwsetup_log"] = "no traces"
                
            return {"traces": traces}
        except Exception as e:
            return {"error": f"Error reading trace files: {str(e)}"}

    # ========================================================================
    # SAVE ROUTES
    # ========================================================================
    
    def handle_save_gedcom(self, method: str, data: dict) -> dict:
        """Handle GEDCOM export (gwb2ged)"""
        if method == "GET":
            # Return form data for GEDCOM export
            return {
                "databases": self._get_database_list(),
                "charsets": ["ASCII", "UTF-8", "ANSEL", "ANSI"],
                "options": {
                    "mem": "Save memory space (slower)",
                    "nn": "Do not extract notes",
                    "nopicture": "Don't extract individual pictures",
                    "picture-path": "Extract individual pictures path"
                },
                "filters": {
                    "ancestors": "Extract only ancestors of person",
                    "descendants": "Extract only descendants of person", 
                    "aws": "Extract ancestors with siblings",
                    "surname": "Extract surname",
                    "censor": "Censor persons < N years"
                }
            }
        elif method == "POST":
            # TODO: Process GEDCOM export request
            return {
                "status": "processing",
                "message": "GEDCOM export functionality to be implemented",
                "command": "gwb2ged",
                "data": data
            }
    
    def handle_save_geneweb(self, method: str, data: dict) -> dict:
        """Handle GeneWeb export (gwu)"""
        if method == "GET":
            # Return form data for GeneWeb export
            return {
                "databases": self._get_database_list(),
                "options": {
                    "isolated": "Save isolated persons",
                    "all_files": "Save all files in notes_d",
                    "mem": "Save memory space (slower)"
                },
                "filters": {
                    "ancestors": "Ancestors of person",
                    "descendants": "Descendants of person"
                }
            }
        elif method == "POST":
            # TODO: Process GeneWeb export request
            return {
                "status": "processing", 
                "message": "GeneWeb export functionality to be implemented",
                "command": "gwu",
                "data": data
            }

    # ========================================================================
    # CREATE ROUTES
    # ========================================================================
    
    def handle_create_from_gedcom(self, method: str, data: dict) -> dict:
        """Handle creating database from GEDCOM file (ged2gwb)"""
        if method == "GET":
            return {
                "form": {
                    "file_selection": "Browse for .ged files",
                    "output_name": "Database name",
                    "output_dir": "Output directory"
                },
                "name_options": {
                    "lf": "Lowercase first names with capitals",
                    "ls": "Lowercase surnames with preserved particles", 
                    "efn": "Extract first name only",
                    "fne": "Handle first names between delimiters",
                    "epn": "Public names: detect nobility titles",
                    "no_epn": "Disable public names detection"
                },
                "date_options": {
                    "dates_dm": "Date format Day/Month/Year",
                    "dates_md": "Date format Month/Day/Year",
                    "tnd": "Handle negative/inconsistent dates",
                    "no_nd": "Disable negative dates"
                },
                "content_options": {
                    "nopicture": "Don't extract pictures",
                    "uin": "Insert unprocessed tags in notes",
                    "ds": "Default source",
                    "rs_no_mention": "Force relationship status"
                },
                "quality_options": {
                    "nc": "Disable consistency check",
                    "f": "Overwrite existing database",
                    "org": "Optimize structure"
                }
            }
        elif method == "POST":
            # TODO: Process GEDCOM import
            return {
                "status": "processing",
                "message": "GEDCOM import functionality to be implemented", 
                "command": "ged2gwb",
                "data": data
            }
    
    def handle_create_from_geneweb(self, method: str, data: dict) -> dict:
        """Handle creating database from GeneWeb file (gwc)"""
        if method == "GET":
            return {
                "form": {
                    "file_selection": "Browse for .gw files",
                    "output_name": "Database name",
                    "output_dir": "Output directory"
                },
                "options": {
                    "traces": "Show processing statistics",
                    "nc": "Disable consistency check",
                    "cg": "Calculate consanguinity after import",
                    "f": "Overwrite existing database",
                    "gwo": "Clean: remove .gwo files after creation",
                    "reorg": "Enable reorganization mode"
                }
            }
        elif method == "POST":
            # TODO: Process GeneWeb import
            return {
                "status": "processing",
                "message": "GeneWeb import functionality to be implemented",
                "command": "gwc", 
                "data": data
            }
    
    def handle_create_empty(self, method: str, data: dict) -> dict:
        """Handle creating empty database"""
        if method == "GET":
            return {
                "form": {
                    "database_name": "Database name (default: base)",
                    "reorg": "Enable reorganization mode"
                }
            }
        elif method == "POST":
            # TODO: Process empty database creation
            return {
                "status": "processing",
                "message": "Empty database creation functionality to be implemented",
                "command": "gwc_empty",
                "data": data
            }

    # ========================================================================
    # ADVANCED OPTIONS ROUTES
    # ========================================================================
    
    def handle_cleanup(self, method: str, data: dict) -> dict:
        """Handle database cleanup"""
        if method == "GET":
            return {
                "databases": self._get_database_list(),
                "cleanup_types": {
                    "simple": "Simple cleanup (initialize consanguinities)",
                    "radical": "Radical cleanup (full database cleanup)"
                }
            }
        elif method == "POST":
            # TODO: Process cleanup
            return {
                "status": "processing",
                "message": "Database cleanup functionality to be implemented",
                "command": "cleanup",
                "data": data
            }
    
    def handle_rename(self, method: str, data: dict) -> dict:
        """Handle database renaming"""
        if method == "GET":
            databases = self._get_database_list()
            return {
                "databases": databases,
                "form": {db["name"]: f"New name for {db['name']}" for db in databases}
            }
        elif method == "POST":
            # TODO: Process renaming
            return {
                "status": "processing",
                "message": "Database renaming functionality to be implemented",
                "command": "rename",
                "data": data
            }
    
    def handle_delete(self, method: str, data: dict) -> dict:
        """Handle database deletion"""
        if method == "GET":
            return {
                "databases": self._get_database_list(),
                "warning": "Deletion is permanent and cannot be undone"
            }
        elif method == "POST":
            # TODO: Process deletion
            return {
                "status": "processing", 
                "message": "Database deletion functionality to be implemented",
                "command": "delete",
                "data": data,
                "warning": "This action is irreversible"
            }
    
    def handle_merge(self, method: str, data: dict) -> dict:
        """Handle database merging"""
        if method == "GET":
            return {
                "databases": self._get_database_list(),
                "requirement": "All databases must be in GeneWeb format",
                "note": "Merging = simple concatenation (no deduplication)",
                "output_name": "Name for merged database"
            }
        elif method == "POST":
            # TODO: Process merging
            return {
                "status": "processing",
                "message": "Database merging functionality to be implemented",
                "command": "merge",
                "data": data
            }
    
    def handle_consang(self, method: str, data: dict) -> dict:
        """Handle consanguinity initialization"""
        if method == "GET":
            return {
                "databases": self._get_database_list(),
                "options": {
                    "scratch": "Restart computing from scratch"
                },
                "purpose": "Initialize consanguinities for consultation display"
            }
        elif method == "POST":
            # TODO: Process consanguinity calculation
            return {
                "status": "processing",
                "message": "Consanguinity calculation functionality to be implemented",
                "command": "consang",
                "data": data
            }
    
    def handle_update_nldb(self, method: str, data: dict) -> dict:
        """Handle update links page / family chronicle"""
        if method == "GET":
            return {
                "databases": self._get_database_list(),
                "purpose": "Update links page and family chronicle"
            }
        elif method == "POST":
            # TODO: Process nldb update
            return {
                "status": "processing",
                "message": "NLDB update functionality to be implemented", 
                "command": "update_nldb",
                "data": data
            }
    
    def handle_connex(self, method: str, data: dict) -> dict:
        """Handle connected components computation"""
        if method == "GET":
            return {
                "databases": self._get_database_list(),
                "options": {
                    "a": "All connected components",
                    "s": "Produce connected components statistics", 
                    "d": "Details length",
                    "i": "Ignore file",
                    "bf": "By origin file"
                },
                "deletion_options": {
                    "del": "Delete branches whose size ≤ value",
                    "cnt": "Number of branches to be deleted",
                    "exact": "Restrict deleting branches whose size = -del"
                },
                "output_options": {
                    "file": "Output to specified file",
                    "basename": "Output to basename/notes_d/connex.txt",
                    "none": "No redirection of results"
                },
                "warning": "Deletion commands are irreversible - backup recommended"
            }
        elif method == "POST":
            # TODO: Process connex computation
            return {
                "status": "processing",
                "message": "Connected components computation functionality to be implemented",
                "command": "connex", 
                "data": data,
                "warning": "May take seconds or minutes"
            }
    
    def handle_gwdiff(self, method: str, data: dict) -> dict:
        """Handle difference computation between two databases"""
        if method == "GET":
            databases = self._get_database_list()
            return {
                "databases": databases,
                "form": {
                    "base1": {
                        "database": "First database",
                        "first_name": "First name (mandatory)",
                        "num": "Number (mandatory)", 
                        "surname": "Surname (mandatory)"
                    },
                    "base2": {
                        "database": "Second database",
                        "first_name": "First name (mandatory)",
                        "num": "Number (mandatory)",
                        "surname": "Surname (mandatory)"
                    }
                },
                "options": {
                    "ad": "Check descendants of all ascendants",
                    "d": "Check descendants (default)",
                    "mem": "Save memory space (slower)"
                }
            }
        elif method == "POST":
            # TODO: Process diff computation
            return {
                "status": "processing",
                "message": "Database difference computation functionality to be implemented",
                "command": "gwdiff",
                "data": data
            }
    
    def handle_fixbase(self, method: str, data: dict) -> dict:
        """Handle fix base and recompute index"""
        if method == "GET":
            return {
                "databases": self._get_database_list(),
                "options": {
                    "dry-run": "Do not commit changes (only traces)",
                    "q": "Quiet mode",
                    "qq": "Very quiet mode", 
                    "fast": "Fast mode (needs more memory)",
                    "families-parents": "Families' parents",
                    "families-children": "Families' children",
                    "persons-NBDS": "Persons' NBDS",
                    "persons-parents": "Persons' parents",
                    "persons-families": "Persons' families",
                    "pevents-witnesses": "Personal events' witnesses", 
                    "fevents-witnesses": "Family events' witnesses",
                    "marriage-divorce": "Marriage divorce",
                    "index": "Index (automatically enabled by any other option)",
                    "help": "Help"
                }
            }
        elif method == "POST":
            # TODO: Process base fixing
            return {
                "status": "processing",
                "message": "Base fixing functionality to be implemented",
                "command": "fixbase",
                "data": data
            }

    # ========================================================================
    # CONFIGURE ROUTES
    # ========================================================================
    
    def handle_config_gwd(self, method: str, data: dict) -> dict:
        """Handle GWD service configuration"""
        if method == "GET":
            return {
                "form": {
                    "lang": {
                        "label": "Default language",
                        "type": "select",
                        "options": ["co", "de", "en", "es", "fr", "it", "lv", "sv"],
                        "current": self.config.default_lang
                    },
                    "only": {
                        "label": "Only authorized address", 
                        "type": "text",
                        "current": ""
                    },
                    "log": {
                        "label": "Connection log file",
                        "type": "text", 
                        "current": ""
                    }
                },
                "current_config_file": "gwd.arg",
                "location": "gw directory of GeneWeb distribution"
            }
        elif method == "POST":
            # TODO: Process GWD configuration update
            return {
                "status": "updated",
                "message": "GWD parameters updated",
                "instruction": "Stop and restart gwd service to apply parameters",
                "config_file": "gwd.arg",
                "data": data
            }
    
    def handle_config_gwf(self, method: str, data: dict) -> dict:
        """Handle database (.gwf) configuration"""
        if method == "GET":
            return {
                "form": {
                    "appearance": {
                        "body_prop": {
                            "label": "Body properties (HTML style)",
                            "type": "textarea",
                            "example": 'style="background-color:lightblue; color:#CC0000; vlink:yellow"'
                        }
                    },
                    "language": {
                        "default_lang": {
                            "label": "Default language",
                            "type": "select",
                            "options": ["co", "de", "en", "es", "fr", "it", "lv", "sv"]
                        }
                    },
                    "display_limits": {
                        "max_anc_level": {"label": "Maximum ancestors level", "default": 8},
                        "max_desc_level": {"label": "Maximum descendants level", "default": 12},
                        "max_anc_tree": {"label": "Maximum ancestors tree level", "default": 7},
                        "max_desc_tree": {"label": "Maximum descendants tree level", "default": 4}
                    },
                    "history": {
                        "history": {"label": "History of updates", "type": "yesno"}
                    },
                    "images": {
                        "images_path": {"label": "Images path", "example": "http://... or file://..."}
                    },
                    "search": {
                        "hide_advanced_request": {"label": "Hide advanced request", "type": "yesno"}
                    },
                    "access": {
                        "friend_passwd": {"label": "Password for 'friends'", "description": "Access < 100 years"},
                        "wizard_passwd": {"label": "Password for 'Wizards'", "description": "Modification rights"},
                        "wizard_just_friend": {"label": "'Wizards' become simple 'friend'", "type": "yesno"},
                        "hide_private_names": {"label": "Hide private person names", "type": "yesno"},
                        "can_send_image": {"label": "Ability to send images", "type": "yesno"}
                    },
                    "misc": {
                        "renamed": {"label": "Base has been renamed", "description": "New name if renamed"},
                        "trailer": {"label": "Footer text", "description": "HTML allowed"},
                        "reorg": {"label": "Reorg mode", "type": "checkbox"}
                    }
                }
            }
        elif method == "POST":
            # TODO: Process GWF configuration update
            return {
                "status": "updated",
                "message": "Database parameters updated",
                "data": data
            }
    
    def handle_config_cache_files(self, method: str, data: dict) -> dict:
        """Handle cache files configuration"""
        if method == "GET":
            return {
                "databases": self._get_database_list(),
                "database_folder": ".",
                "options": {
                    "fn": "First names",
                    "sn": "Surnames", 
                    "al": "Aliases",
                    "pu": "Public names",
                    "qu": "Qualifiers"
                },
                "phases": {
                    "1": "Selection of database and options",
                    "2": "Confirmation and execution", 
                    "3": "Results display"
                }
            }
        elif method == "POST":
            # TODO: Process cache files generation
            return {
                "status": "processing",
                "message": "Cache files generation functionality to be implemented",
                "command": "cache_files",
                "data": data
            }

    # ========================================================================
    # DOCUMENTATION AND LANGUAGES ROUTES  
    # ========================================================================
    
    def get_documentation_data(self) -> dict:
        """Get documentation information"""
        return {
            "title": "Complete GeneWeb Documentation",
            "sections": [
                {"title": "User Manual", "url": "/docs/user"},
                {"title": "Admin Guide", "url": "/docs/admin"},
                {"title": "Developer Documentation", "url": "/docs/dev"},
                {"title": "API Reference", "url": "/docs/api"}
            ],
            "message": "Documentation functionality to be implemented"
        }
    
    def get_languages_data(self) -> dict:
        """Get available languages"""
        return {
            "languages": {
                "co": {"name": "Corsu", "native": "Corsu"},
                "de": {"name": "Deutsch", "native": "Deutsch"}, 
                "en": {"name": "English", "native": "English"},
                "es": {"name": "Español", "native": "Español"},
                "fr": {"name": "Français", "native": "Français"},
                "it": {"name": "Italiano", "native": "Italiano"},
                "lv": {"name": "Latviesu", "native": "Latviešu"},
                "sv": {"name": "Svenska", "native": "Svenska"}
            },
            "current": self.config.default_lang
        }
    
    def handle_set_language(self, method: str, data: dict) -> dict:
        """Handle language change"""
        if method == "POST":
            # TODO: Process language change
            language = data.get("language", [""])[0]
            return {
                "status": "changed",
                "message": f"Language changed to {language}",
                "previous": self.config.default_lang,
                "current": language,
                "data": data
            }
        else:
            return {"error": "POST method required"}

    # ========================================================================
    # HELPER METHODS
    # ========================================================================
    
    def _get_database_list(self) -> list:
        """Helper method to get list of databases"""
        try:
            databases = []
            for item in os.listdir(self.config.database_dir):
                if item.endswith(".pickle") or item.endswith(".gwb"):
                    name = item.replace(".pickle", "").replace(".gwb", "")
                    databases.append({
                        "name": name,
                        "filename": item,
                        "url": f"http://localhost:{self.config.gwd_port}/{name}",
                        "path": os.path.join(self.config.database_dir, item)
                    })
            return databases
        except Exception:
            return []

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