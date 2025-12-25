"""Pydantic schemas for background jobs."""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.jobs.models import JobStatus, JobType


class JobCreate(BaseModel):
    """Schema for creating a new job."""

    job_type: JobType
    task_name: str = Field(..., min_length=1, max_length=255)
    task_args: str | None = Field(None, description="JSON string of task arguments")
    max_retries: int = Field(default=3, ge=0, le=10)


class JobUpdate(BaseModel):
    """Schema for updating job status."""

    status: JobStatus | None = None
    progress: int | None = Field(None, ge=0, le=100)
    result: str | None = None
    error: str | None = None

    @field_validator("progress")
    @classmethod
    def validate_progress(cls, v: int | None) -> int | None:
        """Validate progress is between 0 and 100."""
        if v is not None and (v < 0 or v > 100):
            raise ValueError("Progress must be between 0 and 100")
        return v


class JobSchema(BaseModel):
    """Schema for job response."""

    id: int
    job_type: JobType
    status: JobStatus
    task_name: str
    task_args: str | None
    result: str | None
    error: str | None
    started_at: datetime | None
    completed_at: datetime | None
    progress: int
    retries: int
    max_retries: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class JobSummary(BaseModel):
    """Lightweight job summary schema."""

    id: int
    job_type: JobType
    status: JobStatus
    task_name: str
    progress: int
    created_at: datetime

    model_config = {"from_attributes": True}
