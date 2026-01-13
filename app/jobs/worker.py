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

    def __init__(
        self,
        concurrency: int = 3,
        poll_interval: float = 1.0,
        task_timeout: float = 300.0,
    ):
        """Initialize worker.

        Args:
            concurrency: Number of jobs to process concurrently
            poll_interval: Seconds to wait between polling for new jobs
            task_timeout: Maximum seconds a task can run before timing out (default: 5 minutes)
        """
        self.concurrency = concurrency
        self.poll_interval = poll_interval
        self.task_timeout = task_timeout
        self.running = False
        self._tasks: set[asyncio.Task] = set()
        self._running_jobs: dict[int, asyncio.Task] = {}  # job_id -> task

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
                # Clean up completed job tracking
                self._running_jobs = {
                    job_id: task
                    for job_id, task in self._running_jobs.items()
                    if not task.done()
                }

                # Check if we can start more jobs
                if len(self._tasks) < self.concurrency:
                    async with AsyncSessionLocal() as db:
                        job = await self._get_next_job(db)

                        if job:
                            # Start processing job in background
                            task = asyncio.create_task(self._process_job(job.id))
                            self._tasks.add(task)
                            self._running_jobs[job.id] = task  # Track for cancellation
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

    async def cancel_job(self, job_id: int) -> bool:
        """Cancel a currently running job.

        Args:
            job_id: ID of the job to cancel

        Returns:
            True if job was running and cancelled, False otherwise
        """
        task = self._running_jobs.get(job_id)
        if task and not task.done():
            logger.info(
                "Cancelling running job",
                extra={"job_id": job_id},
            )
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                logger.info(
                    "Job cancelled successfully",
                    extra={"job_id": job_id},
                )
            return True
        return False

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
                try:
                    task_args = json.loads(job.task_args) if job.task_args else {}
                except json.JSONDecodeError as e:
                    logger.error(
                        "Invalid JSON in task args",
                        extra={
                            "job_id": job.id,
                            "task_name": job.task_name,
                            "error": str(e),
                        },
                    )
                    raise WorkerError(f"Invalid JSON in task arguments: {e}") from e

                # Execute task with timeout
                try:
                    result = await asyncio.wait_for(
                        task_func(**task_args), timeout=self.task_timeout
                    )
                except TimeoutError:
                    logger.error(
                        "Task timed out",
                        extra={
                            "job_id": job.id,
                            "task_name": job.task_name,
                            "timeout": self.task_timeout,
                        },
                    )
                    raise WorkerError(
                        f"Task timed out after {self.task_timeout} seconds"
                    ) from None

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
                            # Calculate exponential backoff delay (capped at 5 minutes)
                            delay_seconds = min(300, 2 ** (job.retries + 1))

                            logger.info(
                                "Job will retry after delay",
                                extra={
                                    "job_id": job.id,
                                    "retry": job.retries + 1,
                                    "max_retries": job.max_retries,
                                    "delay_seconds": delay_seconds,
                                },
                            )

                            # Wait before retrying (exponential backoff)
                            await asyncio.sleep(delay_seconds)

                            # Now set back to pending for retry
                            job.status = JobStatus.PENDING
                            job.retries += 1
                            job.started_at = None
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
