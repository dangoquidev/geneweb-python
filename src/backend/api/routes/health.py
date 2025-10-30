"""
Health check and status endpoints.

Provides system health, version info, and database connectivity checks.
"""

from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from backend.api.dependencies import get_repository
from backend.database.repository import Repository

router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str
    timestamp: datetime
    version: str
    database_accessible: bool


class StatusResponse(BaseModel):
    """Detailed status response model."""

    status: str
    timestamp: datetime
    version: str
    database: Dict[str, Any]


@router.get("/health", response_model=HealthResponse)
async def health_check(repository: Repository = Depends(get_repository)) -> HealthResponse:
    """
    Basic health check endpoint.

    Returns:
        Health status with timestamp and database connectivity.

    Examples:
        >>> GET /api/health
        {
            "status": "healthy",
            "timestamp": "2025-10-16T12:00:00",
            "version": "1.0.0",
            "database_accessible": true
        }
    """
    # Test database connectivity
    db_accessible = True
    try:
        # Simple check: try to get all persons count
        persons = repository.get_all_persons()
        _ = len(persons)
    except Exception:
        db_accessible = False

    return HealthResponse(
        status="healthy" if db_accessible else "degraded",
        timestamp=datetime.now(),
        version="1.0.0",
        database_accessible=db_accessible,
    )


@router.get("/status", response_model=StatusResponse)
async def status_check(repository: Repository = Depends(get_repository)) -> StatusResponse:
    """
    Detailed status endpoint with database statistics.

    Returns:
        Detailed status including database metrics.

    Examples:
        >>> GET /api/status
        {
            "status": "healthy",
            "timestamp": "2025-10-16T12:00:00",
            "version": "1.0.0",
            "database": {
                "accessible": true,
                "persons_count": 150,
                "families_count": 75
            }
        }
    """
    db_info: Dict[str, Any] = {"accessible": False}

    try:
        persons = repository.get_all_persons()
        families = repository.get_all_families()

        db_info = {
            "accessible": True,
            "persons_count": len(persons),
            "families_count": len(families),
        }
    except Exception as e:
        db_info["error"] = str(e)

    return StatusResponse(
        status="healthy" if db_info["accessible"] else "unhealthy",
        timestamp=datetime.now(),
        version="1.0.0",
        database=db_info,
    )
