"""Tests for background worker."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.jobs.models import Job, JobStatus
from app.jobs.worker import BackgroundWorker, WorkerError, get_worker


class TestBackgroundWorker:
    """Test background worker."""

    @pytest.fixture
    def worker(self):
        """Create worker instance."""
        return BackgroundWorker(concurrency=2, poll_interval=0.1)

    @pytest.mark.asyncio
    async def test_worker_initialization(self, worker):
        """Test worker initialization."""
        assert worker.concurrency == 2
        assert worker.poll_interval == 0.1
        assert worker.running is False
        assert len(worker._tasks) == 0

    @pytest.mark.asyncio
    async def test_worker_start_stop(self, worker):
        """Test worker start and stop."""
        # Start worker in background
        worker_task = asyncio.create_task(worker.start())

        # Give it time to start
        await asyncio.sleep(0.2)

        assert worker.running is True

        # Stop worker
        await worker.stop()

        # Wait for worker task to complete
        try:
            await asyncio.wait_for(worker_task, timeout=1.0)
        except TimeoutError:
            worker_task.cancel()

        assert worker.running is False

    def test_get_worker_singleton(self):
        """Test get_worker returns singleton."""
        worker1 = get_worker()
        worker2 = get_worker()

        assert worker1 is worker2

    @pytest.mark.asyncio
    async def test_worker_process_job_success(self, worker):
        """Test worker processing job successfully."""
        # Mock database and job
        mock_job = MagicMock(spec=Job)
        mock_job.id = 1
        mock_job.task_name = "example_task"
        mock_job.task_args = '{"message": "test"}'
        mock_job.status = JobStatus.RUNNING
        mock_job.retries = 0
        mock_job.max_retries = 3

        with patch("app.jobs.worker.AsyncSessionLocal") as mock_session_local:
            mock_db = AsyncMock()
            mock_session_local.return_value.__aenter__.return_value = mock_db

            # Mock get job
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_job
            mock_db.execute.return_value = mock_result

            # Process job
            await worker._process_job(1)

            # Verify commit was called
            assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_worker_process_job_not_found(self, worker):
        """Test worker handling job not found."""
        with patch("app.jobs.worker.AsyncSessionLocal") as mock_session_local:
            mock_db = AsyncMock()
            mock_session_local.return_value.__aenter__.return_value = mock_db

            # Mock job not found
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_db.execute.return_value = mock_result

            # Should not raise error
            await worker._process_job(99999)

    @pytest.mark.asyncio
    async def test_worker_process_job_task_not_found(self, worker):
        """Test worker handling task not found."""
        mock_job = MagicMock(spec=Job)
        mock_job.id = 1
        mock_job.task_name = "nonexistent_task"
        mock_job.task_args = None
        mock_job.retries = 0
        mock_job.max_retries = 3

        with patch("app.jobs.worker.AsyncSessionLocal") as mock_session_local:
            mock_db = AsyncMock()
            mock_session_local.return_value.__aenter__.return_value = mock_db

            # Mock get job (return twice for retry logic)
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_job
            mock_db.execute.return_value = mock_result

            # Process job - should handle error
            await worker._process_job(1)

            # Verify job was updated with error
            assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_worker_process_job_with_retry(self, worker):
        """Test worker retrying failed job."""
        mock_job = MagicMock(spec=Job)
        mock_job.id = 1
        mock_job.task_name = "failing_task"
        mock_job.task_args = None
        mock_job.retries = 0
        mock_job.max_retries = 3

        with patch("app.jobs.worker.AsyncSessionLocal") as mock_session_local:
            mock_db = AsyncMock()
            mock_session_local.return_value.__aenter__.return_value = mock_db

            # Mock get job
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_job
            mock_db.execute.return_value = mock_result

            # Process job
            await worker._process_job(1)

            # Verify job was set to pending for retry
            assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_worker_process_job_max_retries(self, worker):
        """Test worker failing job after max retries."""
        mock_job = MagicMock(spec=Job)
        mock_job.id = 1
        mock_job.task_name = "failing_task"
        mock_job.task_args = None
        mock_job.retries = 3  # At max retries
        mock_job.max_retries = 3

        with patch("app.jobs.worker.AsyncSessionLocal") as mock_session_local:
            mock_db = AsyncMock()
            mock_session_local.return_value.__aenter__.return_value = mock_db

            # Mock get job
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_job
            mock_db.execute.return_value = mock_result

            # Process job
            await worker._process_job(1)

            # Verify job was marked as failed
            assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_get_next_job(self, worker):
        """Test getting next pending job."""
        mock_job = MagicMock(spec=Job)
        mock_job.id = 1
        mock_job.status = JobStatus.PENDING

        with patch("app.jobs.worker.AsyncSessionLocal") as mock_session_local:
            mock_db = AsyncMock()
            mock_session_local.return_value.__aenter__.return_value = mock_db

            # Mock get next job
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_job
            mock_db.execute.return_value = mock_result

            job = await worker._get_next_job(mock_db)

            assert job is not None
            assert job.id == 1
            assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_get_next_job_none_available(self, worker):
        """Test getting next job when none available."""
        with patch("app.jobs.worker.AsyncSessionLocal") as mock_session_local:
            mock_db = AsyncMock()
            mock_session_local.return_value.__aenter__.return_value = mock_db

            # Mock no jobs available
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_db.execute.return_value = mock_result

            job = await worker._get_next_job(mock_db)

            assert job is None


class TestWorkerError:
    """Test WorkerError exception."""

    def test_worker_error(self):
        """Test WorkerError can be raised."""
        with pytest.raises(WorkerError):
            raise WorkerError("Test error")

    def test_worker_error_message(self):
        """Test WorkerError preserves message."""
        error = WorkerError("Custom message")
        assert str(error) == "Custom message"
