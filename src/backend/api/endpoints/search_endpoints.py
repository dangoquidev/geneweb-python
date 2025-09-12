"""
Search endpoints
Handles person and family search functionality
"""

import json
import logging
import os
import urllib.parse
from typing import Dict, Any, List
from http.server import BaseHTTPRequestHandler

from ...geneweb.db.driver import create_database_driver
from ...geneweb.util.string_utils import geneweb_date_to_string


class SearchEndpoints:
    """Handles search-related API endpoints"""
    
    def __init__(self, database_dir: str):
        self.database_dir = database_dir
        self.logger = logging.getLogger("geneweb.api.search")
    
    def handle_search(self, handler: BaseHTTPRequestHandler, base_name: str, query_string: str) -> None:
        """
        GET /api/{base}/search?q=term -> search results
        Search for persons in the database
        """
        try:
            base_path = os.path.join(self.database_dir, f"{base_name}.pickle")
            if not os.path.exists(base_path):
                handler.send_error(404, f"Database '{base_name}' not found")
                return
            
            # Parse query parameters
            params = urllib.parse.parse_qs(query_string)
            q = params.get("q", [""])[0] or params.get("search", [""])[0]
            max_results = int(params.get("limit", ["50"])[0])
            
            # Open the database
            db_driver = create_database_driver(base_path, "pickle")
            if not db_driver.open_database(read_only=True):
                handler.send_error(500, "Cannot open database")
                return
            
            try:
                results: List[Dict[str, str]] = []
                if q:
                    search_results = db_driver.search_persons(q, max_results=max_results)
                    for person_id, person in search_results:
                        # Format dates using helper methods
                        birth_date = self._get_person_attr(person, "birth_date")
                        death_date = self._get_death_date(person)
                        
                        results.append({
                            "id": str(person_id),
                            "first_name": str(self._get_person_attr(person, "first_name", "")),
                            "surname": str(self._get_person_attr(person, "surname", "")),
                            "public_name": str(self._get_person_attr(person, "public_name", "")),
                            "occupation": str(self._get_person_attr(person, "occupation", "")),
                            "sex": str(self._get_person_attr(person, "sex", "")),
                            "birth_date": self._format_date(birth_date),
                            "death_date": self._format_date(death_date),
                            "birth_place": str(self._get_person_attr(person, "birth_place", "")),
                            "death_place": str(self._get_person_attr(person, "death_place", "")),
                        })
                
                payload = {
                    "base": base_name,
                    "query": q,
                    "results": results,
                    "total": len(results),
                    "limit": max_results
                }
                self._send_json_response(handler, 200, payload)
                
            finally:
                db_driver.close_database()
                
        except Exception as e:
            self.logger.error(f"Error searching in database '{base_name}': {e}")
            handler.send_error(500, "Internal Server Error")
    
    def handle_advanced_search(self, handler: BaseHTTPRequestHandler, base_name: str, query_string: str) -> None:
        """
        GET /api/{base}/search/advanced -> advanced search with filters
        Advanced search with multiple criteria
        """
        try:
            base_path = os.path.join(self.database_dir, f"{base_name}.pickle")
            if not os.path.exists(base_path):
                handler.send_error(404, f"Database '{base_name}' not found")
                return
            
            # Parse query parameters
            params = urllib.parse.parse_qs(query_string)
            first_name = params.get("first_name", [""])[0]
            surname = params.get("surname", [""])[0]
            birth_year = params.get("birth_year", [""])[0]
            death_year = params.get("death_year", [""])[0]
            occupation = params.get("occupation", [""])[0]
            sex = params.get("sex", [""])[0]
            max_results = int(params.get("limit", ["100"])[0])
            
            # Open the database
            db_driver = create_database_driver(base_path, "pickle")
            if not db_driver.open_database(read_only=True):
                handler.send_error(500, "Cannot open database")
                return
            
            try:
                results: List[Dict[str, str]] = []
                
                # Perform advanced search by iterating through all persons
                # This is a simple implementation - could be optimized with proper indexing
                for person_id, person in db_driver.get_persons():
                    if len(results) >= max_results:
                        break
                    
                    # Apply filters
                    if first_name and first_name.lower() not in str(self._get_person_attr(person, "first_name", "")).lower():
                        continue
                    if surname and surname.lower() not in str(self._get_person_attr(person, "surname", "")).lower():
                        continue
                    if occupation and occupation.lower() not in str(self._get_person_attr(person, "occupation", "")).lower():
                        continue
                    if sex and sex.upper() != str(self._get_person_attr(person, "sex", "")).upper():
                        continue
                    
                    # Date filters (simplified - could be enhanced)
                    if birth_year:
                        birth_date = self._get_person_attr(person, "birth_date")
                        birth_year_from_date = self._extract_year_from_date(birth_date)
                        if birth_year_from_date and str(birth_year_from_date) != birth_year:
                            continue
                    
                    if death_year:
                        death_date = self._get_death_date(person)
                        death_year_from_date = self._extract_year_from_date(death_date)
                        if death_year_from_date and str(death_year_from_date) != death_year:
                            continue
                    
                    # Format dates using helper methods
                    birth_date = self._get_person_attr(person, "birth_date")
                    death_date = self._get_death_date(person)
                    
                    results.append({
                        "id": str(person_id),
                        "first_name": str(self._get_person_attr(person, "first_name", "")),
                        "surname": str(self._get_person_attr(person, "surname", "")),
                        "public_name": str(self._get_person_attr(person, "public_name", "")),
                        "occupation": str(self._get_person_attr(person, "occupation", "")),
                        "sex": str(self._get_person_attr(person, "sex", "")),
                        "birth_date": self._format_date(birth_date),
                        "death_date": self._format_date(death_date),
                        "birth_place": str(self._get_person_attr(person, "birth_place", "")),
                        "death_place": str(self._get_person_attr(person, "death_place", "")),
                    })
                
                payload = {
                    "base": base_name,
                    "filters": {
                        "first_name": first_name,
                        "surname": surname,
                        "birth_year": birth_year,
                        "death_year": death_year,
                        "occupation": occupation,
                        "sex": sex,
                    },
                    "results": results,
                    "total": len(results),
                    "limit": max_results
                }
                self._send_json_response(handler, 200, payload)
                
            finally:
                db_driver.close_database()
                
        except Exception as e:
            self.logger.error(f"Error in advanced search for database '{base_name}': {e}")
            handler.send_error(500, "Internal Server Error")
    
    def _get_person_attr(self, person, attr_name: str, default=None):
        """Get attribute from person (handles both dict and object)"""
        if isinstance(person, dict):
            value = person.get(attr_name, default)
        else:
            value = getattr(person, attr_name, default)
        
        # Handle special case for sex field which might be a complex object
        if attr_name == "sex" and isinstance(value, dict):
            return value.get("value", str(value))
        
        return value
    
    def _get_death_date(self, person):
        """Get death date from person (handles different storage formats)"""
        # Try direct death_date attribute first
        death_date = self._get_person_attr(person, "death_date")
        if death_date:
            return death_date
        
        # Try death.date structure
        death = self._get_person_attr(person, "death")
        if death:
            if isinstance(death, dict):
                return death.get("date")
            else:
                return getattr(death, "date", None)
        
        return None
    
    def _extract_year_from_date(self, date_obj):
        """Extract year from various date formats"""
        if not date_obj:
            return None
        
        # Handle dictionary format
        if isinstance(date_obj, dict):
            gregorian_date = date_obj.get("gregorian_date")
            if gregorian_date and isinstance(gregorian_date, list) and len(gregorian_date) > 0:
                date_my = gregorian_date[0]
                if isinstance(date_my, dict):
                    return date_my.get("year")
        
        # Handle object format
        elif hasattr(date_obj, "gregorian_date") and date_obj.gregorian_date:
            if isinstance(date_obj.gregorian_date, tuple) and len(date_obj.gregorian_date) > 0:
                date_my = date_obj.gregorian_date[0]
                if hasattr(date_my, "year"):
                    return date_my.year
        
        # Handle direct year attribute
        elif hasattr(date_obj, "year"):
            return date_obj.year
        
        return None
    
    def _format_date(self, date_obj) -> str:
        """Format date object to string"""
        if not date_obj:
            return ""
        
        # Handle dictionary format
        if isinstance(date_obj, dict):
            text_date = date_obj.get("text_date")
            if text_date:
                return text_date
            
            gregorian_date = date_obj.get("gregorian_date")
            if gregorian_date and isinstance(gregorian_date, list) and len(gregorian_date) > 0:
                date_my = gregorian_date[0]
                if isinstance(date_my, dict):
                    year = date_my.get("year", 0)
                    month = date_my.get("month", 0)
                    day = date_my.get("day", 0)
                    if year:
                        if month and day:
                            return f"{day:02d}/{month:02d}/{year}"
                        elif month:
                            return f"{month:02d}/{year}"
                        else:
                            return str(year)
        
        # Fallback to geneweb_date_to_string if available
        try:
            return geneweb_date_to_string(date_obj)
        except:
            return str(date_obj) if date_obj else ""

    def _send_json_response(self, handler: BaseHTTPRequestHandler, status_code: int, data: Dict[str, Any]) -> None:
        """Send a JSON response"""
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        handler.send_response(status_code)
        handler.send_header("Content-Type", "application/json; charset=utf-8")
        handler.send_header("Cache-Control", "no-store")
        handler.send_header("Content-Length", str(len(body)))
        handler.end_headers()
        handler.wfile.write(body)
