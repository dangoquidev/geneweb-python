"""
FastAPI application factory and configuration.

This module creates and configures the FastAPI application with all necessary
middleware, error handlers, and route registrations.
"""

import os
from contextlib import asynccontextmanager
from typing import Any, Dict, Optional

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.core.exceptions import (
    DatabaseError,
    FamilyNotFoundError,
    GenEWebError,
    PersonNotFoundError,
    ValidationError,
)

# Global application state
app_state: Dict[str, Any] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifecycle events.

    Args:
        app: FastAPI application instance.

    Yields:
        None during application runtime.
    """
    # Startup
    print("🚀 Starting GenEWeb API...")
    # Initialize database connection, services, etc.
    yield
    # Shutdown
    print("👋 Shutting down GenEWeb API...")
    # Cleanup resources


def create_app(
    database_path: Optional[str] = None,
    debug: bool = False,
) -> FastAPI:
    """
    Create and configure FastAPI application.

    Args:
        database_path: Path to database file. If None, uses default.
        debug: Enable debug mode with detailed errors.

    Returns:
        Configured FastAPI application.

    Examples:
        >>> app = create_app()
        >>> app = create_app(database_path="data/my_db.pickle", debug=True)
    """
    app = FastAPI(
        title="GenEWeb API",
        description="Modern REST API for GenEWeb genealogy software",
        version="1.0.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
        lifespan=lifespan,
    )

    # Store config in app state
    app.state.database_path = database_path or "data/showcase.pickle"
    app.state.debug = debug

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if debug else ["http://localhost:3000", "http://localhost:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register error handlers
    register_error_handlers(app)

    # Register routes
    register_routes(app)

    return app


def register_error_handlers(app: FastAPI) -> None:
    """
    Register custom error handlers for the application.

    Args:
        app: FastAPI application instance.
    """

    @app.exception_handler(ValidationError)
    async def validation_error_handler(request: Request, exc: ValidationError) -> JSONResponse:
        """Handle ValidationError exceptions."""
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": "validation_error",
                "message": str(exc),
                "details": exc.details if hasattr(exc, "details") else None,
            },
        )

    @app.exception_handler(PersonNotFoundError)
    async def person_not_found_handler(request: Request, exc: PersonNotFoundError) -> JSONResponse:
        """Handle PersonNotFoundError exceptions."""
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "error": "person_not_found",
                "message": str(exc),
                "person_id": exc.person_id if hasattr(exc, "person_id") else None,
            },
        )

    @app.exception_handler(FamilyNotFoundError)
    async def family_not_found_handler(request: Request, exc: FamilyNotFoundError) -> JSONResponse:
        """Handle FamilyNotFoundError exceptions."""
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "error": "family_not_found",
                "message": str(exc),
                "family_id": exc.family_id if hasattr(exc, "family_id") else None,
            },
        )

    @app.exception_handler(DatabaseError)
    async def database_error_handler(request: Request, exc: DatabaseError) -> JSONResponse:
        """Handle DatabaseError exceptions."""
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "database_error",
                "message": "An error occurred while accessing the database",
                "details": str(exc) if app.state.debug else None,
            },
        )

    @app.exception_handler(GenEWebError)
    async def geneweb_error_handler(request: Request, exc: GenEWebError) -> JSONResponse:
        """Handle generic GenEWebError exceptions."""
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "internal_error",
                "message": str(exc),
            },
        )

    @app.exception_handler(RequestValidationError)
    async def request_validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        """Handle Pydantic validation errors."""
        # Extract error details in JSON-serializable format
        errors = []
        for error in exc.errors():
            error_dict = {
                "type": error["type"],
                "loc": error["loc"],
                "msg": error["msg"],
                "input": error.get("input"),
            }
            # Extract ValueError message if present in ctx
            if "ctx" in error and "error" in error["ctx"]:
                ctx_error = error["ctx"]["error"]
                if isinstance(ctx_error, ValueError):
                    error_dict["ctx"] = {"error": str(ctx_error)}
                else:
                    error_dict["ctx"] = error["ctx"]
            errors.append(error_dict)

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": "request_validation_error",
                "message": "Invalid request data",
                "details": errors,
            },
        )

    @app.exception_handler(Exception)
    async def generic_error_handler(request: Request, exc: Exception) -> JSONResponse:
        """Handle unexpected exceptions."""
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "internal_server_error",
                "message": "An unexpected error occurred",
                "details": str(exc) if app.state.debug else None,
            },
        )


def register_routes(app: FastAPI) -> None:
    """
    Register all API routes.

    Args:
        app: FastAPI application instance.
    """
    from backend.api.routes import (
        database_families,
        database_persons,
        databases,
        export_routes,
        families,
        health,
        import_routes,
        persons,
        search,
    )

    # Health check
    app.include_router(health.router, prefix="/api", tags=["Health"])

    # Database management
    app.include_router(databases.router, prefix="/api", tags=["Database Management"])

    # Database consultation (per-database access)
    app.include_router(database_persons.router, prefix="/api", tags=["Database Consultation"])
    app.include_router(database_families.router, prefix="/api", tags=["Database Consultation"])

    # Import routes (GEDCOM, GeneWeb, etc.)
    app.include_router(import_routes.router, prefix="/api", tags=["Import"])

    # Export routes (GEDCOM, GeneWeb, etc.)
    app.include_router(export_routes.router, prefix="/api", tags=["Export"])

    # Main API routes (default database)
    app.include_router(persons.router, prefix="/api/persons", tags=["Persons"])
    app.include_router(families.router, prefix="/api/families", tags=["Families"])
    app.include_router(search.router, prefix="/api/search", tags=["Search"])


# Create module-level app instance for uvicorn import string
# Configuration comes from environment variables
app = create_app(
    database_path=os.environ.get("GENEWEB_DATABASE_PATH", "data/showcase.pickle"),
    debug=os.environ.get("GENEWEB_DEBUG", "False").lower() == "true",
)
