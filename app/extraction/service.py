"""Extraction service for orchestrating PDF processing and data extraction."""

import hashlib
import time
from decimal import Decimal
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.extraction.models import (
    ExtractedLineItem,
    ExtractedStatement,
    ExtractionJob,
    ExtractionStatus,
    StatementType,
)
from app.extraction.parser import DirectParser, ParseError
from app.llm.clients import LLMWhispererClient, LLMWhispererError
from app.llm.schemas import ProcessingMode

logger = get_logger(__name__)


class ExtractionServiceError(Exception):
    """Exception raised by extraction service."""

    pass


class ExtractionService:
    """Service for orchestrating financial statement extraction.

    Coordinates:
    1. PDF text extraction via LLMWhisperer
    2. Direct parsing of tables
    3. Database persistence
    4. Error handling and status tracking
    """

    def __init__(self, db_session: AsyncSession):
        """Initialize extraction service.

        Args:
            db_session: Async database session
        """
        self.db = db_session
        self.llm_client = LLMWhispererClient(use_cache=True)
        self.parser = DirectParser()

    async def extract_from_pdf(
        self,
        file_path: str | Path,
        company_name: str | None = None,
        fiscal_year: int | None = None,
    ) -> ExtractionJob:
        """Extract financial data from PDF file.

        Main orchestration method that:
        1. Creates extraction job
        2. Extracts text via LLMWhisperer
        3. Detects statement type
        4. Parses tables
        5. Stores extracted data

        Args:
            file_path: Path to PDF file
            company_name: Optional company name override
            fiscal_year: Optional fiscal year override

        Returns:
            ExtractionJob with results

        Raises:
            ExtractionServiceError: If extraction fails
        """
        file_path = Path(file_path)
        start_time = time.time()

        logger.info("Starting extraction", extra={"file_path": str(file_path)})

        # Calculate file hash
        file_hash = self._calculate_file_hash(file_path)

        # Check for existing job
        existing_job = await self._get_job_by_hash(file_hash)
        if existing_job and existing_job.status == ExtractionStatus.COMPLETED:
            logger.info("Returning existing completed job", extra={"job_id": existing_job.id})
            return existing_job

        # Create extraction job
        job = ExtractionJob(
            file_path=str(file_path),
            file_name=file_path.name,
            file_hash=file_hash,
            status=ExtractionStatus.PENDING,
        )
        self.db.add(job)
        await self.db.flush()

        try:
            # Update status to processing
            job.status = ExtractionStatus.PROCESSING
            await self.db.flush()

            # Step 1: Extract text via LLMWhisperer
            logger.info("Extracting text via LLMWhisperer", extra={"job_id": job.id})
            whisper_result = await self.llm_client.whisper(
                file_path=file_path, processing_mode=ProcessingMode.TEXT
            )

            job.extracted_text = whisper_result.extracted_text

            # Step 2: Detect statement type
            statement_type, confidence = self._detect_statement_type(whisper_result.extracted_text)
            job.statement_type = statement_type
            job.confidence = Decimal(str(confidence))

            logger.info(
                "Statement type detected",
                extra={
                    "type": statement_type.value,
                    "confidence": float(confidence),
                },
            )

            # Step 3: Parse tables
            logger.info("Parsing tables", extra={"job_id": job.id})
            self.parser.reset()
            parsed_data = self.parser.parse_table(whisper_result.extracted_text)

            # Step 4: Extract metadata
            periods = parsed_data["periods"]
            if not company_name:
                company_name = self._extract_company_name(whisper_result.extracted_text)
            if not fiscal_year and periods:
                fiscal_year = self._extract_fiscal_year(periods[0])

            job.company_name = company_name
            job.fiscal_year = fiscal_year

            # Step 5: Create extracted statement
            period_start, period_end = self._determine_periods(periods)

            statement = ExtractedStatement(
                extraction_job_id=job.id,
                statement_type=statement_type,
                company_name=company_name or "Unknown",
                period_start=period_start,
                period_end=period_end,
                fiscal_year=fiscal_year or 0,
                currency="USD",  # TODO: Detect from document
                total_line_items=len(parsed_data["line_items"]),
                has_errors=False,
            )
            self.db.add(statement)
            await self.db.flush()

            # Step 6: Create extracted line items
            for item_data in parsed_data["line_items"]:
                # Extract first value (latest period)
                value_text = item_data["values"][0] if item_data["values"] else "0"
                try:
                    value = self.parser.parse_value(value_text)
                except ParseError:
                    value = Decimal("0")

                line_item = ExtractedLineItem(
                    extracted_statement_id=statement.id,
                    line_item_name=item_data["name"],
                    value=value,
                    indent_level=item_data["indent_level"],
                    order=item_data["order"],
                    section=item_data["section"],
                    is_header=item_data["is_header"],
                    is_total=item_data["is_total"],
                    is_calculated=False,  # TODO: Detect calculated rows
                    raw_text=item_data.get("raw_text"),
                )
                self.db.add(line_item)

            # Step 7: Mark as completed
            job.status = ExtractionStatus.COMPLETED
            job.processing_time = Decimal(str(time.time() - start_time))

            await self.db.commit()

            logger.info(
                "Extraction completed successfully",
                extra={
                    "job_id": job.id,
                    "line_items": len(parsed_data["line_items"]),
                    "processing_time": float(job.processing_time),
                },
            )

            return job

        except (LLMWhispererError, ParseError) as e:
            # Handle extraction errors
            job.status = ExtractionStatus.FAILED
            job.error_message = str(e)
            job.processing_time = Decimal(str(time.time() - start_time))

            await self.db.commit()

            logger.error(
                "Extraction failed",
                extra={"job_id": job.id, "error": str(e)},
                exc_info=True,
            )

            raise ExtractionServiceError(f"Extraction failed: {str(e)}") from e

        except Exception as e:
            # Handle unexpected errors
            job.status = ExtractionStatus.FAILED
            job.error_message = f"Unexpected error: {str(e)}"
            job.processing_time = Decimal(str(time.time() - start_time))

            await self.db.commit()

            logger.error(
                "Unexpected extraction error",
                extra={"job_id": job.id},
                exc_info=True,
            )

            raise ExtractionServiceError(f"Extraction failed: {str(e)}") from e

    async def get_job(self, job_id: int) -> ExtractionJob | None:
        """Get extraction job by ID.

        Args:
            job_id: Job ID

        Returns:
            ExtractionJob or None if not found
        """
        stmt = select(ExtractionJob).where(ExtractionJob.id == job_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_jobs(
        self,
        status: ExtractionStatus | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[ExtractionJob]:
        """Get list of extraction jobs.

        Args:
            status: Filter by status
            skip: Number of records to skip
            limit: Maximum number of records

        Returns:
            List of extraction jobs
        """
        stmt = select(ExtractionJob)

        if status:
            stmt = stmt.where(ExtractionJob.status == status)

        stmt = stmt.offset(skip).limit(limit).order_by(ExtractionJob.created_at.desc())

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of file.

        Args:
            file_path: Path to file

        Returns:
            Hex string of file hash
        """
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    async def _get_job_by_hash(self, file_hash: str) -> ExtractionJob | None:
        """Get existing job by file hash.

        Args:
            file_hash: File hash

        Returns:
            ExtractionJob or None
        """
        stmt = select(ExtractionJob).where(ExtractionJob.file_hash == file_hash)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    def _detect_statement_type(self, text: str) -> tuple[StatementType, float]:
        """Detect statement type from extracted text.

        Args:
            text: Extracted text

        Returns:
            Tuple of (StatementType, confidence_score)
        """
        text_lower = text.lower()

        # Define keywords for each statement type
        keywords = {
            StatementType.INCOME_STATEMENT: [
                "income statement",
                "statement of income",
                "profit and loss",
                "p&l",
                "revenue",
                "net income",
                "operating income",
            ],
            StatementType.BALANCE_SHEET: [
                "balance sheet",
                "statement of financial position",
                "assets",
                "liabilities",
                "equity",
                "shareholders equity",
            ],
            StatementType.CASH_FLOW: [
                "cash flow",
                "statement of cash flows",
                "operating activities",
                "investing activities",
                "financing activities",
            ],
        }

        # Count keyword matches
        scores = {}
        for stmt_type, keyword_list in keywords.items():
            score = sum(1 for keyword in keyword_list if keyword in text_lower)
            scores[stmt_type] = score

        # Find type with highest score
        if max(scores.values()) == 0:
            return StatementType.UNKNOWN, 0.0

        detected_type = max(scores, key=scores.get)
        total_matches = sum(scores.values())
        confidence = scores[detected_type] / total_matches if total_matches > 0 else 0.0

        return detected_type, confidence

    def _extract_company_name(self, text: str) -> str:
        """Extract company name from document.

        Simple extraction - looks for company name near top of document.

        Args:
            text: Extracted text

        Returns:
            Company name or "Unknown"
        """
        # Take first few lines
        lines = text.split("\n")[:10]

        for line in lines:
            line = line.strip()
            # Company names are often in title case and longer
            # Skip common headers
            if (
                line
                and len(line) > 5
                and not line.isupper()
                and not any(
                    keyword in line.lower()
                    for keyword in [
                        "statement",
                        "balance",
                        "income",
                        "cash",
                        "period",
                        "year",
                    ]
                )
            ):
                return line

        return "Unknown"

    def _extract_fiscal_year(self, period_text: str) -> int:
        """Extract fiscal year from period text.

        Args:
            period_text: Period label (e.g., "2024", "FY 2024")

        Returns:
            Fiscal year as integer
        """
        # Look for 4-digit year
        import re

        match = re.search(r"\b(20\d{2})\b", period_text)
        if match:
            return int(match.group(1))

        return 0

    def _determine_periods(self, periods: list[str]) -> tuple[str, str]:
        """Determine period start and end dates.

        Args:
            periods: List of period labels

        Returns:
            Tuple of (period_start, period_end) in YYYY-MM-DD format
        """
        if not periods:
            return "1900-01-01", "1900-12-31"

        # Extract year from first period
        year = self._extract_fiscal_year(periods[0])
        if year == 0:
            return "1900-01-01", "1900-12-31"

        # Assume fiscal year
        return f"{year}-01-01", f"{year}-12-31"
