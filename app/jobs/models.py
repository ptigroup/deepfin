"""Database models for background job tracking."""

import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.shared.models import TimestampMixin


class JobStatus(enum.Enum):
    """Job status enum."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobType(enum.Enum):
    """Job type enum."""

    EXTRACTION = "extraction"
    CONSOLIDATION = "consolidation"
    EXPORT = "export"
    CUSTOM = "custom"


class Job(Base, TimestampMixin):
    """Background job tracking model."""

    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    job_type: Mapped[JobType] = mapped_column(Enum(JobType), nullable=False)
    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus),
        nullable=False,
        default=JobStatus.PENDING,
        index=True,
    )
    task_name: Mapped[str] = mapped_column(String(255), nullable=False)
    task_args: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON string
    result: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON string
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    progress: Mapped[int] = mapped_column(Integer, default=0)  # 0-100
    retries: Mapped[int] = mapped_column(Integer, default=0)
    max_retries: Mapped[int] = mapped_column(Integer, default=3)

    def __repr__(self) -> str:
        """String representation."""
        return f"<Job(id={self.id}, type={self.job_type.value}, status={self.status.value})>"
