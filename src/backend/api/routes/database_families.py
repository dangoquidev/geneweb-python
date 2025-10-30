"""
Database-specific family API endpoints.

Provides family access scoped to a specific database.
"""

from typing import List

from fastapi import APIRouter, Depends, Path, Query

from backend.api.schemas import FamilyResponse
from backend.core.models import Family
from backend.services.database_service import DatabaseService

from .database_persons import get_database_driver, get_database_service

router = APIRouter()


def family_to_response(family: Family) -> FamilyResponse:
    """
    Convert Family model to FamilyResponse schema.

    Args:
        family: Family model instance.

    Returns:
        FamilyResponse schema.
    """
    from backend.api.schemas.common import DateSchema

    def date_to_schema(date):
        if date is None:
            return None
        return DateSchema(
            year=date.year,
            month=date.month,
            day=date.day,
            calendar=date.calendar,
        )

    return FamilyResponse(
        id=family.id,
        father_id=family.father_id,
        mother_id=family.mother_id,
        children_ids=family.children_ids,
        marriage_date=date_to_schema(family.marriage_date),
        marriage_place=family.marriage_place,
        divorce_date=date_to_schema(family.divorce_date),
        notes=family.notes,
    )


@router.get(
    "/databases/{database_name}/families",
    response_model=List[FamilyResponse],
    summary="List families in database",
    description="Get all families from a specific database with pagination.",
    tags=["Database Consultation"],
)
async def list_database_families(
    database_name: str = Path(..., description="Database name"),
    skip: int = Query(0, ge=0, description="Number of families to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of families to return"),
    service: DatabaseService = Depends(get_database_service),
) -> List[FamilyResponse]:
    """
    List all families in a specific database with pagination.

    Args:
        database_name: Name of the database to query.
        skip: Number of families to skip (offset).
        limit: Maximum number of families to return.
        service: DatabaseService dependency.

    Returns:
        List of families from the specified database.

    Raises:
        HTTP 404: If database not found.

    Examples:
        >>> GET /api/databases/ma_famille/families?skip=0&limit=50
        [
            {
                "id": "F001",
                "father_id": "P001",
                "mother_id": "P002",
                ...
            }
        ]
    """
    driver = get_database_driver(database_name, service)

    all_families_dict = driver.repository.get_all_families()
    all_families = list(all_families_dict.values())
    paginated = all_families[skip : skip + limit]

    return [family_to_response(f) for f in paginated]


@router.get(
    "/databases/{database_name}/families/{family_id}",
    response_model=FamilyResponse,
    summary="Get family from database",
    description="Get a specific family from a database by ID.",
    tags=["Database Consultation"],
)
async def get_database_family(
    database_name: str = Path(..., description="Database name"),
    family_id: str = Path(..., description="Family ID"),
    service: DatabaseService = Depends(get_database_service),
) -> FamilyResponse:
    """
    Get a family by ID from a specific database.

    Args:
        database_name: Name of the database to query.
        family_id: Family ID.
        service: DatabaseService dependency.

    Returns:
        Family details.

    Raises:
        HTTP 404: If database or family not found.

    Examples:
        >>> GET /api/databases/ma_famille/families/F001
        {
            "id": "F001",
            "father_id": "P001",
            "mother_id": "P002",
            ...
        }
    """
    driver = get_database_driver(database_name, service)
    family = driver.repository.get_family(family_id)
    return family_to_response(family)
