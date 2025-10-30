"""
Database API routes.

Endpoints for database management (create, list, info, delete).
"""

import logging
import os

from fastapi import APIRouter, Depends, HTTPException, status

from backend.api.schemas import (
    DatabaseCreateRequest,
    DatabaseCreateResponse,
    DatabaseInfoResponse,
    DatabaseListResponse,
)
from backend.core.exceptions import DatabaseError, ValidationError
from backend.database.pickle_driver import PickleDriver
from backend.services.database_service import DatabaseService

router = APIRouter()
logger = logging.getLogger(__name__)


def get_database_service() -> DatabaseService:
    """
    Dependency to get database service instance.

    Returns:
        DatabaseService instance configured with database directory.
    """
    # Get database directory from environment or use default
    database_dir = os.environ.get("GENEWEB_DATABASE_PATH", "data")
    # Remove filename if full path provided
    if database_dir.endswith(".pickle"):
        database_dir = os.path.dirname(database_dir)
    return DatabaseService(database_dir)


@router.get(
    "/databases",
    response_model=DatabaseListResponse,
    summary="List all databases",
    description="Get a list of all available databases in the system.",
    tags=["Database Management"],
)
async def list_databases(
    service: DatabaseService = Depends(get_database_service),
) -> DatabaseListResponse:
    """
    List all available databases.

    Returns:
        DatabaseListResponse with list of database names and count.

    Raises:
        HTTPException: 500 if database directory cannot be read.
    """
    try:
        databases = service.list_databases()
        return DatabaseListResponse(databases=databases, count=len(databases))
    except DatabaseError as e:
        logger.error(f"Error listing databases: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/databases",
    response_model=DatabaseCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new database",
    description="Create a new empty database with the specified name and type.",
    tags=["Database Management"],
)
async def create_database(
    request: DatabaseCreateRequest,
    service: DatabaseService = Depends(get_database_service),
    # Uncomment when authentication is implemented:
    # _auth = Depends(require_auth),
) -> DatabaseCreateResponse:
    """
    Create a new database.

    Args:
        request: Database creation request with name and type.
        service: Database service instance.

    Returns:
        DatabaseCreateResponse with success status and database info.

    Raises:
        HTTPException: 400 if validation fails or database exists.
        HTTPException: 500 if creation fails.
    """
    try:
        success, db_path, error = service.create_database(name=request.name, db_type=request.db_type)

        if not success:
            raise HTTPException(status_code=500, detail=error)

        return DatabaseCreateResponse(
            success=True,
            database_name=request.name,
            path=db_path,
            message=f"Database '{request.name}' created successfully",
        )

    except ValidationError as e:
        logger.warning(f"Validation error creating database: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except DatabaseError as e:
        logger.error(f"Database error creating database: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error creating database: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/databases/{database_name}",
    response_model=DatabaseInfoResponse,
    summary="Get database info",
    description="Get detailed information about a specific database.",
    tags=["Database Management"],
)
async def get_database_info(
    database_name: str,
    service: DatabaseService = Depends(get_database_service),
) -> DatabaseInfoResponse:
    """
    Get database information.

    Args:
        database_name: Name of the database.
        service: Database service instance.

    Returns:
        DatabaseInfoResponse with database details.

    Raises:
        HTTPException: 404 if database not found.
        HTTPException: 500 if database cannot be opened.
    """
    try:
        # Check if database exists
        if not service.database_exists(database_name):
            raise HTTPException(status_code=404, detail=f"Database '{database_name}' not found")

        # Load database to get info
        db_path = service.get_database_path(database_name)
        driver = PickleDriver(db_path)
        driver.load()

        info = driver.get_info()

        return DatabaseInfoResponse(
            base_name=database_name,
            persons=info["persons_count"],
            families=info["families_count"],
            path=db_path,
            version=info.get("version", "1.0"),
            created_date=info.get("created_date", ""),
            modified_date=info.get("modified_date", ""),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting database info for '{database_name}': {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete(
    "/databases/{database_name}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete database",
    description="Permanently delete a database. This action cannot be undone.",
    tags=["Database Management"],
)
async def delete_database(
    database_name: str,
    service: DatabaseService = Depends(get_database_service),
    # Uncomment when authentication is implemented:
    # _auth = Depends(require_auth),
) -> None:
    """
    Delete a database.

    Args:
        database_name: Name of the database to delete.
        service: Database service instance.

    Raises:
        HTTPException: 404 if database not found.
        HTTPException: 500 if deletion fails.
    """
    try:
        service.delete_database(database_name)
    except ValidationError as e:
        logger.warning(f"Validation error deleting database: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except DatabaseError as e:
        logger.error(f"Database error deleting database: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error deleting database: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
