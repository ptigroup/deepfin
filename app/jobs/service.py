"""Job management service."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.jobs.models import Job, JobStatus, JobType
from app.jobs.schemas import JobCreate, JobUpdate

logger = get_logger(__name__)


class JobServiceError(Exception):
    """Job service errors."""

    pass


class JobService:
    """Service for managing background jobs."""

    def __init__(self, db_session: AsyncSession):
        """Initialize job service.

        Args:
            db_session: Database session
        """
        self.db = db_session

    async def create_job(self, job_data: JobCreate) -> Job:
        """Create a new job.

        Args:
            job_data: Job creation data

        Returns:
            Created job

        Raises:
            JobServiceError: If creation fails
        """
        try:
            job = Job(**job_data.model_dump())
            self.db.add(job)
            await self.db.commit()
            await self.db.refresh(job)

            logger.info(
                "Created job",
                extra={
                    "job_id": job.id,
                    "task_name": job.task_name,
                    "job_type": job.job_type.value,
                },
            )

            return job

        except Exception as e:
            await self.db.rollback()
            logger.error(
                "Failed to create job",
                extra={"error": str(e)},
                exc_info=True,
            )
            raise JobServiceError(f"Failed to create job: {str(e)}") from e

    async def get_job(self, job_id: int) -> Job | None:
        """Get job by ID.

        Args:
            job_id: Job ID

        Returns:
            Job or None if not found
        """
        stmt = select(Job).where(Job.id == job_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_jobs(
        self,
        status: JobStatus | None = None,
        job_type: JobType | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Job]:
        """Get list of jobs with optional filtering.

        Args:
            status: Filter by status
            job_type: Filter by job type
            skip: Number of records to skip
            limit: Maximum number of records

        Returns:
            List of jobs
        """
        stmt = select(Job)

        if status:
            stmt = stmt.where(Job.status == status)
        if job_type:
            stmt = stmt.where(Job.job_type == job_type)

        stmt = stmt.offset(skip).limit(limit).order_by(Job.created_at.desc())

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def update_job(self, job_id: int, job_update: JobUpdate) -> Job | None:
        """Update job status.

        Args:
            job_id: Job ID
            job_update: Update data

        Returns:
            Updated job or None if not found

        Raises:
            JobServiceError: If update fails
        """
        try:
            job = await self.get_job(job_id)
            if not job:
                return None

            # Update fields
            update_data = job_update.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(job, field, value)

            await self.db.commit()
            await self.db.refresh(job)

            logger.info(
                "Updated job",
                extra={"job_id": job.id, "updates": list(update_data.keys())},
            )

            return job

        except Exception as e:
            await self.db.rollback()
            logger.error(
                "Failed to update job",
                extra={"job_id": job_id, "error": str(e)},
                exc_info=True,
            )
            raise JobServiceError(f"Failed to update job: {str(e)}") from e

    async def cancel_job(self, job_id: int) -> bool:
        """Cancel a pending or running job.

        Args:
            job_id: Job ID to cancel

        Returns:
            True if cancelled, False if not found or cannot be cancelled
        """
        job = await self.get_job(job_id)
        if not job:
            return False

        # Only cancel pending or running jobs
        if job.status not in {JobStatus.PENDING, JobStatus.RUNNING}:
            logger.warning(
                "Cannot cancel job",
                extra={"job_id": job_id, "status": job.status.value},
            )
            return False

        job.status = JobStatus.CANCELLED
        await self.db.commit()

        logger.info("Cancelled job", extra={"job_id": job_id})
        return True

    async def delete_job(self, job_id: int) -> bool:
        """Delete a job.

        Args:
            job_id: Job ID to delete

        Returns:
            True if deleted, False if not found
        """
        job = await self.get_job(job_id)
        if not job:
            return False

        await self.db.delete(job)
        await self.db.commit()

        logger.info("Deleted job", extra={"job_id": job_id})
        return True

    async def get_job_stats(self) -> dict[str, int]:
        """Get job statistics.

        Returns:
            Dictionary with status counts
        """
        stats = {
            "total": 0,
            "pending": 0,
            "running": 0,
            "completed": 0,
            "failed": 0,
            "cancelled": 0,
        }

        stmt = select(Job)
        result = await self.db.execute(stmt)
        jobs = result.scalars().all()

        stats["total"] = len(jobs)
        for job in jobs:
            status_key = job.status.value
            if status_key in stats:
                stats[status_key] += 1

        return stats
