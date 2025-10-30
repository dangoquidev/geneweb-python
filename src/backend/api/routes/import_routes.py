"""
Import routes for genealogy files (GEDCOM, GeneWeb, etc.).

Handles file uploads and import operations.
"""

import logging
import tempfile
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel, Field

from backend.core.exceptions import DatabaseError, ValidationError
from backend.services.gedcom_import_service import GedcomImportService
from backend.services.geneweb_import_service import GeneWebImportService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/import", tags=["import"])


class ImportStatisticsResponse(BaseModel):
    """Response model for import statistics preview."""

    file_path: str = Field(..., description="Path to uploaded file")
    file_size_bytes: int = Field(..., description="File size in bytes")
    individuals: int = Field(..., description="Number of individuals")
    families: int = Field(..., description="Number of families")
    notes: int = Field(0, description="Number of notes")
    sources: int = Field(0, description="Number of sources")
    total_records: int = Field(..., description="Total GEDCOM records")
    warnings_count: int = Field(0, description="Number of warnings")
    errors_count: int = Field(0, description="Number of errors")


class ImportReportResponse(BaseModel):
    """Response model for import operation."""

    success: bool = Field(..., description="Whether import succeeded")
    database_name: str = Field(..., description="Name of created database")
    database_path: str = Field(..., description="Path to database file")
    persons_count: int = Field(..., description="Number of persons imported")
    families_count: int = Field(..., description="Number of families imported")
    warnings: list[str] = Field(default_factory=list, description="Import warnings")
    errors: list[str] = Field(default_factory=list, description="Import errors")
    duration_seconds: float = Field(..., description="Import duration in seconds")
    summary: str = Field(..., description="Human-readable summary")


@router.post(
    "/gedcom",
    response_model=ImportReportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Import GEDCOM file",
    description="""
Import a GEDCOM file and create a new GenEWeb database.

**Supported formats:**
- GEDCOM 5.5.1
- Various character encodings (UTF-8, ANSEL, Latin-1, etc.)

**Process:**
1. Validate uploaded file
2. Parse GEDCOM structure
3. Convert to GenEWeb models
4. Save to database
5. Return import report

**Example:**
```bash
curl -X POST http://localhost:8000/api/import/gedcom \\
  -F "file=@family.ged" \\
  -F "database_name=my-family" \\
  -F "overwrite=false"
```
""",
)
async def import_gedcom(
    file: UploadFile = File(..., description="GEDCOM file to import"),
    database_name: Optional[str] = Form(None, description="Output database name (default: filename)"),
    encoding: str = Form("utf-8", description="Character encoding (default: utf-8, auto-detected)"),
    lenient: bool = Form(True, description="Ignore non-critical errors (default: true)"),
    overwrite: bool = Form(False, description="Overwrite existing database (default: false)"),
) -> ImportReportResponse:
    """
    Import a GEDCOM file into a GenEWeb database.

    Args:
        file: Uploaded GEDCOM file.
        database_name: Name for the output database (optional, derived from filename if not provided).
        encoding: Character encoding (default: utf-8, can be auto-detected).
        lenient: If True, ignore non-critical errors. If False, fail on any error.
        overwrite: If True, overwrite existing database. If False, fail if exists.

    Returns:
        ImportReportResponse with statistics and status.

    Raises:
        HTTPException 400: Invalid file format or database name.
        HTTPException 409: Database already exists and overwrite=False.
        HTTPException 500: Import failed.
    """
    # Validate file
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No filename provided",
        )

    # Validate file extension
    allowed_extensions = {".ged", ".gedcom"}
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file format. Allowed: {', '.join(allowed_extensions)}. Got: {file_ext}",
        )

    # Derive database name from filename if not provided
    if not database_name:
        database_name = Path(file.filename).stem
        # Clean name: replace spaces and underscores with hyphens
        database_name = database_name.replace(" ", "-").replace("_", "-")
        # Remove non-alphanumeric characters except hyphens
        database_name = "".join(c for c in database_name if c.isalnum() or c == "-")

    logger.info(f"Importing GEDCOM file '{file.filename}' to database '{database_name}'")

    # Save uploaded file to temporary location
    temp_file = None
    try:
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode="wb", suffix=".ged", delete=False) as temp_file:
            # Read uploaded file in chunks to handle large files
            chunk_size = 1024 * 1024  # 1 MB chunks
            while chunk := await file.read(chunk_size):
                temp_file.write(chunk)
            temp_file.flush()

        temp_file_path = Path(temp_file.name)
        logger.info(f"Saved uploaded file to: {temp_file_path}")

        # Import GEDCOM
        # Use absolute path to data directory (5 levels up from import_routes.py)
        # src/backend/api/routes/import_routes.py -> Awkward_legacy/
        project_root = Path(__file__).parent.parent.parent.parent.parent
        data_dir = project_root / "data"
        data_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Using data directory: {data_dir.absolute()}")
        service = GedcomImportService(database_dir=str(data_dir))

        try:
            report = service.import_gedcom(
                gedcom_file_path=temp_file_path,
                output_database_name=database_name,
                encoding=encoding,
                lenient=lenient,
                overwrite=overwrite,
            )

            if not report.success:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail={
                        "message": "Import failed",
                        "errors": report.errors,
                        "warnings": report.warnings,
                    },
                )

            logger.info(f"✅ Import successful: {report.summary}")

            return ImportReportResponse(**report.to_dict())

        except ValidationError as e:
            if "already exists" in str(e).lower():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=str(e),
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(e),
                )

        except DatabaseError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error: {str(e)}",
            )

    except HTTPException:
        # Re-raise HTTP exceptions
        raise

    except Exception as e:
        logger.error(f"Unexpected error during GEDCOM import: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )

    finally:
        # Clean up temporary file
        if temp_file and temp_file_path.exists():
            try:
                temp_file_path.unlink()
                logger.info(f"Cleaned up temporary file: {temp_file_path}")
            except Exception as cleanup_error:
                logger.warning(f"Failed to clean up {temp_file_path}: {cleanup_error}")


@router.post(
    "/gedcom/preview",
    response_model=ImportStatisticsResponse,
    summary="Preview GEDCOM import",
    description="""
Preview a GEDCOM file without importing.

Returns statistics about the file content:
- Number of individuals
- Number of families
- File size
- Potential warnings/errors

Useful for validating file before actual import.

**Example:**
```bash
curl -X POST http://localhost:8000/api/import/gedcom/preview \\
  -F "file=@family.ged"
```
""",
)
async def preview_gedcom_import(
    file: UploadFile = File(..., description="GEDCOM file to preview"),
) -> ImportStatisticsResponse:
    """
    Preview GEDCOM import without creating database.

    Args:
        file: Uploaded GEDCOM file.

    Returns:
        ImportStatisticsResponse with file statistics.

    Raises:
        HTTPException 400: Invalid file format.
        HTTPException 500: Preview failed.
    """
    # Validate file
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No filename provided",
        )

    # Validate file extension
    allowed_extensions = {".ged", ".gedcom"}
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file format. Allowed: {', '.join(allowed_extensions)}",
        )

    logger.info(f"Previewing GEDCOM file '{file.filename}'")

    # Save uploaded file to temporary location
    temp_file = None
    try:
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode="wb", suffix=".ged", delete=False) as temp_file:
            # Read uploaded file in chunks
            chunk_size = 1024 * 1024  # 1 MB chunks
            while chunk := await file.read(chunk_size):
                temp_file.write(chunk)
            temp_file.flush()

        temp_file_path = Path(temp_file.name)

        # Get statistics
        service = GedcomImportService()
        stats = service.get_import_statistics(temp_file_path)

        logger.info(f"Preview: {stats['individuals']} individuals, {stats['families']} families")

        return ImportStatisticsResponse(**stats)

    except Exception as e:
        logger.error(f"Error previewing GEDCOM: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to preview file: {str(e)}",
        )

    finally:
        # Clean up temporary file
        if temp_file and temp_file_path.exists():
            try:
                temp_file_path.unlink()
                logger.info(f"Cleaned up temporary file: {temp_file_path}")
            except Exception as cleanup_error:
                logger.warning(f"Failed to clean up {temp_file_path}: {cleanup_error}")


@router.post(
    "/geneweb",
    response_model=ImportReportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Import GeneWeb file",
    description="""
Import a GeneWeb .gw source file and create a new GenEWeb database.

**Supported formats:**
- GeneWeb .gw source files (UTF-8 encoding)
- gwplus extended format

**Process:**
1. Validate uploaded file
2. Parse GeneWeb structure
3. Convert to GenEWeb models
4. Save to database
5. Return import report

**Example:**
```bash
curl -X POST http://localhost:8000/api/import/geneweb \\
  -F "file=@family.gw" \\
  -F "database_name=my-family" \\
  -F "overwrite=false"
```
""",
)
async def import_geneweb(
    file: UploadFile = File(..., description="GeneWeb .gw file to import"),
    database_name: Optional[str] = Form(None, description="Output database name (default: filename)"),
    lenient: bool = Form(True, description="Ignore non-critical errors (default: true)"),
    overwrite: bool = Form(False, description="Overwrite existing database (default: false)"),
) -> ImportReportResponse:
    """
    Import a GeneWeb .gw file into a GenEWeb database.

    Args:
        file: Uploaded GeneWeb file.
        database_name: Name for the output database (optional, derived from filename if not provided).
        lenient: If True, ignore non-critical errors. If False, fail on any error.
        overwrite: If True, overwrite existing database. If False, fail if exists.

    Returns:
        ImportReportResponse with statistics and status.

    Raises:
        HTTPException 400: Invalid file format or database name.
        HTTPException 409: Database already exists and overwrite=False.
        HTTPException 500: Import failed.
    """
    # Validate file
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No filename provided",
        )

    # Validate file extension
    allowed_extensions = {".gw", ".txt"}
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file format. Allowed: {', '.join(allowed_extensions)}. Got: {file_ext}",
        )

    # Derive database name from filename if not provided
    if not database_name:
        database_name = Path(file.filename).stem
        # Clean name: replace spaces and underscores with hyphens
        database_name = database_name.replace(" ", "-").replace("_", "-")
        # Remove non-alphanumeric characters except hyphens
        database_name = "".join(c for c in database_name if c.isalnum() or c == "-")

    logger.info(f"Importing GeneWeb file '{file.filename}' to database '{database_name}'")

    # Save uploaded file to temporary location
    temp_file = None
    try:
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode="wb", suffix=".gw", delete=False) as temp_file:
            # Read uploaded file in chunks to handle large files
            chunk_size = 1024 * 1024  # 1 MB chunks
            while chunk := await file.read(chunk_size):
                temp_file.write(chunk)
            temp_file.flush()

        temp_file_path = Path(temp_file.name)
        logger.info(f"Saved uploaded file to: {temp_file_path}")

        # Import GeneWeb
        # Use absolute path to data directory
        project_root = Path(__file__).parent.parent.parent.parent.parent
        data_dir = project_root / "data"
        data_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Using data directory: {data_dir.absolute()}")
        service = GeneWebImportService(database_dir=str(data_dir))

        try:
            report = service.import_geneweb(
                geneweb_file_path=temp_file_path,
                output_database_name=database_name,
                lenient=lenient,
                overwrite=overwrite,
            )

            if not report.success:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail={
                        "message": "Import failed",
                        "errors": report.errors,
                        "warnings": report.warnings,
                    },
                )

            logger.info(f"✅ Import successful: {report.summary}")

            return ImportReportResponse(**report.to_dict())

        except ValidationError as e:
            if "already exists" in str(e).lower():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=str(e),
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(e),
                )

        except DatabaseError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error: {str(e)}",
            )

    except HTTPException:
        # Re-raise HTTP exceptions
        raise

    except Exception as e:
        logger.error(f"Unexpected error during GeneWeb import: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )

    finally:
        # Clean up temporary file
        if temp_file and temp_file_path.exists():
            try:
                temp_file_path.unlink()
                logger.info(f"Cleaned up temporary file: {temp_file_path}")
            except Exception as cleanup_error:
                logger.warning(f"Failed to clean up {temp_file_path}: {cleanup_error}")


@router.post(
    "/geneweb/preview",
    response_model=ImportStatisticsResponse,
    summary="Preview GeneWeb import",
    description="""
Preview a GeneWeb .gw file without importing.

Returns statistics about the file content:
- Number of persons
- Number of families
- File size
- Encoding information

Useful for validating file before actual import.

**Example:**
```bash
curl -X POST http://localhost:8000/api/import/geneweb/preview \\
  -F "file=@family.gw"
```
""",
)
async def preview_geneweb_import(
    file: UploadFile = File(..., description="GeneWeb file to preview"),
) -> ImportStatisticsResponse:
    """
    Preview GeneWeb import without creating database.

    Args:
        file: Uploaded GeneWeb file.

    Returns:
        ImportStatisticsResponse with file statistics.

    Raises:
        HTTPException 400: Invalid file format.
        HTTPException 500: Preview failed.
    """
    # Validate file
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No filename provided",
        )

    # Validate file extension
    allowed_extensions = {".gw", ".txt"}
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file format. Allowed: {', '.join(allowed_extensions)}",
        )

    logger.info(f"Previewing GeneWeb file '{file.filename}'")

    # Save uploaded file to temporary location
    temp_file = None
    try:
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode="wb", suffix=".gw", delete=False) as temp_file:
            # Read uploaded file in chunks
            chunk_size = 1024 * 1024  # 1 MB chunks
            while chunk := await file.read(chunk_size):
                temp_file.write(chunk)
            temp_file.flush()

        temp_file_path = Path(temp_file.name)

        # Get statistics
        service = GeneWebImportService()
        stats = service.get_import_statistics(temp_file_path)

        logger.info(f"Preview: {stats['persons']} persons, {stats['families']} families")

        return ImportStatisticsResponse(
            file_path=stats["file_path"],
            file_size_bytes=stats["file_size_bytes"],
            individuals=stats["persons"],
            families=stats["families"],
            notes=stats["notes_count"],
            sources=0,
            total_records=stats["total_records"],
            warnings_count=stats["warnings_count"],
            errors_count=stats["errors_count"],
        )

    except Exception as e:
        logger.error(f"Error previewing GeneWeb: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to preview file: {str(e)}",
        )

    finally:
        # Clean up temporary file
        if temp_file and temp_file_path.exists():
            try:
                temp_file_path.unlink()
                logger.info(f"Cleaned up temporary file: {temp_file_path}")
            except Exception as cleanup_error:
                logger.warning(f"Failed to clean up {temp_file_path}: {cleanup_error}")
