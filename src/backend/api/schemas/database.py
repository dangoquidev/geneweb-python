"""
Database API schemas.

Pydantic models for database-related requests and responses.
"""

from typing import Literal

from pydantic import BaseModel, Field, field_validator


class DatabaseCreateRequest(BaseModel):
    """
    Request schema for creating a new database.

    Attributes:
        name: Database name (alphanumeric, underscores, hyphens allowed).
        db_type: Database type ('pickle' or 'sqlite').
    """

    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Database name (alphanumeric, underscores, hyphens)",
        examples=["ma_famille", "my-genealogy", "base2024"],
    )
    db_type: Literal["pickle", "sqlite"] = Field(
        default="pickle",
        description="Database storage type",
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """
        Validate database name.

        Args:
            v: Database name to validate.

        Returns:
            Validated database name.

        Raises:
            ValueError: If name contains invalid characters.
        """
        # Allow alphanumeric, underscores, hyphens
        if not all(c.isalnum() or c in ("_", "-") for c in v):
            raise ValueError("Database name must contain only letters, numbers, underscores, and hyphens")
        # Disallow leading/trailing spaces
        if v != v.strip():
            raise ValueError("Database name cannot have leading or trailing spaces")
        # Disallow common reserved names
        reserved = {"con", "prn", "aux", "nul", "com1", "lpt1", ".", ".."}
        if v.lower() in reserved:
            raise ValueError(f"Database name '{v}' is reserved")
        return v


class DatabaseCreateResponse(BaseModel):
    """
    Response schema for database creation.

    Attributes:
        success: Whether creation succeeded.
        database_name: Name of created database.
        path: Full path to database file.
        message: Optional success message.
    """

    success: bool = Field(..., description="Creation success status")
    database_name: str = Field(..., description="Name of the created database")
    path: str = Field(..., description="Full path to database file")
    message: str = Field(
        default="Database created successfully",
        description="Human-readable message",
    )


class DatabaseListResponse(BaseModel):
    """
    Response schema for listing databases.

    Attributes:
        databases: List of database names.
        count: Total number of databases.
    """

    databases: list[str] = Field(..., description="List of available database names")
    count: int = Field(..., description="Total number of databases")


class DatabaseInfoResponse(BaseModel):
    """
    Response schema for database information.

    Attributes:
        base_name: Database name.
        persons: Number of persons in database.
        families: Number of families in database.
        path: Full path to database file.
        version: Database version.
        created_date: Creation date (ISO 8601).
        modified_date: Last modification date (ISO 8601).
    """

    base_name: str = Field(..., description="Database name")
    persons: int = Field(..., description="Number of persons")
    families: int = Field(..., description="Number of families")
    path: str = Field(..., description="Full path to database file")
    version: str = Field(..., description="Database version")
    created_date: str = Field(..., description="Creation date")
    modified_date: str = Field(..., description="Last modification date")
