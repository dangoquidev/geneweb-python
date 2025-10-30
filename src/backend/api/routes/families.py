"""
Family API endpoints.

Provides CRUD operations and family-related functionality.
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Path, Query, status

from backend.api.dependencies import get_family_service, require_auth
from backend.api.schemas import FamilyCreate, FamilyResponse, FamilyStatistics, FamilyUpdate
from backend.core.models import Date, Family
from backend.services.family_service import FamilyService

router = APIRouter()


# ============================================================================
# Helper functions
# ============================================================================


def family_to_response(family: Family) -> FamilyResponse:
    """
    Convert Family model to FamilyResponse schema.

    Args:
        family: Family model instance.

    Returns:
        FamilyResponse schema.
    """
    from backend.api.schemas.common import DateSchema

    def date_to_schema(date: Optional[Date]) -> Optional[DateSchema]:
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
        marital_status=family.marital_status,
        marriage_date=date_to_schema(family.marriage_date),
        marriage_place=family.marriage_place,
        divorce_date=date_to_schema(family.divorce_date),
        divorce_type=family.divorce_type,
    )


# ============================================================================
# CRUD Endpoints
# ============================================================================


@router.get("", response_model=List[FamilyResponse])
async def list_families(
    skip: int = Query(0, ge=0, description="Number of families to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of families to return"),
    service: FamilyService = Depends(get_family_service),
) -> List[FamilyResponse]:
    """
    List all families with pagination.

    Args:
        skip: Number of families to skip (offset).
        limit: Maximum number of families to return.
        service: FamilyService dependency.

    Returns:
        List of families.

    Examples:
        >>> GET /api/families?skip=0&limit=50
        [
            {
                "id": "F001",
                "father_id": "P001",
                "mother_id": "P002",
                ...
            }
        ]
    """
    # Get all families from repository
    all_families_dict = service.repository.get_all_families()
    all_families = list(all_families_dict.values())
    paginated = all_families[skip : skip + limit]
    return [family_to_response(f) for f in paginated]


@router.post("", response_model=FamilyResponse, status_code=status.HTTP_201_CREATED)
async def create_family(
    family_data: FamilyCreate,
    service: FamilyService = Depends(get_family_service),
    user: dict = Depends(require_auth),
) -> FamilyResponse:
    """
    Create a new family.

    Args:
        family_data: Family creation data.
        service: FamilyService dependency.
        user: Authenticated user (required).

    Returns:
        Created family.

    Raises:
        ValidationError: If data is invalid.
        HTTP 401: If not authenticated.

    Examples:
        >>> POST /api/families
        >>> {
        >>>     "father_id": "P001",
        >>>     "mother_id": "P002",
        >>>     "marital_status": "MARRIED",
        >>>     "marriage_date": {"year": 2010, "month": 6, "day": 15}
        >>> }
    """
    # Convert schema to Date objects if provided
    marriage_date = None
    if family_data.marriage_date:
        marriage_date = Date(
            year=family_data.marriage_date.year,
            month=family_data.marriage_date.month,
            day=family_data.marriage_date.day,
            calendar=family_data.marriage_date.calendar,
        )

    divorce_date = None
    if family_data.divorce_date:
        divorce_date = Date(
            year=family_data.divorce_date.year,
            month=family_data.divorce_date.month,
            day=family_data.divorce_date.day,
            calendar=family_data.divorce_date.calendar,
        )

    # Create family
    family = service.create_family(
        father_id=family_data.father_id,
        mother_id=family_data.mother_id,
        children_ids=family_data.children_ids,
        marital_status=family_data.marital_status,
        marriage_date=marriage_date,
        marriage_place=family_data.marriage_place,
        divorce_date=divorce_date,
        divorce_type=family_data.divorce_type,
    )

    return family_to_response(family)


@router.get("/{family_id}", response_model=FamilyResponse)
async def get_family(
    family_id: str = Path(..., description="Family ID"),
    service: FamilyService = Depends(get_family_service),
) -> FamilyResponse:
    """
    Get a family by ID.

    Args:
        family_id: Family ID.
        service: FamilyService dependency.

    Returns:
        Family details.

    Raises:
        HTTP 404: If family not found.

    Examples:
        >>> GET /api/families/F001
        {
            "id": "F001",
            "father_id": "P001",
            ...
        }
    """
    family = service.repository.get_family(family_id)
    return family_to_response(family)


@router.put("/{family_id}", response_model=FamilyResponse)
async def update_family(
    family_id: str = Path(..., description="Family ID"),
    family_data: FamilyUpdate = ...,
    service: FamilyService = Depends(get_family_service),
    user: dict = Depends(require_auth),
) -> FamilyResponse:
    """
    Update a family.

    Args:
        family_id: Family ID.
        family_data: Updated family data.
        service: FamilyService dependency.
        user: Authenticated user (required).

    Returns:
        Updated family.

    Raises:
        HTTP 404: If family not found.
        HTTP 401: If not authenticated.

    Examples:
        >>> PUT /api/families/F001
        >>> {
        >>>     "marital_status": "DIVORCED",
        >>>     "divorce_date": {"year": 2020, "month": 12, "day": 31}
        >>> }
    """
    # Build kwargs with only provided fields
    kwargs: Dict[str, Any] = {}

    if family_data.father_id is not None:
        kwargs["father_id"] = family_data.father_id
    if family_data.mother_id is not None:
        kwargs["mother_id"] = family_data.mother_id
    if family_data.marital_status is not None:
        kwargs["marital_status"] = family_data.marital_status
    if family_data.marriage_date is not None:
        kwargs["marriage_date"] = Date(
            year=family_data.marriage_date.year,
            month=family_data.marriage_date.month,
            day=family_data.marriage_date.day,
            calendar=family_data.marriage_date.calendar,
        )
    if family_data.marriage_place is not None:
        kwargs["marriage_place"] = family_data.marriage_place
    if family_data.divorce_date is not None:
        kwargs["divorce_date"] = Date(
            year=family_data.divorce_date.year,
            month=family_data.divorce_date.month,
            day=family_data.divorce_date.day,
            calendar=family_data.divorce_date.calendar,
        )
    if family_data.divorce_type is not None:
        kwargs["divorce_type"] = family_data.divorce_type

    family = service.update_family(family_id, **kwargs)
    return family_to_response(family)


@router.delete("/{family_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_family(
    family_id: str = Path(..., description="Family ID"),
    update_members: bool = Query(True, description="Update family members' relationships"),
    service: FamilyService = Depends(get_family_service),
    user: dict = Depends(require_auth),
) -> None:
    """
    Delete a family.

    Args:
        family_id: Family ID.
        update_members: Whether to update members' relationships.
        service: FamilyService dependency.
        user: Authenticated user (required).

    Raises:
        HTTP 404: If family not found.
        HTTP 401: If not authenticated.

    Examples:
        >>> DELETE /api/families/F001?update_members=true
        >>> Response: 204 No Content
    """
    service.delete_family(family_id, update_members=update_members)


# ============================================================================
# Children Management Endpoints
# ============================================================================


@router.post("/{family_id}/children/{child_id}", response_model=FamilyResponse)
async def add_child_to_family(
    family_id: str = Path(..., description="Family ID"),
    child_id: str = Path(..., description="Child person ID"),
    service: FamilyService = Depends(get_family_service),
    user: dict = Depends(require_auth),
) -> FamilyResponse:
    """
    Add a child to a family.

    Args:
        family_id: Family ID.
        child_id: Child's person ID.
        service: FamilyService dependency.
        user: Authenticated user (required).

    Returns:
        Updated family.

    Raises:
        HTTP 404: If family or child not found.
        HTTP 401: If not authenticated.

    Examples:
        >>> POST /api/families/F001/children/P003
        {
            "id": "F001",
            "children_ids": ["P003"],
            ...
        }
    """
    family = service.add_child(family_id, child_id)
    return family_to_response(family)


@router.delete("/{family_id}/children/{child_id}", response_model=FamilyResponse)
async def remove_child_from_family(
    family_id: str = Path(..., description="Family ID"),
    child_id: str = Path(..., description="Child person ID"),
    service: FamilyService = Depends(get_family_service),
    user: dict = Depends(require_auth),
) -> FamilyResponse:
    """
    Remove a child from a family.

    Args:
        family_id: Family ID.
        child_id: Child's person ID.
        service: FamilyService dependency.
        user: Authenticated user (required).

    Returns:
        Updated family.

    Raises:
        HTTP 404: If family or child not found.
        HTTP 401: If not authenticated.

    Examples:
        >>> DELETE /api/families/F001/children/P003
        {
            "id": "F001",
            "children_ids": [],
            ...
        }
    """
    family = service.remove_child(family_id, child_id)
    return family_to_response(family)


# ============================================================================
# Statistics Endpoint
# ============================================================================


@router.get("/{family_id}/statistics", response_model=FamilyStatistics)
async def get_family_statistics(
    family_id: str = Path(..., description="Family ID"),
    service: FamilyService = Depends(get_family_service),
) -> FamilyStatistics:
    """
    Get statistics for a family.

    Args:
        family_id: Family ID.
        service: FamilyService dependency.

    Returns:
        Family statistics.

    Raises:
        HTTP 404: If family not found.

    Examples:
        >>> GET /api/families/F001/statistics
        {
            "family_id": "F001",
            "father_name": "John Doe",
            "mother_name": "Jane Smith",
            "children_count": 3,
            "is_married": true,
            "is_divorced": false,
            "marital_status": "MARRIED"
        }
    """
    stats = service.get_family_statistics(family_id)
    return FamilyStatistics(**stats)
