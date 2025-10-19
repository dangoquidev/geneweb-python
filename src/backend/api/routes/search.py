"""
Search and genealogy API endpoints.

Provides advanced search, filtering, pagination, and genealogy tree traversal.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from backend.api.dependencies import get_search_service
from backend.api.routes.persons import person_to_response
from backend.api.schemas import DatabaseStatistics, PersonResponse
from backend.core.models import Sex
from backend.services.search_service import SearchService

router = APIRouter()


# ============================================================================
# Search Request/Response Models
# ============================================================================


class SearchRequest(BaseModel):
    """Search request parameters."""

    query: str
    search_in: List[str] = ["first_name", "surname"]
    fuzzy: bool = False
    threshold: float = 0.8
    # Filters
    birth_year_min: Optional[int] = None
    birth_year_max: Optional[int] = None
    sex: Optional[Sex] = None
    places: Optional[List[str]] = None
    is_alive: Optional[bool] = None
    # Pagination & sorting
    page: int = 1
    page_size: int = 50
    sort_by: str = "surname"
    sort_order: str = "asc"


class RelationshipPath(BaseModel):
    """Relationship path between two persons."""

    person1_id: str
    person2_id: str
    path: List[str]
    relationship_degree: int


# ============================================================================
# Search Endpoints
# ============================================================================


@router.post("/persons", response_model=List[PersonResponse])
async def search_persons(
    search_req: SearchRequest,
    service: SearchService = Depends(get_search_service),
) -> List[PersonResponse]:
    """
    Search for persons with advanced filtering and pagination.

    Args:
        search_req: Search request with query, filters, and pagination.
        service: SearchService dependency.

    Returns:
        List of matching persons.

    Examples:
        >>> POST /api/search/persons
        >>> {
        >>>     "query": "John",
        >>>     "search_in": ["first_name", "surname"],
        >>>     "fuzzy": true,
        >>>     "birth_year_min": 1980,
        >>>     "birth_year_max": 2000,
        >>>     "page": 1,
        >>>     "page_size": 20
        >>> }
    """
    # Execute text search via repository
    results = service.repository.search_persons(
        query=search_req.query,
        search_in=search_req.search_in,
        fuzzy=search_req.fuzzy,
        threshold=search_req.threshold,
    )

    # Apply filters manually
    filtered_results = []
    for person in results:
        # Birth year filter
        if search_req.birth_year_min and person.birth_date and person.birth_date.year < search_req.birth_year_min:
            continue
        if search_req.birth_year_max and person.birth_date and person.birth_date.year > search_req.birth_year_max:
            continue
        # Sex filter
        if search_req.sex and person.sex != search_req.sex:
            continue
        # Is alive filter
        if search_req.is_alive is not None:
            is_alive = person.death_date is None
            if search_req.is_alive != is_alive:
                continue
        filtered_results.append(person)

    # Sort
    if search_req.sort_by == "first_name":
        filtered_results.sort(key=lambda p: p.first_name.lower(), reverse=(search_req.sort_order == "desc"))
    elif search_req.sort_by == "birth_date":
        filtered_results.sort(
            key=lambda p: (p.birth_date.year if p.birth_date else 9999), reverse=(search_req.sort_order == "desc")
        )
    else:  # surname
        filtered_results.sort(key=lambda p: p.surname.lower(), reverse=(search_req.sort_order == "desc"))

    # Paginate
    start = (search_req.page - 1) * search_req.page_size
    end = start + search_req.page_size
    paginated = filtered_results[start:end]

    return [person_to_response(p) for p in paginated]


@router.get("/persons", response_model=List[PersonResponse])
async def search_persons_get(
    query: str = Query(..., description="Search query", min_length=1),
    search_in: str = Query("first_name,surname", description="Comma-separated fields"),
    fuzzy: bool = Query(False, description="Enable fuzzy matching"),
    threshold: float = Query(0.8, description="Fuzzy match threshold", ge=0.0, le=1.0),
    birth_year_min: Optional[int] = Query(None, description="Minimum birth year"),
    birth_year_max: Optional[int] = Query(None, description="Maximum birth year"),
    sex: Optional[Sex] = Query(None, description="Filter by sex"),
    page: int = Query(1, description="Page number", ge=1),
    page_size: int = Query(50, description="Items per page", ge=1, le=1000),
    sort_by: str = Query("surname", description="Sort field"),
    sort_order: str = Query("asc", description="Sort order (asc/desc)"),
    service: SearchService = Depends(get_search_service),
) -> List[PersonResponse]:
    """
    Search for persons using GET request (alternative to POST).

    Args:
        query: Search query string.
        search_in: Comma-separated list of fields to search.
        fuzzy: Enable fuzzy matching.
        threshold: Fuzzy match threshold.
        birth_year_min: Minimum birth year filter.
        birth_year_max: Maximum birth year filter.
        sex: Sex filter.
        page: Page number.
        page_size: Items per page.
        sort_by: Field to sort by.
        sort_order: Sort order (asc/desc).
        service: SearchService dependency.

    Returns:
        List of matching persons.

    Examples:
        >>> GET /api/search/persons?query=John&fuzzy=true&page=1
        [
            {
                "id": "P001",
                "first_name": "John",
                ...
            }
        ]
    """
    # Parse search_in
    search_in_list = [field.strip() for field in search_in.split(",")]

    # Execute text search via repository
    results = service.repository.search_persons(
        query=query,
        search_in=search_in_list,
        fuzzy=fuzzy,
        threshold=threshold,
    )

    # Apply additional filters if provided
    if birth_year_min or birth_year_max or sex:
        filtered_results = []
        for person in results:
            # Birth year filter
            if birth_year_min and person.birth_date and person.birth_date.year < birth_year_min:
                continue
            if birth_year_max and person.birth_date and person.birth_date.year > birth_year_max:
                continue
            # Sex filter
            if sex and person.sex != sex:
                continue
            filtered_results.append(person)
        results = filtered_results

    # Sort
    if sort_by == "first_name":
        results.sort(key=lambda p: p.first_name.lower(), reverse=(sort_order == "desc"))
    elif sort_by == "birth_date":
        results.sort(key=lambda p: (p.birth_date.year if p.birth_date else 9999), reverse=(sort_order == "desc"))
    else:  # surname
        results.sort(key=lambda p: p.surname.lower(), reverse=(sort_order == "desc"))

    # Paginate
    start = (page - 1) * page_size
    end = start + page_size
    results = results[start:end]

    return [person_to_response(p) for p in results]


# ============================================================================
# Genealogy Endpoints
# ============================================================================


@router.get("/ancestors/{person_id}", response_model=List[PersonResponse])
async def get_ancestors(
    person_id: str,
    max_generations: int = Query(5, description="Maximum generations", ge=1, le=20),
    service: SearchService = Depends(get_search_service),
) -> List[PersonResponse]:
    """
    Get ancestors of a person.

    Args:
        person_id: Person ID.
        max_generations: Maximum number of generations to traverse.
        service: SearchService dependency.

    Returns:
        List of ancestors.

    Raises:
        HTTP 404: If person not found.

    Examples:
        >>> GET /api/search/ancestors/P001?max_generations=3
        [
            {"id": "P010", "first_name": "Grandfather", ...},
            {"id": "P020", "first_name": "Great-Grandfather", ...}
        ]
    """
    ancestors = service.get_ancestors(person_id, max_generations=max_generations)
    return [person_to_response(p) for p in ancestors]


@router.get("/descendants/{person_id}", response_model=List[PersonResponse])
async def get_descendants(
    person_id: str,
    max_generations: int = Query(5, description="Maximum generations", ge=1, le=20),
    service: SearchService = Depends(get_search_service),
) -> List[PersonResponse]:
    """
    Get descendants of a person.

    Args:
        person_id: Person ID.
        max_generations: Maximum number of generations to traverse.
        service: SearchService dependency.

    Returns:
        List of descendants.

    Raises:
        HTTP 404: If person not found.

    Examples:
        >>> GET /api/search/descendants/P001?max_generations=3
        [
            {"id": "P030", "first_name": "Child", ...},
            {"id": "P040", "first_name": "Grandchild", ...}
        ]
    """
    descendants = service.get_descendants(person_id, max_generations=max_generations)
    return [person_to_response(p) for p in descendants]


@router.get("/relatives/{person_id}", response_model=List[PersonResponse])
async def get_all_relatives(
    person_id: str,
    service: SearchService = Depends(get_search_service),
) -> List[PersonResponse]:
    """
    Get all relatives of a person (parents, siblings, spouses, children).

    Args:
        person_id: Person ID.
        service: SearchService dependency.

    Returns:
        List of all relatives.

    Raises:
        HTTP 404: If person not found.

    Examples:
        >>> GET /api/search/relatives/P001
        [
            {"id": "P002", "first_name": "Father", ...},
            {"id": "P003", "first_name": "Mother", ...},
            {"id": "P004", "first_name": "Sibling", ...}
        ]
    """
    relatives = service.get_all_relatives(person_id)
    return [person_to_response(p) for p in relatives]


@router.get("/relationship/{person1_id}/{person2_id}", response_model=RelationshipPath)
async def find_relationship_path(
    person1_id: str,
    person2_id: str,
    max_depth: int = Query(10, description="Maximum search depth", ge=1, le=20),
    service: SearchService = Depends(get_search_service),
) -> RelationshipPath:
    """
    Find relationship path between two persons.

    Args:
        person1_id: First person ID.
        person2_id: Second person ID.
        max_depth: Maximum search depth.
        service: SearchService dependency.

    Returns:
        Relationship path information.

    Raises:
        HTTP 404: If either person not found or no relationship found.

    Examples:
        >>> GET /api/search/relationship/P001/P010?max_depth=5
        {
            "person1_id": "P001",
            "person2_id": "P010",
            "path": ["P001", "P002", "P010"],
            "relationship_degree": 2
        }
    """
    path = service.find_relationship_path(person1_id, person2_id, max_depth=max_depth)

    if not path:
        from fastapi import HTTPException, status

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No relationship found between {person1_id} and {person2_id}",
        )

    # Convert Person objects to IDs
    path_ids = [p.id for p in path]

    return RelationshipPath(
        person1_id=person1_id,
        person2_id=person2_id,
        path=path_ids,
        relationship_degree=len(path_ids) - 1,
    )


# ============================================================================
# Statistics Endpoints
# ============================================================================


@router.get("/statistics", response_model=DatabaseStatistics)
async def get_database_statistics(
    service: SearchService = Depends(get_search_service),
) -> DatabaseStatistics:
    """
    Get database-wide statistics.

    Args:
        service: SearchService dependency.

    Returns:
        Database statistics.

    Examples:
        >>> GET /api/search/statistics
        {
            "total_persons": 1500,
            "total_families": 750,
            "avg_children_per_family": 2.3,
            "oldest_person": {...},
            "youngest_person": {...}
        }
    """
    stats = service.get_statistics()
    return DatabaseStatistics(**stats)
