"""API routes for consolidation operations."""

from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.consolidation.exporter import ConsolidationExporter, ExcelExportError
from app.consolidation.schemas import (
    ConsolidatedStatementCreate,
    ConsolidatedStatementSchema,
    ConsolidatedStatementWithComparisons,
    PeriodComparisonCreate,
    PeriodComparisonSchema,
)
from app.consolidation.service import ConsolidationService, ConsolidationServiceError
from app.core.database import get_db
from app.shared.schemas import BaseResponse

router = APIRouter(prefix="/consolidation", tags=["consolidation"])


@router.post("/", response_model=BaseResponse, status_code=status.HTTP_201_CREATED)
async def create_consolidated_statement(
    statement_data: ConsolidatedStatementCreate,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Create a new consolidated statement.

    Args:
        statement_data: Consolidated statement creation data
        db: Database session

    Returns:
        Created consolidated statement

    Raises:
        HTTPException: If creation fails
    """
    service = ConsolidationService(db)

    try:
        statement = await service.create_consolidated_statement(statement_data)
        statement_schema = ConsolidatedStatementSchema.model_validate(statement)

        return {
            "success": True,
            "message": "Consolidated statement created successfully",
            "data": statement_schema.model_dump(),
        }
    except ConsolidationServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e


@router.get("/{statement_id}", response_model=BaseResponse)
async def get_consolidated_statement(
    statement_id: int,
    include_comparisons: bool = Query(False, description="Include period comparisons"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get consolidated statement by ID.

    Args:
        statement_id: Statement ID
        include_comparisons: Whether to include period comparisons
        db: Database session

    Returns:
        Consolidated statement

    Raises:
        HTTPException: If statement not found
    """
    service = ConsolidationService(db)
    statement = await service.get_consolidated_statement(statement_id, include_comparisons)

    if not statement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Consolidated statement {statement_id} not found",
        )

    if include_comparisons:
        statement_schema = ConsolidatedStatementWithComparisons.model_validate(statement)
    else:
        statement_schema = ConsolidatedStatementSchema.model_validate(statement)

    return {
        "success": True,
        "data": statement_schema.model_dump(),
    }


@router.get("/", response_model=BaseResponse)
async def list_consolidated_statements(
    company_name: str | None = Query(None, description="Filter by company name"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """List consolidated statements with optional filtering.

    Args:
        company_name: Filter by company name
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return
        db: Database session

    Returns:
        List of consolidated statements
    """
    service = ConsolidationService(db)
    statements = await service.get_consolidated_statements(company_name, skip, limit)

    statement_schemas = [
        ConsolidatedStatementSchema.model_validate(stmt) for stmt in statements
    ]

    return {
        "success": True,
        "data": [stmt.model_dump() for stmt in statement_schemas],
    }


@router.delete("/{statement_id}", response_model=BaseResponse)
async def delete_consolidated_statement(
    statement_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Delete consolidated statement and related comparisons.

    Args:
        statement_id: Statement ID to delete
        db: Database session

    Returns:
        Success confirmation

    Raises:
        HTTPException: If statement not found
    """
    service = ConsolidationService(db)
    deleted = await service.delete_consolidated_statement(statement_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Consolidated statement {statement_id} not found",
        )

    return {
        "success": True,
        "message": f"Consolidated statement {statement_id} deleted successfully",
    }


@router.post("/{statement_id}/comparisons", response_model=BaseResponse, status_code=status.HTTP_201_CREATED)
async def add_period_comparison(
    statement_id: int,
    comparison_data: PeriodComparisonCreate,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Add period comparison to consolidated statement.

    Args:
        statement_id: Consolidated statement ID
        comparison_data: Period comparison creation data
        db: Database session

    Returns:
        Created period comparison

    Raises:
        HTTPException: If statement not found or creation fails
    """
    # Ensure statement_id matches
    if comparison_data.consolidated_statement_id != statement_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Statement ID in URL must match statement ID in request body",
        )

    service = ConsolidationService(db)

    try:
        comparison = await service.add_period_comparison(comparison_data)
        comparison_schema = PeriodComparisonSchema.model_validate(comparison)

        return {
            "success": True,
            "message": "Period comparison added successfully",
            "data": comparison_schema.model_dump(),
        }
    except ConsolidationServiceError as e:
        if "not found" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e),
            ) from e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e


@router.get("/{statement_id}/comparisons", response_model=BaseResponse)
async def get_period_comparisons(
    statement_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get all period comparisons for a consolidated statement.

    Args:
        statement_id: Consolidated statement ID
        db: Database session

    Returns:
        List of period comparisons
    """
    service = ConsolidationService(db)
    comparisons = await service.get_period_comparisons(statement_id)

    comparison_schemas = [
        PeriodComparisonSchema.model_validate(comp) for comp in comparisons
    ]

    return {
        "success": True,
        "data": [comp.model_dump() for comp in comparison_schemas],
    }


@router.get("/{statement_id}/export")
async def export_to_excel(
    statement_id: int,
    db: AsyncSession = Depends(get_db),
) -> FileResponse:
    """Export consolidated statement to Excel file.

    Args:
        statement_id: Consolidated statement ID
        db: Database session

    Returns:
        Excel file response

    Raises:
        HTTPException: If statement not found or export fails
    """
    service = ConsolidationService(db)

    # Get statement with comparisons
    statement = await service.get_consolidated_statement(statement_id, include_comparisons=True)

    if not statement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Consolidated statement {statement_id} not found",
        )

    # Export to Excel
    exporter = ConsolidationExporter()

    try:
        # Create temporary file
        with NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp_file:
            tmp_path = Path(tmp_file.name)

        # Export to temp file
        exporter.export_consolidated_statement(
            statement,
            statement.period_comparisons,
            tmp_path,
        )

        # Generate safe filename
        safe_name = statement.name.replace(" ", "_").replace("/", "-")
        filename = f"{safe_name}_{statement.id}.xlsx"

        return FileResponse(
            path=tmp_path,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename=filename,
        )

    except ExcelExportError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export to Excel: {str(e)}",
        ) from e
