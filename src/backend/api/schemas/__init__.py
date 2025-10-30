"""
API schemas package.

Exports all Pydantic models for API requests and responses.
"""

from backend.api.schemas.common import (  # Base schemas; Person schemas; Family schemas; Search & pagination
    DatabaseStatistics,
    DateSchema,
    EventSchema,
    FamilyCreate,
    FamilyResponse,
    FamilyStatistics,
    FamilyUpdate,
    PaginatedResponse,
    PaginationParams,
    PersonCreate,
    PersonResponse,
    PersonStatistics,
    PersonUpdate,
    SearchQuery,
)
from backend.api.schemas.database import (
    DatabaseCreateRequest,
    DatabaseCreateResponse,
    DatabaseInfoResponse,
    DatabaseListResponse,
)

__all__ = [
    # Base
    "DateSchema",
    "EventSchema",
    # Person
    "PersonCreate",
    "PersonUpdate",
    "PersonResponse",
    # Family
    "FamilyCreate",
    "FamilyUpdate",
    "FamilyResponse",
    # Search
    "SearchQuery",
    "PaginationParams",
    "PaginatedResponse",
    # Statistics
    "PersonStatistics",
    "FamilyStatistics",
    "DatabaseStatistics",
    # Database
    "DatabaseCreateRequest",
    "DatabaseCreateResponse",
    "DatabaseListResponse",
    "DatabaseInfoResponse",
]
