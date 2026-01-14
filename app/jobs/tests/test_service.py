"""Tests for job service."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.jobs.models import Job, JobStatus, JobType
from app.jobs.schemas import JobCreate, JobUpdate
from app.jobs.service import JobService


class TestJobService:
    """Test job service operations."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = AsyncMock(spec=AsyncSession)
        db.commit = AsyncMock()
        db.rollback = AsyncMock()
        db.refresh = AsyncMock()
        db.add = MagicMock()
        db.execute = AsyncMock()
        db.delete = AsyncMock()
        return db

    @pytest.fixture
    def service(self, mock_db):
        """Create job service instance."""
        return JobService(mock_db)

    @pytest.fixture
    def sample_job(self):
        """Create sample job."""
        job = MagicMock(spec=Job)
        job.id = 1
        job.job_type = JobType.EXTRACTION
        job.status = JobStatus.PENDING
        job.task_name = "example_task"
        job.task_args = '{"message": "test"}'
        job.result = None
        job.error = None
        job.progress = 0
        job.retries = 0
        job.max_retries = 3
        return job

    @pytest.mark.asyncio
    async def test_create_job(self, service, mock_db):
        """Test creating a job."""
        job_data = JobCreate(
            job_type=JobType.EXTRACTION,
            task_name="example_task",
            task_args='{"message": "test"}',
        )

        await service.create_job(job_data)

        assert mock_db.add.called
        assert mock_db.commit.called
        assert mock_db.refresh.called

    @pytest.mark.asyncio
    async def test_create_job_with_max_retries(self, service, mock_db):
        """Test creating job with custom max retries."""
        job_data = JobCreate(
            job_type=JobType.CONSOLIDATION,
            task_name="generate_consolidation",
            max_retries=5,
        )

        await service.create_job(job_data)

        assert mock_db.add.called
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_get_job(self, service, sample_job, mock_db):
        """Test getting job by ID."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_job
        mock_db.execute.return_value = mock_result

        job = await service.get_job(1)

        assert job is not None
        assert job.id == 1
        assert mock_db.execute.called

    @pytest.mark.asyncio
    async def test_get_job_not_found(self, service, mock_db):
        """Test getting non-existent job."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        job = await service.get_job(99999)

        assert job is None

    @pytest.mark.asyncio
    async def test_get_jobs(self, service, mock_db):
        """Test listing jobs."""
        mock_jobs = [
            MagicMock(id=1, status=JobStatus.PENDING),
            MagicMock(id=2, status=JobStatus.RUNNING),
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_jobs
        mock_db.execute.return_value = mock_result

        jobs = await service.get_jobs()

        assert len(jobs) == 2
        assert mock_db.execute.called

    @pytest.mark.asyncio
    async def test_get_jobs_filtered_by_status(self, service, mock_db):
        """Test filtering jobs by status."""
        mock_jobs = [MagicMock(id=1, status=JobStatus.COMPLETED)]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_jobs
        mock_db.execute.return_value = mock_result

        jobs = await service.get_jobs(status=JobStatus.COMPLETED)

        assert len(jobs) == 1
        assert jobs[0].status == JobStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_get_jobs_filtered_by_type(self, service, mock_db):
        """Test filtering jobs by type."""
        mock_jobs = [MagicMock(id=1, job_type=JobType.EXTRACTION)]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_jobs
        mock_db.execute.return_value = mock_result

        jobs = await service.get_jobs(job_type=JobType.EXTRACTION)

        assert len(jobs) == 1

    @pytest.mark.asyncio
    async def test_get_jobs_pagination(self, service, mock_db):
        """Test job pagination."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        await service.get_jobs(skip=10, limit=20)

        assert mock_db.execute.called

    @pytest.mark.asyncio
    async def test_update_job(self, service, sample_job, mock_db):
        """Test updating job."""
        mock_get_result = MagicMock()
        mock_get_result.scalar_one_or_none.return_value = sample_job
        mock_db.execute.return_value = mock_get_result

        job_update = JobUpdate(status=JobStatus.RUNNING, progress=50)
        updated_job = await service.update_job(1, job_update)

        assert updated_job is not None
        assert mock_db.commit.called
        assert mock_db.refresh.called

    @pytest.mark.asyncio
    async def test_update_job_not_found(self, service, mock_db):
        """Test updating non-existent job."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        job_update = JobUpdate(status=JobStatus.RUNNING)
        updated_job = await service.update_job(99999, job_update)

        assert updated_job is None

    @pytest.mark.asyncio
    async def test_cancel_job(self, service, sample_job, mock_db):
        """Test cancelling a job."""
        sample_job.status = JobStatus.PENDING
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_job
        mock_db.execute.return_value = mock_result

        cancelled = await service.cancel_job(1)

        assert cancelled is True
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_cancel_job_already_completed(self, service, sample_job, mock_db):
        """Test cancelling completed job fails."""
        sample_job.status = JobStatus.COMPLETED
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_job
        mock_db.execute.return_value = mock_result

        cancelled = await service.cancel_job(1)

        assert cancelled is False

    @pytest.mark.asyncio
    async def test_cancel_job_not_found(self, service, mock_db):
        """Test cancelling non-existent job."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        cancelled = await service.cancel_job(99999)

        assert cancelled is False

    @pytest.mark.asyncio
    async def test_delete_job(self, service, sample_job, mock_db):
        """Test deleting a job."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_job
        mock_db.execute.return_value = mock_result

        deleted = await service.delete_job(1)

        assert deleted is True
        assert mock_db.delete.called
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_delete_job_not_found(self, service, mock_db):
        """Test deleting non-existent job."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        deleted = await service.delete_job(99999)

        assert deleted is False

    @pytest.mark.asyncio
    async def test_get_job_stats(self, service, mock_db):
        """Test getting job statistics."""
        # Mock the query result to return tuples of (status, count)
        mock_result = MagicMock()
        mock_result.__iter__.return_value = iter(
            [
                (JobStatus.PENDING, 1),
                (JobStatus.RUNNING, 1),
                (JobStatus.COMPLETED, 1),
                (JobStatus.FAILED, 1),
            ]
        )
        mock_db.execute.return_value = mock_result

        stats = await service.get_job_stats()

        assert stats["total"] == 4
        assert stats["pending"] == 1
        assert stats["running"] == 1
        assert stats["completed"] == 1
        assert stats["failed"] == 1
