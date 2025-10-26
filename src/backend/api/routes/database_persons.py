"""
Database-specific person API endpoints.

Provides person access scoped to a specific database.
"""

from typing import List

from fastapi import APIRouter, Depends, Path, Query

from backend.api.routes.persons import person_to_response
from backend.api.schemas import PersonResponse
from backend.database.pickle_driver import PickleDriver
from backend.services.database_service import DatabaseService

router = APIRouter()


def get_database_service() -> DatabaseService:
    """
    Dependency to get database service instance.

    Returns:
        DatabaseService instance configured with database directory.
    """
    import os

    # Get database directory from environment or use default
    database_dir = os.environ.get("GENEWEB_DATABASE_PATH", "data")
    # Remove filename if full path provided
    if database_dir.endswith(".pickle"):
        database_dir = os.path.dirname(database_dir)
    return DatabaseService(database_dir)


def get_database_driver(
    database_name: str,
    service: DatabaseService = Depends(get_database_service),
) -> PickleDriver:
    """
    Get driver for a specific database.

    Args:
        database_name: Name of the database.
        service: Database service instance.

    Returns:
        Loaded PickleDriver instance.

    Raises:
        HTTPException: 404 if database not found.
    """
    from fastapi import HTTPException

    from backend.database.repository import Repository

    if not service.database_exists(database_name):
        raise HTTPException(status_code=404, detail=f"Database '{database_name}' not found")

    db_path = service.get_database_path(database_name)
    driver = PickleDriver(db_path)
    driver.load()
    # Attach repository to driver for convenience
    driver.repository = Repository(driver)
    return driver


@router.get(
    "/databases/{database_name}/persons",
    response_model=List[PersonResponse],
    summary="List persons in database",
    description="Get all persons from a specific database with pagination.",
    tags=["Database Consultation"],
)
async def list_database_persons(
    database_name: str = Path(..., description="Database name"),
    skip: int = Query(0, ge=0, description="Number of persons to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of persons to return"),
    service: DatabaseService = Depends(get_database_service),
) -> List[PersonResponse]:
    """
    List all persons in a specific database with pagination.

    Args:
        database_name: Name of the database to query.
        skip: Number of persons to skip (offset).
        limit: Maximum number of persons to return.
        service: DatabaseService dependency.

    Returns:
        List of persons from the specified database.

    Raises:
        HTTP 404: If database not found.

    Examples:
        >>> GET /api/databases/ma_famille/persons?skip=0&limit=50
        [
            {
                "id": "P001",
                "first_name": "John",
                "surname": "Doe",
                ...
            }
        ]
    """
    driver = get_database_driver(database_name, service)

    all_persons_dict = driver.repository.get_all_persons()
    all_persons = list(all_persons_dict.values())
    paginated = all_persons[skip : skip + limit]

    return [person_to_response(p) for p in paginated]


@router.get(
    "/databases/{database_name}/persons/{person_id}",
    response_model=PersonResponse,
    summary="Get person from database",
    description="Get a specific person from a database by ID.",
    tags=["Database Consultation"],
)
async def get_database_person(
    database_name: str = Path(..., description="Database name"),
    person_id: str = Path(..., description="Person ID"),
    service: DatabaseService = Depends(get_database_service),
) -> PersonResponse:
    """
    Get a person by ID from a specific database.

    Args:
        database_name: Name of the database to query.
        person_id: Person ID.
        service: DatabaseService dependency.

    Returns:
        Person details.

    Raises:
        HTTP 404: If database or person not found.

    Examples:
        >>> GET /api/databases/ma_famille/persons/P001
        {
            "id": "P001",
            "first_name": "John",
            ...
        }
    """
    driver = get_database_driver(database_name, service)
    person = driver.repository.get_person(person_id)
    return person_to_response(person)


@router.get(
    "/databases/{database_name}/statistics",
    summary="Get database statistics",
    description="Get statistical information about a database.",
    tags=["Database Consultation"],
)
async def get_database_statistics(
    database_name: str = Path(..., description="Database name"),
    service: DatabaseService = Depends(get_database_service),
) -> dict:
    """
    Get statistics for a specific database.

    Args:
        database_name: Name of the database.
        service: DatabaseService dependency.

    Returns:
        Dictionary with database statistics.

    Raises:
        HTTP 404: If database not found.

    Examples:
        >>> GET /api/databases/ma_famille/statistics
        {
            "database_name": "ma_famille",
            "persons_count": 150,
            "families_count": 45,
            "oldest_birth_year": 1850,
            "newest_birth_year": 2020
        }
    """
    driver = get_database_driver(database_name, service)

    all_persons = driver.repository.get_all_persons()
    all_families = driver.repository.get_all_families()

    # Calculate some basic statistics
    birth_years = []
    for person in all_persons.values():
        if person.birth_date and person.birth_date.year:
            birth_years.append(person.birth_date.year)

    return {
        "database_name": database_name,
        "persons_count": len(all_persons),
        "families_count": len(all_families),
        "oldest_birth_year": min(birth_years) if birth_years else None,
        "newest_birth_year": max(birth_years) if birth_years else None,
    }


@router.get(
    "/databases/{database_name}/search",
    response_model=List[PersonResponse],
    summary="Search persons in database",
    description="Search for persons in a specific database by name.",
    tags=["Database Consultation"],
)
async def search_database_persons(
    database_name: str = Path(..., description="Database name"),
    q: str = Query(..., description="Search query (name)"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of results"),
    service: DatabaseService = Depends(get_database_service),
) -> List[PersonResponse]:
    """
    Search for persons in a specific database.

    Args:
        database_name: Name of the database to query.
        q: Search query string (searches in first name and surname).
        limit: Maximum number of results to return.
        service: DatabaseService dependency.

    Returns:
        List of matching persons.

    Raises:
        HTTP 404: If database not found.

    Examples:
        >>> GET /api/databases/ma_famille/search?q=Martin&limit=10
        [
            {
                "id": "P001",
                "first_name": "Martin",
                "surname": "Dupont",
                ...
            }
        ]
    """
    driver = get_database_driver(database_name, service)

    all_persons = driver.repository.get_all_persons()
    query_lower = q.lower()

    # Simple search in first_name and surname
    results = []
    for person in all_persons.values():
        first_name = (person.first_name or "").lower()
        surname = (person.surname or "").lower()
        public_name = (person.public_name or "").lower()

        if (
            query_lower in first_name
            or query_lower in surname
            or query_lower in public_name
            or any(query_lower in alias.lower() for alias in (person.aliases or []))
        ):
            results.append(person_to_response(person))

            if len(results) >= limit:
                break

    return results
