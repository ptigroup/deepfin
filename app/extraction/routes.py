"""REST API endpoints for extraction service."""

import json
import logging
from datetime import UTC, datetime
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.extraction.models import ExtractionStatus
from app.extraction.service import ExtractionService
from app.jobs.models import JobType
from app.jobs.schemas import JobCreate
from app.jobs.service import JobService
from app.shared.schemas import BaseResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/extraction", tags=["extraction"])


@router.post("/extract", response_model=BaseResponse, status_code=status.HTTP_202_ACCEPTED)
async def extract_from_pdf(
    file: UploadFile = File(..., description="PDF file to extract"),
    company_name: str | None = Query(None, description="Company name override"),
    fiscal_year: int | None = Query(None, ge=1900, le=2100, description="Fiscal year override"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Extract financial data from PDF file (async via background job).

    Accepts a PDF file upload and queues it for processing:
    1. Saves file to persistent storage
    2. Creates background job for extraction
    3. Returns immediately with job ID

    The background worker will:
    1. Extract text via LLMWhisperer
    2. Detect statement type
    3. Parse tables with direct parsing
    4. Store extracted data

    Returns:
        Background job ID to track extraction progress
    """
    # Validate file type
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a PDF (.pdf extension)",
        )

    try:
        # Create uploads directory if it doesn't exist
        uploads_dir = Path("uploads")
        uploads_dir.mkdir(exist_ok=True)

        # Generate unique filename with timestamp
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        safe_filename = f"{timestamp}_{file.filename}"
        file_path = uploads_dir / safe_filename

        # Save uploaded file to persistent storage
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        logger.info(
            "Saved uploaded file",
            extra={"file_path": str(file_path), "original_name": file.filename},
        )

        # Create background job for extraction
        job_service = JobService(db)

        task_args = {
            "file_path": str(file_path),
            "company_name": company_name,
            "fiscal_year": fiscal_year,
        }

        job_data = JobCreate(
            job_type=JobType.EXTRACTION,
            task_name="extract_pdf",
            task_args=json.dumps(task_args),
            max_retries=3,
        )

        job = await job_service.create_job(job_data)

        logger.info(
            "Created extraction background job",
            extra={
                "job_id": job.id,
                "file_path": str(file_path),
                "company_name": company_name,
            },
        )

        return {
            "success": True,
            "message": "Extraction job created successfully",
            "data": {
                "job_id": job.id,
                "status": job.status.value,
                "task_name": job.task_name,
                "file_name": file.filename,
            },
        }

    except Exception as e:
        logger.error(f"Unexpected error creating extraction job: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create extraction job: {str(e)}",
        ) from e


@router.get("/jobs/{job_id}", response_model=BaseResponse)
async def get_extraction_job(
    job_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get extraction job details by ID.

    Returns:
        Job details including status, results, and errors
    """
    service = ExtractionService(db)
    job = await service.get_job(job_id)

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Extraction job {job_id} not found",
        )

    return {
        "success": True,
        "data": {
            "id": job.id,
            "file_name": job.file_name,
            "status": job.status.value,
            "statement_type": job.statement_type.value if job.statement_type else None,
            "confidence": float(job.confidence) if job.confidence else None,
            "company_name": job.company_name,
            "fiscal_year": job.fiscal_year,
            "processing_time": float(job.processing_time) if job.processing_time else None,
            "error_message": job.error_message,
            "created_at": job.created_at.isoformat() if hasattr(job, "created_at") else None,
        },
    }


@router.get("/jobs", response_model=BaseResponse)
async def list_extraction_jobs(
    status_filter: ExtractionStatus | None = Query(
        None, alias="status", description="Filter by status"
    ),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum records to return"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """List extraction jobs with optional filtering.

    Returns:
        List of extraction jobs
    """
    service = ExtractionService(db)
    jobs = await service.get_jobs(status=status_filter, skip=skip, limit=limit)

    return {
        "success": True,
        "data": [
            {
                "id": job.id,
                "file_name": job.file_name,
                "status": job.status.value,
                "statement_type": job.statement_type.value if job.statement_type else None,
                "confidence": float(job.confidence) if job.confidence else None,
                "company_name": job.company_name,
                "fiscal_year": job.fiscal_year,
                "created_at": job.created_at.isoformat() if hasattr(job, "created_at") else None,
            }
            for job in jobs
        ],
        "total": len(jobs),
    }
