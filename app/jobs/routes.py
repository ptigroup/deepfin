"""API routes for background job management."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.jobs.models import JobStatus, JobType
from app.jobs.schemas import JobCreate, JobSchema, JobSummary, JobUpdate
from app.jobs.service import JobService, JobServiceError
from app.shared.schemas import BaseResponse

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("/", response_model=BaseResponse, status_code=status.HTTP_201_CREATED)
async def create_job(
    job_data: JobCreate,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Create a new background job.

    Args:
        job_data: Job creation data
        db: Database session

    Returns:
        Created job

    Raises:
        HTTPException: If creation fails
    """
    service = JobService(db)

    try:
        job = await service.create_job(job_data)
        job_schema = JobSchema.model_validate(job)

        return {
            "success": True,
            "message": "Job created successfully",
            "data": job_schema.model_dump(),
        }
    except JobServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e


@router.get("/{job_id}", response_model=BaseResponse)
async def get_job(
    job_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get job by ID.

    Args:
        job_id: Job ID
        db: Database session

    Returns:
        Job details

    Raises:
        HTTPException: If job not found
    """
    service = JobService(db)
    job = await service.get_job(job_id)

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found",
        )

    job_schema = JobSchema.model_validate(job)

    return {
        "success": True,
        "data": job_schema.model_dump(),
    }


@router.get("/", response_model=BaseResponse)
async def list_jobs(
    status_filter: JobStatus | None = Query(None, description="Filter by status"),
    type_filter: JobType | None = Query(None, description="Filter by job type"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """List jobs with optional filtering.

    Args:
        status_filter: Filter by job status
        type_filter: Filter by job type
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return
        db: Database session

    Returns:
        List of jobs
    """
    service = JobService(db)
    jobs = await service.get_jobs(
        status=status_filter,
        job_type=type_filter,
        skip=skip,
        limit=limit,
    )

    job_schemas = [JobSummary.model_validate(job) for job in jobs]

    return {
        "success": True,
        "data": [job.model_dump() for job in job_schemas],
    }


@router.patch("/{job_id}", response_model=BaseResponse)
async def update_job(
    job_id: int,
    job_update: JobUpdate,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Update job status and progress.

    Args:
        job_id: Job ID
        job_update: Update data
        db: Database session

    Returns:
        Updated job

    Raises:
        HTTPException: If job not found or update fails
    """
    service = JobService(db)

    try:
        job = await service.update_job(job_id, job_update)

        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found",
            )

        job_schema = JobSchema.model_validate(job)

        return {
            "success": True,
            "message": "Job updated successfully",
            "data": job_schema.model_dump(),
        }
    except JobServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e


@router.post("/{job_id}/cancel", response_model=BaseResponse)
async def cancel_job(
    job_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Cancel a pending or running job.

    Args:
        job_id: Job ID
        db: Database session

    Returns:
        Success confirmation

    Raises:
        HTTPException: If job not found or cannot be cancelled
    """
    service = JobService(db)
    cancelled = await service.cancel_job(job_id)

    if not cancelled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Job {job_id} cannot be cancelled (not found or already completed)",
        )

    return {
        "success": True,
        "message": f"Job {job_id} cancelled successfully",
    }


@router.delete("/{job_id}", response_model=BaseResponse)
async def delete_job(
    job_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Delete a job.

    Args:
        job_id: Job ID
        db: Database session

    Returns:
        Success confirmation

    Raises:
        HTTPException: If job not found
    """
    service = JobService(db)
    deleted = await service.delete_job(job_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found",
        )

    return {
        "success": True,
        "message": f"Job {job_id} deleted successfully",
    }


@router.get("/stats/summary", response_model=BaseResponse)
async def get_job_stats(
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get job statistics.

    Args:
        db: Database session

    Returns:
        Job statistics by status
    """
    service = JobService(db)
    stats = await service.get_job_stats()

    return {
        "success": True,
        "data": stats,
    }
