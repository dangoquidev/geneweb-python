"""
API Endpoints package
Contains modular endpoint handlers for the GenEWeb API
"""

from .database_endpoints import DatabaseEndpoints
from .search_endpoints import SearchEndpoints  
from .statistics_endpoints import StatisticsEndpoints

__all__ = [
    "DatabaseEndpoints",
    "SearchEndpoints", 
    "StatisticsEndpoints"
]
