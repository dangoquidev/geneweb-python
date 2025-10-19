"""
FastAPI dependencies for dependency injection.

Provides database connections, services, and authentication dependencies.
"""

from typing import Generator, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.database.pickle_driver import PickleDriver
from backend.database.repository import Repository
from backend.services.family_service import FamilyService
from backend.services.person_service import PersonService
from backend.services.search_service import SearchService

# Security scheme for JWT authentication
security = HTTPBearer(auto_error=False)


def get_database_path() -> str:
    """
    Get database path from configuration.

    Returns:
        Path to database file.

    Examples:
        >>> path = get_database_path()
        >>> print(path)
        data/showcase.pickle
    """
    # TODO: Get from app state or config
    return "data/showcase.pickle"


def get_repository() -> Generator[Repository, None, None]:
    """
    Dependency for getting Repository instance.

    Yields:
        Repository instance with active database connection.

    Examples:
        >>> @app.get("/persons")
        >>> async def get_persons(repo: Repository = Depends(get_repository)):
        >>>     return repo.get_all_persons()
    """
    db_path = get_database_path()
    driver = PickleDriver(db_path)
    repository = Repository(driver)

    try:
        yield repository
    finally:
        # Cleanup if needed (driver handles this)
        pass


def get_person_service(repository: Repository = Depends(get_repository)) -> PersonService:
    """
    Dependency for getting PersonService instance.

    Args:
        repository: Repository instance from dependency.

    Returns:
        PersonService instance.

    Examples:
        >>> @app.post("/persons")
        >>> async def create_person(
        >>>     data: PersonCreate,
        >>>     service: PersonService = Depends(get_person_service)
        >>> ):
        >>>     return service.create_person(**data.dict())
    """
    return PersonService(repository)


def get_family_service(repository: Repository = Depends(get_repository)) -> FamilyService:
    """
    Dependency for getting FamilyService instance.

    Args:
        repository: Repository instance from dependency.

    Returns:
        FamilyService instance.
    """
    return FamilyService(repository)


def get_search_service(repository: Repository = Depends(get_repository)) -> SearchService:
    """
    Dependency for getting SearchService instance.

    Args:
        repository: Repository instance from dependency.

    Returns:
        SearchService instance.
    """
    return SearchService(repository)


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> dict:
    """
    Dependency for authenticating requests (optional).

    Args:
        credentials: HTTP authorization credentials from header.

    Returns:
        User information if authenticated, or anonymous user.

    Raises:
        HTTPException: If authentication fails.

    Examples:
        >>> @app.get("/protected")
        >>> async def protected_route(user: dict = Depends(get_current_user)):
        >>>     return {"user": user["username"]}
    """
    # TODO: Implement actual JWT validation
    # For now, allow all requests (no auth)
    if credentials is None:
        # Anonymous access
        return {"username": "anonymous", "authenticated": False}

    # Validate JWT token here
    # For now, just accept any token
    return {"username": "authenticated_user", "authenticated": True}


def require_auth(user: dict = Depends(get_current_user)) -> dict:
    """
    Dependency that requires authentication.

    Args:
        user: User from get_current_user dependency.

    Returns:
        User information.

    Raises:
        HTTPException: If user is not authenticated.

    Examples:
        >>> @app.delete("/persons/{person_id}")
        >>> async def delete_person(
        >>>     person_id: str,
        >>>     user: dict = Depends(require_auth)
        >>> ):
        >>>     # Only authenticated users can delete
        >>>     pass
    """
    if not user.get("authenticated", False):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user
