"""
Export routes for downloading databases in various formats.

Handles export operations:
- GEDCOM export
- GeneWeb .gw export (future)
- Filtered exports
"""

import logging
import tempfile
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from backend.core.exceptions import DatabaseError
from backend.services.export_service import ExportService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/export", tags=["export"])


class ExportStatisticsResponse(BaseModel):
    """Response model for export statistics."""

    database_name: str = Field(..., description="Name of database")
    persons_count: int = Field(..., description="Number of persons")
    families_count: int = Field(..., description="Number of families")
    estimated_gedcom_size_kb: int = Field(..., description="Estimated GEDCOM file size in KB")


@router.get(
    "/{database_name}/statistics",
    response_model=ExportStatisticsResponse,
    summary="Get export statistics",
    description="""
Get statistics about a database before exporting.

Useful for:
- Estimating file size
- Showing user what will be exported
- Validating database before export

**Example:**
```bash
curl http://localhost:8000/api/export/my-family/statistics
```
""",
)
async def get_export_statistics(
    database_name: str,
) -> ExportStatisticsResponse:
    """
    Get export statistics for a database.

    Args:
        database_name: Name of database.

    Returns:
        ExportStatisticsResponse with database statistics.

    Raises:
        HTTPException 404: If database doesn't exist.
        HTTPException 500: If statistics retrieval fails.
    """
    logger.info(f"Getting export statistics for database '{database_name}'")

    try:
        # Get absolute path to data directory
        project_root = Path(__file__).parent.parent.parent.parent.parent
        data_dir = project_root / "data"

        service = ExportService(database_dir=str(data_dir))
        stats = service.get_database_statistics(database_name)

        return ExportStatisticsResponse(**stats)

    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Database '{database_name}' not found",
        )

    except Exception as e:
        logger.error(f"Error getting export statistics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get statistics: {str(e)}",
        )


@router.get(
    "/{database_name}/gedcom",
    response_class=FileResponse,
    summary="Export database to GEDCOM",
    description="""
Export a GenEWeb database to GEDCOM 5.5.1 format.

Returns a downloadable GEDCOM file (.ged).

**Supports:**
- Full database export
- GEDCOM 5.5.1 specification
- UTF-8 encoding
- All persons and families

**Example:**
```bash
curl -O http://localhost:8000/api/export/my-family/gedcom
# Downloads my-family.ged
```

**Query parameters:**
- `download`: Set to true to force download (default: true)
- `include_notes`: Include notes and comments (default: true)
- `include_images`: Include image references (default: true)
""",
)
async def export_to_gedcom(
    database_name: str,
    download: bool = Query(True, description="Force download (Content-Disposition: attachment)"),
    include_notes: bool = Query(True, description="Include notes and comments in export"),
    include_images: bool = Query(True, description="Include image references in export"),
) -> FileResponse:
    """
    Export database to GEDCOM format.

    Args:
        database_name: Name of database to export.
        download: If True, force download. If False, display inline.
        include_notes: If True, include notes and comments in export.
        include_images: If True, include image references in export.

    Returns:
        FileResponse with GEDCOM file.

    Raises:
        HTTPException 404: If database doesn't exist.
        HTTPException 500: If export fails.
    """
    logger.info(f"Exporting database '{database_name}' to GEDCOM " f"(notes={include_notes}, images={include_images})")

    try:
        # Get absolute path to data directory
        project_root = Path(__file__).parent.parent.parent.parent.parent
        data_dir = project_root / "data"

        service = ExportService(database_dir=str(data_dir))

        # Create temporary file for export
        with tempfile.NamedTemporaryFile(mode="w", suffix=".ged", delete=False) as temp_file:
            temp_path = Path(temp_file.name)

        try:
            # Export to file with options
            output_path = service.export_to_gedcom(
                database_name=database_name,
                output_file=temp_path,
                include_notes=include_notes,
                include_images=include_images,
            )

            # Prepare filename
            filename = f"{database_name}.ged"

            # Return file
            disposition = "attachment" if download else "inline"

            return FileResponse(
                path=str(output_path),
                media_type="text/plain",
                filename=filename,
                headers={
                    "Content-Disposition": f'{disposition}; filename="{filename}"',
                    "X-Content-Type-Options": "nosniff",
                },
            )

        except Exception:
            # Clean up temp file on error
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except Exception:
                    pass
            raise

    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Database '{database_name}' not found",
        )

    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}",
        )

    except Exception as e:
        logger.error(f"Error exporting to GEDCOM: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export: {str(e)}",
        )


@router.get(
    "/{database_name}/geneweb",
    response_class=FileResponse,
    summary="Export database to GeneWeb .gw format",
    description="""
Export a GenEWeb database to GeneWeb .gw source format.

Returns a downloadable GeneWeb file (.gw).

**Supports:**
- Full database export
- GeneWeb .gw source format
- UTF-8 encoding
- All persons and families
- Events, notes, and relationships

**Example:**
```bash
curl -O http://localhost:8000/api/export/my-family/geneweb
# Downloads my-family.gw
```

**Query parameters:**
- `download`: Set to true to force download (default: true)
- `include_notes`: Include notes and comments (default: true)
""",
)
async def export_to_geneweb(
    database_name: str,
    download: bool = Query(True, description="Force download (Content-Disposition: attachment)"),
    include_notes: bool = Query(True, description="Include notes and comments in export"),
) -> FileResponse:
    """
    Export database to GeneWeb .gw format.

    Args:
        database_name: Name of database to export.
        download: If True, force download. If False, display inline.
        include_notes: If True, include notes and comments in export.

    Returns:
        FileResponse with GeneWeb file.

    Raises:
        HTTPException 404: If database doesn't exist.
        HTTPException 500: If export fails.
    """
    logger.info(f"Exporting database '{database_name}' to GeneWeb (notes={include_notes})")

    try:
        # Get absolute path to data directory
        project_root = Path(__file__).parent.parent.parent.parent.parent
        data_dir = project_root / "data"

        service = ExportService(database_dir=str(data_dir))

        # Create temporary file for export
        with tempfile.NamedTemporaryFile(mode="w", suffix=".gw", delete=False) as temp_file:
            temp_path = Path(temp_file.name)

        try:
            # Export to file with options
            output_path = service.export_to_geneweb(
                database_name=database_name,
                output_file=temp_path,
                include_notes=include_notes,
            )

            # Prepare filename
            filename = f"{database_name}.gw"

            # Return file
            disposition = "attachment" if download else "inline"

            return FileResponse(
                path=str(output_path),
                media_type="text/plain",
                filename=filename,
                headers={
                    "Content-Disposition": f'{disposition}; filename="{filename}"',
                    "X-Content-Type-Options": "nosniff",
                },
            )

        except Exception:
            # Clean up temp file on error
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except Exception:
                    pass
            raise

    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Database '{database_name}' not found",
        )

    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}",
        )

    except Exception as e:
        logger.error(f"Error exporting to GeneWeb: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export: {str(e)}",
        )
