"""Business logic for financial statements processing service."""

import logging
from decimal import Decimal
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.llm.clients import LLMWhispererClient
from app.llm.schemas import ProcessingMode
from app.statements.models import LineItem, Statement, StatementType

logger = logging.getLogger(__name__)


class StatementProcessingError(Exception):
    """Exception raised when statement processing fails."""

    pass


class StatementService:
    """Service for managing financial statements processing."""

    def __init__(self, db_session: AsyncSession):
        """
        Initialize statement service.

        Args:
            db_session: Async database session
        """
        self.db = db_session
        self.llm_client = LLMWhispererClient(use_cache=True)

    async def create_statement(
        self,
        statement_type: StatementType,
        company_name: str,
        period_start: str,
        period_end: str,
        fiscal_year: int,
        currency: str = "USD",
        extra_metadata: str | None = None,
    ) -> Statement:
        """
        Create a new statement record.

        Args:
            statement_type: Type of financial statement
            company_name: Name of the company
            period_start: Start date (YYYY-MM-DD)
            period_end: End date (YYYY-MM-DD)
            fiscal_year: Fiscal year
            currency: Currency code
            extra_metadata: Additional metadata as JSON

        Returns:
            Created statement
        """
        statement = Statement(
            statement_type=statement_type,
            company_name=company_name,
            period_start=period_start,
            period_end=period_end,
            fiscal_year=fiscal_year,
            currency=currency,
            extra_metadata=extra_metadata,
        )

        self.db.add(statement)
        await self.db.commit()
        await self.db.refresh(statement)

        logger.info(
            f"Created statement: {statement.id} - {statement.statement_type.value} "
            f"for {statement.company_name}"
        )
        return statement

    async def get_statement(
        self, statement_id: int, with_line_items: bool = False
    ) -> Statement | None:
        """
        Get statement by ID.

        Args:
            statement_id: Statement ID
            with_line_items: Whether to load line items

        Returns:
            Statement if found, None otherwise
        """
        query = select(Statement).where(Statement.id == statement_id)

        if with_line_items:
            query = query.options(selectinload(Statement.line_items))

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_statements(
        self,
        statement_type: StatementType | None = None,
        company_name: str | None = None,
        fiscal_year: int | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Statement]:
        """
        Get list of statements.

        Args:
            statement_type: Filter by statement type
            company_name: Filter by company name
            fiscal_year: Filter by fiscal year
            limit: Maximum number of statements
            offset: Number of statements to skip

        Returns:
            List of statements
        """
        query = select(Statement)

        if statement_type:
            query = query.where(Statement.statement_type == statement_type)

        if company_name:
            query = query.where(Statement.company_name.ilike(f"%{company_name}%"))

        if fiscal_year:
            query = query.where(Statement.fiscal_year == fiscal_year)

        query = query.limit(limit).offset(offset).order_by(Statement.created_at.desc())

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def add_line_item(
        self,
        statement_id: int,
        line_item_name: str,
        value: Decimal,
        order: int,
        category: str | None = None,
        indent_level: int = 0,
        parent_id: int | None = None,
        notes: str | None = None,
    ) -> LineItem:
        """
        Add a line item to a statement.

        Args:
            statement_id: Statement ID
            line_item_name: Name of the line item
            value: Numeric value
            order: Display order
            category: Optional category
            indent_level: Indentation level (0-5)
            parent_id: Optional parent line item ID
            notes: Optional notes

        Returns:
            Created line item

        Raises:
            StatementProcessingError: If statement not found
        """
        # Verify statement exists
        statement = await self.get_statement(statement_id)
        if not statement:
            raise StatementProcessingError(f"Statement {statement_id} not found")

        line_item = LineItem(
            statement_id=statement_id,
            line_item_name=line_item_name,
            value=value,
            order=order,
            category=category,
            indent_level=indent_level,
            parent_id=parent_id,
            notes=notes,
        )

        self.db.add(line_item)
        await self.db.commit()
        await self.db.refresh(line_item)

        logger.info(f"Added line item {line_item.id} to statement {statement_id}")
        return line_item

    async def get_line_items(self, statement_id: int) -> list[LineItem]:
        """
        Get all line items for a statement.

        Args:
            statement_id: Statement ID

        Returns:
            List of line items ordered by order field
        """
        query = (
            select(LineItem).where(LineItem.statement_id == statement_id).order_by(LineItem.order)
        )

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def process_pdf_statement(
        self,
        file_path: str | Path,
        statement_type: StatementType,
        company_name: str,
        fiscal_year: int,
    ) -> dict:
        """
        Process a PDF financial statement using LLMWhisperer.

        This is a basic implementation that extracts text from PDF.
        Full statement parsing will be implemented in later sessions.

        Args:
            file_path: Path to PDF file
            statement_type: Type of statement
            company_name: Company name
            fiscal_year: Fiscal year

        Returns:
            Dict with extracted text and metadata

        Raises:
            StatementProcessingError: If processing fails
        """
        try:
            logger.info(f"Processing PDF statement: {file_path}")

            # Extract text using LLMWhisperer
            result = await self.llm_client.whisper(
                file_path=file_path,
                processing_mode=ProcessingMode.TEXT,
                force_reprocess=False,
            )

            logger.info(
                f"Extracted {len(result.extracted_text)} characters from PDF "
                f"(hash: {result.whisper_hash})"
            )

            return {
                "extracted_text": result.extracted_text,
                "whisper_hash": result.whisper_hash,
                "page_count": result.page_count,
                "processing_time": result.processing_time,
                "statement_type": statement_type.value,
                "company_name": company_name,
                "fiscal_year": fiscal_year,
            }

        except Exception as e:
            logger.error(f"Error processing PDF statement: {e}")
            raise StatementProcessingError(f"Failed to process PDF: {str(e)}") from e

    def detect_statement_type(self, text: str) -> tuple[StatementType, float]:
        """
        Detect the type of financial statement from extracted text.

        Uses keyword matching to determine statement type.

        Args:
            text: Extracted text from statement

        Returns:
            Tuple of (statement_type, confidence_score)
        """
        text_lower = text.lower()

        # Keywords for each statement type
        income_keywords = ["income statement", "profit and loss", "p&l", "revenue", "net income"]
        balance_keywords = ["balance sheet", "assets", "liabilities", "equity"]
        cash_flow_keywords = ["cash flow", "operating activities", "investing activities"]

        # Count keyword matches
        income_score = sum(1 for keyword in income_keywords if keyword in text_lower)
        balance_score = sum(1 for keyword in balance_keywords if keyword in text_lower)
        cash_flow_score = sum(1 for keyword in cash_flow_keywords if keyword in text_lower)

        # Determine type and confidence
        scores = {
            StatementType.INCOME_STATEMENT: income_score,
            StatementType.BALANCE_SHEET: balance_score,
            StatementType.CASH_FLOW: cash_flow_score,
        }

        # Get type with highest score
        detected_type = max(scores, key=scores.get)
        max_score = scores[detected_type]

        # Calculate confidence (0.0 to 1.0)
        total_score = sum(scores.values())
        confidence = max_score / total_score if total_score > 0 else 0.0

        logger.info(
            f"Detected statement type: {detected_type.value} (confidence: {confidence:.2f})"
        )

        return detected_type, confidence

    async def delete_statement(self, statement_id: int) -> bool:
        """
        Delete a statement and its line items.

        Args:
            statement_id: Statement ID

        Returns:
            True if deleted, False if not found
        """
        statement = await self.get_statement(statement_id)
        if not statement:
            return False

        await self.db.delete(statement)
        await self.db.commit()

        logger.info(f"Deleted statement {statement_id}")
        return True
