"""Background worker for processing jobs."""

import asyncio
import json
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.core.logging import get_logger
from app.jobs.models import Job, JobStatus
from app.jobs.tasks import TASK_REGISTRY

logger = get_logger(__name__)


class WorkerError(Exception):
    """Worker-related errors."""

    pass


class BackgroundWorker:
    """Background worker for processing jobs."""

    def __init__(self, concurrency: int = 3, poll_interval: float = 1.0):
        """Initialize worker.

        Args:
            concurrency: Number of jobs to process concurrently
            poll_interval: Seconds to wait between polling for new jobs
        """
        self.concurrency = concurrency
        self.poll_interval = poll_interval
        self.running = False
        self._tasks: set[asyncio.Task] = set()

    async def start(self) -> None:
        """Start the worker."""
        logger.info(
            "Starting background worker",
            extra={"concurrency": self.concurrency, "poll_interval": self.poll_interval},
        )
        self.running = True

        while self.running:
            try:
                # Clean up completed tasks
                self._tasks = {t for t in self._tasks if not t.done()}

                # Check if we can start more jobs
                if len(self._tasks) < self.concurrency:
                    async with AsyncSessionLocal() as db:
                        job = await self._get_next_job(db)

                        if job:
                            # Start processing job in background
                            task = asyncio.create_task(self._process_job(job.id))
                            self._tasks.add(task)
                        else:
                            # No jobs available, wait
                            await asyncio.sleep(self.poll_interval)
                else:
                    # At max concurrency, wait
                    await asyncio.sleep(self.poll_interval)

            except Exception as e:
                logger.error(
                    "Error in worker loop",
                    extra={"error": str(e)},
                    exc_info=True,
                )
                await asyncio.sleep(self.poll_interval)

    async def stop(self) -> None:
        """Stop the worker gracefully."""
        logger.info("Stopping background worker")
        self.running = False

        # Wait for running tasks to complete
        if self._tasks:
            logger.info(
                "Waiting for running tasks to complete",
                extra={"task_count": len(self._tasks)},
            )
            await asyncio.gather(*self._tasks, return_exceptions=True)

        logger.info("Background worker stopped")

    async def _get_next_job(self, db: AsyncSession) -> Job | None:
        """Get next pending job.

        Args:
            db: Database session

        Returns:
            Next job to process or None
        """
        stmt = (
            select(Job)
            .where(Job.status == JobStatus.PENDING)
            .order_by(Job.created_at)
            .limit(1)
        )

        result = await db.execute(stmt)
        job = result.scalar_one_or_none()

        if job:
            # Mark as running
            job.status = JobStatus.RUNNING
            job.started_at = datetime.now(UTC)
            await db.commit()
            await db.refresh(job)

        return job

    async def _process_job(self, job_id: int) -> None:
        """Process a single job.

        Args:
            job_id: Job ID to process
        """
        async with AsyncSessionLocal() as db:
            try:
                # Get job
                stmt = select(Job).where(Job.id == job_id)
                result = await db.execute(stmt)
                job = result.scalar_one_or_none()

                if not job:
                    logger.error("Job not found", extra={"job_id": job_id})
                    return

                logger.info(
                    "Processing job",
                    extra={
                        "job_id": job.id,
                        "task_name": job.task_name,
                        "job_type": job.job_type.value,
                    },
                )

                # Get task function
                task_func = TASK_REGISTRY.get(job.task_name)
                if not task_func:
                    raise WorkerError(f"Task not found: {job.task_name}")

                # Parse task args
                task_args = json.loads(job.task_args) if job.task_args else {}

                # Execute task
                result = await task_func(**task_args)

                # Mark as completed
                job.status = JobStatus.COMPLETED
                job.completed_at = datetime.now(UTC)
                job.progress = 100
                job.result = json.dumps(result) if result else None
                await db.commit()

                logger.info(
                    "Job completed successfully",
                    extra={"job_id": job.id, "task_name": job.task_name},
                )

            except Exception as e:
                logger.error(
                    "Job failed",
                    extra={"job_id": job_id, "error": str(e)},
                    exc_info=True,
                )

                # Update job with error
                try:
                    stmt = select(Job).where(Job.id == job_id)
                    result = await db.execute(stmt)
                    job = result.scalar_one_or_none()

                    if job:
                        # Check if we should retry
                        if job.retries < job.max_retries:
                            job.status = JobStatus.PENDING
                            job.retries += 1
                            job.started_at = None
                            logger.info(
                                "Job will retry",
                                extra={
                                    "job_id": job.id,
                                    "retry": job.retries,
                                    "max_retries": job.max_retries,
                                },
                            )
                        else:
                            job.status = JobStatus.FAILED
                            job.completed_at = datetime.now(UTC)
                            job.error = str(e)

                        await db.commit()

                except Exception as update_error:
                    logger.error(
                        "Failed to update job status",
                        extra={"job_id": job_id, "error": str(update_error)},
                        exc_info=True,
                    )


# Global worker instance
_worker_instance: BackgroundWorker | None = None


def get_worker() -> BackgroundWorker:
    """Get global worker instance.

    Returns:
        Background worker instance
    """
    global _worker_instance
    if _worker_instance is None:
        _worker_instance = BackgroundWorker()
    return _worker_instance
