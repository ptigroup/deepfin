"""Integration tests for job queue and background processing."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.integration
class TestJobCreation:
    """Test job creation and status tracking."""

    @pytest.mark.asyncio
    async def test_create_job_in_database(self, db_session: AsyncSession) -> None:
        """Test creating a job in the database."""
        from app.jobs.models import Job, JobStatus, JobType
        from app.jobs.service import JobService
        
        service = JobService(db_session)
        
        # Create job
        job = await service.create_job(
            task_type=JobType.EXTRACT_PDF,
            task_name="test_task",
            task_args={"file_path": "/tmp/test.pdf"},
        )
        
        assert job.id is not None
        assert job.task_type == JobType.EXTRACT_PDF
        assert job.status == JobStatus.PENDING
        assert job.task_name == "test_task"

    @pytest.mark.asyncio
    async def test_job_status_transitions(self, db_session: AsyncSession) -> None:
        """Test job status can be updated."""
        from app.jobs.models import JobStatus, JobType
        from app.jobs.service import JobService
        
        service = JobService(db_session)
        
        # Create job
        job = await service.create_job(
            task_type=JobType.EXTRACT_PDF,
            task_name="status_test",
            task_args={},
        )
        
        job_id = job.id
        assert job.status == JobStatus.PENDING
        
        # Start job
        updated = await service.update_job_status(
            job_id=job_id,
            status=JobStatus.RUNNING,
        )
        assert updated.status == JobStatus.RUNNING
        
        # Complete job
        completed = await service.update_job_status(
            job_id=job_id,
            status=JobStatus.COMPLETED,
        )
        assert completed.status == JobStatus.COMPLETED


@pytest.mark.integration
class TestJobAPI:
    """Test job API endpoints."""

    def test_list_jobs(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test listing jobs."""
        response = client.get("/jobs/", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert isinstance(data["items"], list)

    @pytest.mark.asyncio
    async def test_get_job_by_id(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        db_session: AsyncSession,
    ) -> None:
        """Test retrieving a specific job."""
        from app.jobs.models import JobType
        from app.jobs.service import JobService
        
        # Create job
        service = JobService(db_session)
        job = await service.create_job(
            task_type=JobType.EXTRACT_PDF,
            task_name="get_test",
            task_args={},
        )
        
        # Get job by ID
        response = client.get(
            f"/jobs/{job.id}",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == job.id
        assert data["task_name"] == "get_test"
