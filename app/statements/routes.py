"""REST API endpoints for financial statements processing."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.shared.schemas import BaseResponse
from app.statements.models import StatementType
from app.statements.schemas import (
    LineItemCreate,
    LineItemListResponse,
    LineItemResponse,
    StatementCreate,
    StatementListResponse,
    StatementResponse,
    StatementTypeDetectionData,
    StatementTypeDetectionResponse,
    StatementWithLineItems,
)
from app.statements.service import StatementProcessingError, StatementService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/statements", tags=["statements"])


@router.post(
    "/",
    response_model=StatementResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new financial statement",
)
async def create_statement(
    statement: StatementCreate,
    db: AsyncSession = Depends(get_db),
) -> StatementResponse:
    """
    Create a new financial statement record.

    Args:
        statement: Statement creation data
        db: Database session

    Returns:
        Created statement

    Raises:
        HTTPException: If creation fails
    """
    try:
        service = StatementService(db)
        result = await service.create_statement(
            statement_type=statement.statement_type,
            company_name=statement.company_name,
            period_start=statement.period_start,
            period_end=statement.period_end,
            fiscal_year=statement.fiscal_year,
            currency=statement.currency,
            extra_metadata=statement.extra_metadata,
        )

        return StatementResponse(
            success=True,
            message="Statement created successfully",
            data=result,
        )

    except Exception as e:
        logger.error(f"Error creating statement: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create statement: {str(e)}",
        ) from e


@router.get(
    "/{statement_id}",
    response_model=StatementResponse,
    summary="Get statement by ID",
)
async def get_statement(
    statement_id: int,
    include_line_items: bool = Query(False, description="Include line items in response"),
    db: AsyncSession = Depends(get_db),
) -> StatementResponse:
    """
    Get a financial statement by ID.

    Args:
        statement_id: Statement ID
        include_line_items: Whether to include line items
        db: Database session

    Returns:
        Statement data

    Raises:
        HTTPException: If statement not found
    """
    service = StatementService(db)
    statement = await service.get_statement(statement_id, with_line_items=include_line_items)

    if not statement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Statement {statement_id} not found",
        )

    if include_line_items:
        # Return statement with line items
        response_data = StatementWithLineItems.model_validate(statement)
        return StatementResponse(
            success=True,
            data=response_data,
        )
    else:
        return StatementResponse(
            success=True,
            data=statement,
        )


@router.get(
    "/",
    response_model=StatementListResponse,
    summary="List financial statements",
)
async def list_statements(
    statement_type: StatementType | None = Query(None, description="Filter by statement type"),
    company_name: str | None = Query(None, description="Filter by company name"),
    fiscal_year: int | None = Query(None, description="Filter by fiscal year"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    db: AsyncSession = Depends(get_db),
) -> StatementListResponse:
    """
    List financial statements with optional filters.

    Args:
        statement_type: Filter by statement type
        company_name: Filter by company name (partial match)
        fiscal_year: Filter by fiscal year
        limit: Maximum number of results
        offset: Number of results to skip
        db: Database session

    Returns:
        List of statements
    """
    service = StatementService(db)
    statements = await service.get_statements(
        statement_type=statement_type,
        company_name=company_name,
        fiscal_year=fiscal_year,
        limit=limit,
        offset=offset,
    )

    return StatementListResponse(
        success=True,
        data=statements,
        total=len(statements),
    )


@router.delete(
    "/{statement_id}",
    response_model=BaseResponse,
    summary="Delete statement",
)
async def delete_statement(
    statement_id: int,
    db: AsyncSession = Depends(get_db),
) -> BaseResponse:
    """
    Delete a financial statement and its line items.

    Args:
        statement_id: Statement ID
        db: Database session

    Returns:
        Success response

    Raises:
        HTTPException: If statement not found
    """
    service = StatementService(db)
    deleted = await service.delete_statement(statement_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Statement {statement_id} not found",
        )

    return BaseResponse(
        success=True,
        message=f"Statement {statement_id} deleted successfully",
    )


@router.post(
    "/{statement_id}/line-items",
    response_model=LineItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add line item to statement",
)
async def add_line_item(
    statement_id: int,
    line_item: LineItemCreate,
    db: AsyncSession = Depends(get_db),
) -> LineItemResponse:
    """
    Add a line item to a financial statement.

    Args:
        statement_id: Statement ID
        line_item: Line item data
        db: Database session

    Returns:
        Created line item

    Raises:
        HTTPException: If statement not found or creation fails
    """
    try:
        service = StatementService(db)

        # Override statement_id from URL
        result = await service.add_line_item(
            statement_id=statement_id,
            line_item_name=line_item.line_item_name,
            value=line_item.value,
            order=line_item.order,
            category=line_item.category,
            indent_level=line_item.indent_level,
            parent_id=line_item.parent_id,
            notes=line_item.notes,
        )

        return LineItemResponse(
            success=True,
            message="Line item added successfully",
            data=result,
        )

    except StatementProcessingError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(f"Error adding line item: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add line item: {str(e)}",
        ) from e


@router.get(
    "/{statement_id}/line-items",
    response_model=LineItemListResponse,
    summary="Get statement line items",
)
async def get_line_items(
    statement_id: int,
    db: AsyncSession = Depends(get_db),
) -> LineItemListResponse:
    """
    Get all line items for a statement.

    Args:
        statement_id: Statement ID
        db: Database session

    Returns:
        List of line items ordered by display order
    """
    service = StatementService(db)
    line_items = await service.get_line_items(statement_id)

    return LineItemListResponse(
        success=True,
        data=line_items,
        total=len(line_items),
    )


@router.post(
    "/detect-type",
    response_model=StatementTypeDetectionResponse,
    summary="Detect statement type from text",
)
async def detect_statement_type(
    text: str = Query(..., description="Extracted text from statement"),
    db: AsyncSession = Depends(get_db),
) -> StatementTypeDetectionResponse:
    """
    Detect the type of financial statement from extracted text.

    Args:
        text: Extracted text from statement
        db: Database session

    Returns:
        Detected statement type and confidence score
    """
    service = StatementService(db)
    statement_type, confidence = service.detect_statement_type(text)

    return StatementTypeDetectionResponse(
        success=True,
        data=StatementTypeDetectionData(
            statement_type=statement_type.value,
            confidence=confidence,
        ),
    )
