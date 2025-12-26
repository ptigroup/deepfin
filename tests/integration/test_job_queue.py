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
        import json
        from app.jobs.models import Job, JobStatus, JobType
        from app.jobs.schemas import JobCreate
        from app.jobs.service import JobService

        service = JobService(db_session)

        # Create job
        job_data = JobCreate(
            job_type=JobType.EXTRACTION,
            task_name="test_task",
            task_args=json.dumps({"file_path": "/tmp/test.pdf"}),
        )
        job = await service.create_job(job_data)

        assert job.id is not None
        assert job.job_type == JobType.EXTRACTION
        assert job.status == JobStatus.PENDING
        assert job.task_name == "test_task"

    @pytest.mark.asyncio
    async def test_job_status_transitions(self, db_session: AsyncSession) -> None:
        """Test job status can be updated."""
        import json
        from app.jobs.models import JobStatus, JobType
        from app.jobs.schemas import JobCreate
        from app.jobs.service import JobService

        service = JobService(db_session)

        # Create job
        job_data = JobCreate(
            job_type=JobType.EXTRACTION,
            task_name="status_test",
            task_args=json.dumps({}),
        )
        job = await service.create_job(job_data)
        
        job_id = job.id
        assert job.status == JobStatus.PENDING

        # Start job
        from app.jobs.schemas import JobUpdate

        job_update = JobUpdate(status=JobStatus.RUNNING)
        updated = await service.update_job(job_id=job_id, job_update=job_update)
        assert updated.status == JobStatus.RUNNING

        # Complete job
        job_update = JobUpdate(status=JobStatus.COMPLETED)
        completed = await service.update_job(job_id=job_id, job_update=job_update)
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
        assert data["success"] is True
        assert "data" in data
        assert isinstance(data["data"], list)

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
        import json
        from app.jobs.schemas import JobCreate

        service = JobService(db_session)
        job_data = JobCreate(
            job_type=JobType.EXTRACTION,
            task_name="get_test",
            task_args=json.dumps({}),
        )
        job = await service.create_job(job_data)
        
        # Get job by ID
        response = client.get(
            f"/jobs/{job.id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        response_data = response.json()
        assert response_data["success"] is True
        assert "data" in response_data
        job_data = response_data["data"]
        assert job_data["id"] == job.id
        assert job_data["task_name"] == "get_test"
