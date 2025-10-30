"""
Pydantic schemas for API request/response models.

These schemas provide validation, serialization, and documentation for the API.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from backend.core.models import AccessLevel, EventType, MaritalStatus, Sex

# ============================================================================
# Base Schemas
# ============================================================================


class DateSchema(BaseModel):
    """Schema for dates with optional precision."""

    year: Optional[int] = Field(None, description="Year", ge=-4000, le=3000)
    month: Optional[int] = Field(None, description="Month (1-12)", ge=1, le=12)
    day: Optional[int] = Field(None, description="Day (1-31)", ge=1, le=31)
    calendar: str = Field("Gregorian", description="Calendar system")

    model_config = ConfigDict(
        json_schema_extra={"example": {"year": 1990, "month": 5, "day": 15, "calendar": "Gregorian"}}
    )


class EventSchema(BaseModel):
    """Schema for life events."""

    event_type: EventType = Field(..., description="Type of event")
    date: Optional[DateSchema] = Field(None, description="Event date")
    place: Optional[str] = Field(None, description="Event place", max_length=200)
    note: Optional[str] = Field(None, description="Additional notes", max_length=1000)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "event_type": "BIRTH",
                "date": {"year": 1990, "month": 5, "day": 15},
                "place": "Paris, France",
                "note": "Born at home",
            }
        }
    )


# ============================================================================
# Person Schemas
# ============================================================================


class PersonCreate(BaseModel):
    """Schema for creating a new person."""

    first_name: str = Field(..., description="First name", min_length=1, max_length=100)
    surname: str = Field(..., description="Surname/family name", min_length=1, max_length=100)
    sex: Sex = Field(..., description="Biological sex")
    birth_date: Optional[DateSchema] = Field(None, description="Birth date")
    birth_place: Optional[str] = Field(None, description="Birth place", max_length=200)
    death_date: Optional[DateSchema] = Field(None, description="Death date")
    death_place: Optional[str] = Field(None, description="Death place", max_length=200)
    occupation: Optional[str] = Field(None, description="Occupation", max_length=200)
    public_name: Optional[str] = Field(None, description="Public/display name", max_length=100)
    aliases: List[str] = Field(default_factory=list, description="Alternative names")
    titles: List[str] = Field(default_factory=list, description="Titles held")
    access_level: AccessLevel = Field(AccessLevel.PUBLIC, description="Privacy level")

    @field_validator("first_name", "surname")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate names are not empty after stripping."""
        if not v.strip():
            raise ValueError("Name cannot be empty or whitespace only")
        return v.strip()

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "first_name": "John",
                "surname": "Doe",
                "sex": "M",
                "birth_date": {"year": 1990, "month": 5, "day": 15},
                "birth_place": "Paris, France",
                "occupation": "Software Engineer",
            }
        }
    )


class PersonUpdate(BaseModel):
    """Schema for updating an existing person (all fields optional)."""

    first_name: Optional[str] = Field(None, description="First name", min_length=1, max_length=100)
    surname: Optional[str] = Field(None, description="Surname", min_length=1, max_length=100)
    sex: Optional[Sex] = Field(None, description="Biological sex")
    birth_date: Optional[DateSchema] = Field(None, description="Birth date")
    birth_place: Optional[str] = Field(None, description="Birth place", max_length=200)
    death_date: Optional[DateSchema] = Field(None, description="Death date")
    death_place: Optional[str] = Field(None, description="Death place", max_length=200)
    occupation: Optional[str] = Field(None, description="Occupation", max_length=200)
    public_name: Optional[str] = Field(None, description="Public name", max_length=100)
    access_level: Optional[AccessLevel] = Field(None, description="Privacy level")


class PersonResponse(BaseModel):
    """Schema for person in API responses."""

    id: str = Field(..., description="Unique person ID")
    first_name: str = Field(..., description="First name")
    surname: str = Field(..., description="Surname")
    sex: Sex = Field(..., description="Biological sex")
    birth_date: Optional[DateSchema] = Field(None, description="Birth date")
    birth_place: Optional[str] = Field(None, description="Birth place")
    death_date: Optional[DateSchema] = Field(None, description="Death date")
    death_place: Optional[str] = Field(None, description="Death place")
    occupation: Optional[str] = Field(None, description="Occupation")
    public_name: Optional[str] = Field(None, description="Public name")
    aliases: List[str] = Field(default_factory=list, description="Alternative names")
    titles: List[str] = Field(default_factory=list, description="Titles")
    family_id: Optional[str] = Field(None, description="Parent family ID")
    family_ids: List[str] = Field(default_factory=list, description="Spouse family IDs")
    events: List[EventSchema] = Field(default_factory=list, description="Life events")
    access_level: AccessLevel = Field(..., description="Privacy level")

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Family Schemas
# ============================================================================


class FamilyCreate(BaseModel):
    """Schema for creating a new family."""

    father_id: Optional[str] = Field(None, description="Father's person ID")
    mother_id: Optional[str] = Field(None, description="Mother's person ID")
    children_ids: List[str] = Field(default_factory=list, description="Children's person IDs")
    marital_status: MaritalStatus = Field(MaritalStatus.UNKNOWN, description="Marital status")
    marriage_date: Optional[DateSchema] = Field(None, description="Marriage date")
    marriage_place: Optional[str] = Field(None, description="Marriage place", max_length=200)
    divorce_date: Optional[DateSchema] = Field(None, description="Divorce date")
    divorce_type: Optional[str] = Field(None, description="Divorce type", max_length=50)

    @field_validator("children_ids")
    @classmethod
    def validate_unique_children(cls, v: List[str]) -> List[str]:
        """Ensure children IDs are unique."""
        if len(v) != len(set(v)):
            raise ValueError("Duplicate children IDs not allowed")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "father_id": "P001",
                "mother_id": "P002",
                "children_ids": ["P003", "P004"],
                "marital_status": "MARRIED",
                "marriage_date": {"year": 2010, "month": 6, "day": 15},
                "marriage_place": "London, UK",
            }
        }
    )


class FamilyUpdate(BaseModel):
    """Schema for updating an existing family (all fields optional)."""

    father_id: Optional[str] = Field(None, description="Father's person ID")
    mother_id: Optional[str] = Field(None, description="Mother's person ID")
    marital_status: Optional[MaritalStatus] = Field(None, description="Marital status")
    marriage_date: Optional[DateSchema] = Field(None, description="Marriage date")
    marriage_place: Optional[str] = Field(None, description="Marriage place", max_length=200)
    divorce_date: Optional[DateSchema] = Field(None, description="Divorce date")
    divorce_type: Optional[str] = Field(None, description="Divorce type", max_length=50)


class FamilyResponse(BaseModel):
    """Schema for family in API responses."""

    id: str = Field(..., description="Unique family ID")
    father_id: Optional[str] = Field(None, description="Father's ID")
    mother_id: Optional[str] = Field(None, description="Mother's ID")
    children_ids: List[str] = Field(default_factory=list, description="Children IDs")
    marital_status: MaritalStatus = Field(..., description="Marital status")
    marriage_date: Optional[DateSchema] = Field(None, description="Marriage date")
    marriage_place: Optional[str] = Field(None, description="Marriage place")
    divorce_date: Optional[DateSchema] = Field(None, description="Divorce date")
    divorce_type: Optional[str] = Field(None, description="Divorce type")

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Search & Pagination Schemas
# ============================================================================


class SearchQuery(BaseModel):
    """Schema for search queries."""

    query: str = Field(..., description="Search query string", min_length=1, max_length=200)
    search_in: List[str] = Field(default_factory=lambda: ["first_name", "surname"], description="Fields to search in")
    fuzzy: bool = Field(False, description="Enable fuzzy matching")
    threshold: float = Field(0.8, description="Fuzzy match threshold", ge=0.0, le=1.0)


class PaginationParams(BaseModel):
    """Schema for pagination parameters."""

    page: int = Field(1, description="Page number (1-indexed)", ge=1)
    page_size: int = Field(50, description="Items per page", ge=1, le=1000)


class PaginatedResponse(BaseModel):
    """Schema for paginated API responses."""

    items: List[Any] = Field(..., description="List of items for current page")
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Items per page")
    total_pages: int = Field(..., description="Total number of pages")


# ============================================================================
# Statistics Schemas
# ============================================================================


class PersonStatistics(BaseModel):
    """Schema for person statistics."""

    person_id: str
    full_name: str
    age: Optional[int]
    events_count: int
    family_memberships: int


class FamilyStatistics(BaseModel):
    """Schema for family statistics."""

    family_id: str
    father_name: Optional[str]
    mother_name: Optional[str]
    children_count: int
    is_married: bool
    is_divorced: bool
    marital_status: str


class DatabaseStatistics(BaseModel):
    """Schema for database-wide statistics."""

    total_persons: int
    total_families: int
    male_count: Optional[int] = None
    female_count: Optional[int] = None
    unknown_sex_count: Optional[int] = None
    living_count: Optional[int] = None
    deceased_count: Optional[int] = None
    with_birth_date: Optional[int] = None
    with_death_date: Optional[int] = None
    avg_children_per_family: Optional[float] = None
    oldest_person: Optional[Dict[str, Any]] = None
    youngest_person: Optional[Dict[str, Any]] = None
