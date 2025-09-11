"""
Statistics endpoints
Handles statistical queries and analysis of genealogical data
"""

import json
import logging
import os
import urllib.parse
from typing import Dict, Any, List, Optional, Tuple
from http.server import BaseHTTPRequestHandler
from datetime import datetime, date
from collections import defaultdict

from ...geneweb.db.driver import create_database_driver
from ...geneweb.util.string_utils import geneweb_date_to_string


class StatisticsEndpoints:
    """Handles statistics-related API endpoints"""
    
    def __init__(self, database_dir: str):
        self.database_dir = database_dir
        self.logger = logging.getLogger("geneweb.api.statistics")
    
    def handle_statistics(self, handler: BaseHTTPRequestHandler, base_name: str, stat_type: str, query_string: str) -> None:
        """
        GET /api/{base}/statistics/{stat_type} -> statistical data
        Handle different types of statistical queries
        """
        try:
            base_path = os.path.join(self.database_dir, f"{base_name}.pickle")
            if not os.path.exists(base_path):
                handler.send_error(404, f"Database '{base_name}' not found")
                return
            
            # Parse query parameters
            params = urllib.parse.parse_qs(query_string)
            limit = int(params.get("limit", ["20"])[0])
            
            # Open the database
            db_driver = create_database_driver(base_path, "pickle")
            if not db_driver.open_database(read_only=True):
                handler.send_error(500, "Cannot open database")
                return

            try:
                # Route to appropriate statistics handler
                if stat_type == "latest-births":
                    result = self._get_latest_births(db_driver, limit)
                elif stat_type == "latest-deaths":
                    result = self._get_latest_deaths(db_driver, limit)
                elif stat_type == "latest-marriages":
                    result = self._get_latest_marriages(db_driver, limit)
                elif stat_type == "oldest-couples":
                    result = self._get_oldest_couples(db_driver, limit)
                elif stat_type == "oldest-people":
                    result = self._get_oldest_people(db_driver, limit)
                elif stat_type == "longest-lived":
                    result = self._get_longest_lived(db_driver, limit)
                elif stat_type == "population-pyramid":
                    result = self._get_population_pyramid(db_driver)
                elif stat_type == "general-stats":
                    result = self._get_general_statistics(db_driver)
                else:
                    handler.send_error(404, f"Unknown statistics type: {stat_type}")
                    return

                payload = {
                    "base": base_name,
                    "stat_type": stat_type,
                    "results": result,  # Frontend expects 'results', not 'data'
                    "data": result,     # Keep both for compatibility
                    "generated_at": datetime.now().isoformat()
                }
                self._send_json_response(handler, 200, payload)
                
            finally:
                db_driver.close_database()
                
        except Exception as e:
            self.logger.error(f"Error generating statistics '{stat_type}' for database '{base_name}': {e}")
            handler.send_error(500, "Internal Server Error")
    
    def _get_latest_births(self, db_driver, limit: int) -> List[Dict[str, Any]]:
        """Get the most recent births"""
        births = []

        for person_id, person in db_driver.get_persons():
            birth_date = self._get_person_attr(person, "birth_date")
            birth_year = self._extract_year_from_date(birth_date)
            if birth_year:
                births.append({
                    "id": str(person_id),
                    "first_name": str(self._get_person_attr(person, "first_name", "")),
                    "surname": str(self._get_person_attr(person, "surname", "")),
                    "occupation": str(self._get_person_attr(person, "occupation", "")),  # Add missing field
                    "sex": str(self._get_person_attr(person, "sex", "")),
                    "birth_date": self._format_date(birth_date),
                    "death_date": "",  # Add missing field (empty for births)
                    "birth_place": str(self._get_person_attr(person, "birth_place", "")),
                    "year": birth_year
                })

        births.sort(key=lambda x: x["year"], reverse=True)
        return births[:limit]
    
    def _get_latest_deaths(self, db_driver, limit: int) -> List[Dict[str, Any]]:
        """Get the most recent deaths"""
        deaths = []
        
        for person_id, person in db_driver.get_persons():
            death_date = self._get_death_date(person)
            death_year = self._extract_year_from_date(death_date)
            
            if death_year:
                birth_date = self._get_person_attr(person, "birth_date")
                
                deaths.append({
                    "id": str(person_id),
                    "first_name": str(self._get_person_attr(person, "first_name", "")),
                    "surname": str(self._get_person_attr(person, "surname", "")),
                    "birth_date": self._format_date(birth_date),
                    "death_date": self._format_date(death_date),
                    "death_place": str(self._get_person_attr(person, "death_place", "")),
                    "sex": str(self._get_person_attr(person, "sex", "")),
                    "year": death_year
                })
        
        # Sort by death year (most recent first)
        deaths.sort(key=lambda x: x["year"], reverse=True)
        return deaths[:limit]
    
    def _get_latest_marriages(self, db_driver, limit: int) -> List[Dict[str, Any]]:
        """Get the most recent marriages"""
        marriages = []
        
        for family_id, family in db_driver.get_families():
            # Use direct attribute access like working search
            try:
                marriage_date = getattr(family, "marriage_date", None)
                marriage_year = self._extract_year_from_date(marriage_date)
                
                if marriage_year:
                    # Get spouse information using direct attribute access
                    husband_id = getattr(family, "father", None)
                    wife_id = getattr(family, "mother", None)
                    
                    husband = db_driver.get_person(husband_id) if husband_id else None
                    wife = db_driver.get_person(wife_id) if wife_id else None
                    
                    marriages.append({
                        "family_id": str(family_id),
                        "marriage_date": self._format_date(marriage_date),
                        "marriage_place": str(getattr(family, "marriage_place", "")),
                        "husband": {
                            "id": str(husband_id) if husband_id else "",
                            "first_name": str(getattr(husband, "first_name", "")) if husband else "",
                            "surname": str(getattr(husband, "surname", "")) if husband else "",
                        } if husband else None,
                        "wife": {
                            "id": str(wife_id) if wife_id else "",
                            "first_name": str(getattr(wife, "first_name", "")) if wife else "",
                            "surname": str(getattr(wife, "surname", "")) if wife else "",
                        } if wife else None,
                        "year": marriage_year
                    })
            except Exception as e:
                # Skip families with invalid data
                continue
        
        # Sort by marriage year (most recent first)
        marriages.sort(key=lambda x: x["year"], reverse=True)
        return marriages[:limit]
    
    def _get_oldest_couples(self, db_driver, limit: int) -> List[Dict[str, Any]]:
        """Get the oldest living couples"""
        couples = []
        current_year = datetime.now().year
        
        for family_id, family in db_driver.get_families():
            try:
                # Use direct attribute access like working search
                husband_id = getattr(family, "father", None)
                wife_id = getattr(family, "mother", None)
                
                if husband_id and wife_id:
                    husband = db_driver.get_person(husband_id)
                    wife = db_driver.get_person(wife_id)
                    
                    if husband and wife:
                        # Check if both are still alive (no death date)
                        husband_death = getattr(husband, "death", None)
                        wife_death = getattr(wife, "death", None)
                        
                        if not husband_death and not wife_death:
                            # Calculate ages using direct attribute access
                            husband_birth_date = getattr(husband, "birth_date", None)
                            wife_birth_date = getattr(wife, "birth_date", None)
                            
                            husband_birth_year = self._extract_year_from_date(husband_birth_date)
                            wife_birth_year = self._extract_year_from_date(wife_birth_date)
                            
                            if husband_birth_year and wife_birth_year:
                                husband_age = current_year - husband_birth_year
                                wife_age = current_year - wife_birth_year
                                combined_age = husband_age + wife_age
                                
                                marriage_date = getattr(family, "marriage_date", None)
                                
                                couples.append({
                                    "family_id": str(family_id),
                                    "husband": {
                                        "id": str(husband_id),
                                        "first_name": str(getattr(husband, "first_name", "")),
                                        "surname": str(getattr(husband, "surname", "")),
                                        "age": husband_age,
                                        "birth_date": self._format_date(husband_birth_date)
                                    },
                                    "wife": {
                                        "id": str(wife_id),
                                        "first_name": str(getattr(wife, "first_name", "")),
                                        "surname": str(getattr(wife, "surname", "")),
                                        "age": wife_age,
                                        "birth_date": self._format_date(wife_birth_date)
                                    },
                                    "combined_age": combined_age,
                                    "marriage_date": self._format_date(marriage_date)
                                })
            except Exception as e:
                # Skip couples with invalid data
                continue
        
        # Sort by combined age (oldest first)
        couples.sort(key=lambda x: x["combined_age"], reverse=True)
        return couples[:limit]
    
    def _get_oldest_people(self, db_driver, limit: int) -> List[Dict[str, Any]]:
        """Get the oldest living people"""
        people = []
        
        for person_id, person in db_driver.get_persons():
            # Check if person is still alive
            if not self._has_death_date(person):
                age = self._calculate_age(person)
                if age:
                    birth_date = self._get_person_attr(person, "birth_date")
                    people.append({
                        "id": str(person_id),
                        "first_name": str(self._get_person_attr(person, "first_name", "")),
                        "surname": str(self._get_person_attr(person, "surname", "")),
                        "sex": str(self._get_person_attr(person, "sex", "")),
                        "age": age,
                        "birth_date": self._format_date(birth_date),
                        "birth_place": str(self._get_person_attr(person, "birth_place", "")),
                    })
        
        # Sort by age (oldest first)
        people.sort(key=lambda x: x["age"], reverse=True)
        return people[:limit]
    
    def _get_longest_lived(self, db_driver, limit: int) -> List[Dict[str, Any]]:
        """Get people who lived the longest"""
        people = []
        
        for person_id, person in db_driver.get_persons():
            # Only include people who have died
            if self._has_death_date(person):
                lifespan = self._calculate_lifespan(person)
                if lifespan:
                    birth_date = self._get_person_attr(person, "birth_date")
                    death_date = self._get_death_date(person)
                    
                    people.append({
                        "id": str(person_id),
                        "first_name": str(self._get_person_attr(person, "first_name", "")),
                        "surname": str(self._get_person_attr(person, "surname", "")),
                        "sex": str(self._get_person_attr(person, "sex", "")),
                        "lifespan_years": lifespan,
                        "birth_date": self._format_date(birth_date),
                        "death_date": self._format_date(death_date),
                        "birth_place": str(self._get_person_attr(person, "birth_place", "")),
                        "death_place": str(self._get_person_attr(person, "death_place", "")),
                    })
        
        # Sort by lifespan (longest first)
        people.sort(key=lambda x: x["lifespan_years"], reverse=True)
        return people[:limit]
    
    def _get_population_pyramid(self, db_driver) -> Dict[str, Any]:
        """Generate population pyramid data grouped by birth year"""
        birth_years = defaultdict(lambda: {"male": 0, "female": 0, "unknown": 0})
        current_year = datetime.now().year
        total_living = 0
        
        for person_id, person in db_driver.get_persons():
            # Only count living people
            if not self._has_death_date(person):
                birth_date = self._get_person_attr(person, "birth_date")
                birth_year = self._extract_year_from_date(birth_date)
                
                if birth_year:
                    sex = str(self._get_person_attr(person, "sex", "")).upper()
                    total_living += 1
                    
                    if sex == "M" or "MALE" in sex:
                        birth_years[birth_year]["male"] += 1
                    elif sex == "F" or "FEMALE" in sex:
                        birth_years[birth_year]["female"] += 1
                    else:
                        birth_years[birth_year]["unknown"] += 1
        
        # Convert to timeline format (birth year to current year)
        pyramid_data = []
        
        # Get the range of years from oldest birth to current year
        if birth_years:
            min_year = min(birth_years.keys())
            max_year = current_year
            
            # Group by 5-year periods like in the original
            for year in range(min_year, max_year + 1, 5):
                period_start = year
                period_end = min(year + 4, max_year)
                
                # Sum up all births in this 5-year period
                period_male = 0
                period_female = 0
                period_unknown = 0
                
                for birth_year in range(period_start, period_end + 1):
                    if birth_year in birth_years:
                        period_male += birth_years[birth_year]["male"]
                        period_female += birth_years[birth_year]["female"]
                        period_unknown += birth_years[birth_year]["unknown"]
                
                age_at_period = current_year - period_start
                
                pyramid_data.append({
                    "birth_year": period_start,
                    "age": age_at_period,
                    "male": period_male,
                    "female": period_female,
                    "unknown": period_unknown,
                    "total": period_male + period_female + period_unknown
                })
        
        # Sort by birth year (oldest first)
        pyramid_data.sort(key=lambda x: x["birth_year"])
        
        return {
            "pyramid": pyramid_data,
            "total_living": total_living,
            "current_year": current_year
        }
    
    def _get_general_statistics(self, db_driver) -> Dict[str, Any]:
        """Get general database statistics"""
        stats = {
            "total_persons": 0,
            "total_families": 0,
            "living_persons": 0,
            "deceased_persons": 0,
            "males": 0,
            "females": 0,
            "unknown_sex": 0,
            "persons_with_birth_date": 0,
            "persons_with_death_date": 0,
            "oldest_birth_year": None,
            "newest_birth_year": None,
            "oldest_death_year": None,
            "newest_death_year": None,
        }
        
        birth_years = []
        death_years = []
        
        # Count persons
        for person_id, person in db_driver.get_persons():
            stats["total_persons"] += 1
            
            # Count by vital status - use direct attribute access like search
            death_date = getattr(person, "death", None)
            if death_date:
                stats["deceased_persons"] += 1
            else:
                stats["living_persons"] += 1
            
            # Count by sex
            sex = str(getattr(person, "sex", "")).upper()
            if sex == "M" or "MALE" in sex:
                stats["males"] += 1
            elif sex == "F" or "FEMALE" in sex:
                stats["females"] += 1
            else:
                stats["unknown_sex"] += 1
            
            # Birth dates - use same logic as working search
            try:
                birth_date = getattr(person, "birth_date", None)
                if birth_date and hasattr(birth_date, "gregorian_date") and birth_date.gregorian_date:
                    date_my, calendar = birth_date.gregorian_date
                    if hasattr(date_my, "year"):
                        stats["persons_with_birth_date"] += 1
                        birth_years.append(date_my.year)
            except:
                pass
            
            # Death dates
            try:
                death = getattr(person, "death", None)
                if death and hasattr(death, "date") and death.date:
                    death_date = death.date
                    if hasattr(death_date, "gregorian_date") and death_date.gregorian_date:
                        date_my, calendar = death_date.gregorian_date
                        if hasattr(date_my, "year"):
                            stats["persons_with_death_date"] += 1
                            death_years.append(date_my.year)
            except:
                pass
        
        # Count families
        for family_id, family in db_driver.get_families():
            stats["total_families"] += 1
        
        # Calculate year ranges
        if birth_years:
            stats["oldest_birth_year"] = min(birth_years)
            stats["newest_birth_year"] = max(birth_years)
        
        if death_years:
            stats["oldest_death_year"] = min(death_years)
            stats["newest_death_year"] = max(death_years)
        
        return stats
    
    def _has_death_date(self, person) -> bool:
        """Check if person has a death date"""
        death_date = self._get_death_date(person)
        return death_date is not None
    
    def _calculate_age(self, person) -> Optional[int]:
        """Calculate person's current age"""
        birth_date = self._get_person_attr(person, "birth_date")
        birth_year = self._extract_year_from_date(birth_date)
        if birth_year:
            current_year = datetime.now().year
            return current_year - birth_year
        return None
    
    def _calculate_lifespan(self, person) -> Optional[int]:
        """Calculate person's lifespan in years"""
        birth_date = self._get_person_attr(person, "birth_date")
        death_date = self._get_death_date(person)
        
        birth_year = self._extract_year_from_date(birth_date)
        death_year = self._extract_year_from_date(death_date)
        
        if birth_year and death_year:
            return death_year - birth_year
        return None
    
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
    
    def _get_family_attr(self, family, attr_name: str, default=None):
        """Get attribute from family (handles both dict and object)"""
        if isinstance(family, dict):
            return family.get(attr_name, default)
        else:
            return getattr(family, attr_name, default)
    
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
    
    def _extract_year_from_date(self, date_obj) -> Optional[int]:
        """Extract year from various date formats"""
        if not date_obj:
            return None
        
        # Handle object format first - check for text_date
        if hasattr(date_obj, "text_date") and date_obj.text_date:
            # Parse text date like "12 JAN 1940", "5 MAY 1942"
            try:
                text_date = date_obj.text_date
                # Split and get the last part which should be the year
                parts = text_date.strip().split()
                if parts:
                    year_str = parts[-1]  # Last part should be year
                    if year_str.isdigit() and len(year_str) == 4:
                        return int(year_str)
            except:
                pass
        
        # Handle gregorian_date format
        if hasattr(date_obj, "gregorian_date") and date_obj.gregorian_date:
            if isinstance(date_obj.gregorian_date, tuple) and len(date_obj.gregorian_date) > 0:
                date_my = date_obj.gregorian_date[0]
                if hasattr(date_my, "year"):
                    return date_my.year
        
        # Handle dictionary format
        if isinstance(date_obj, dict):
            # Check text_date first
            text_date = date_obj.get("text_date")
            if text_date:
                try:
                    parts = text_date.strip().split()
                    if parts:
                        year_str = parts[-1]
                        if year_str.isdigit() and len(year_str) == 4:
                            return int(year_str)
                except:
                    pass
            
            # Check gregorian_date
            gregorian_date = date_obj.get("gregorian_date")
            if gregorian_date and isinstance(gregorian_date, list) and len(gregorian_date) > 0:
                date_my = gregorian_date[0]
                if isinstance(date_my, dict):
                    return date_my.get("year")
        
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
