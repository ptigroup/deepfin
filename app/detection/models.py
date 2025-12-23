"""Database models for table detection."""

import enum

from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.shared.models import TimestampMixin


class DocumentStatus(str, enum.Enum):
    """Status of document processing."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class DetectionStatus(str, enum.Enum):
    """Status of table detection."""

    PENDING = "pending"
    DETECTED = "detected"
    NO_TABLES = "no_tables"
    FAILED = "failed"


class Document(Base, TimestampMixin):
    """Document uploaded for processing."""

    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size: Mapped[int] = mapped_column(nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[DocumentStatus] = mapped_column(
        Enum(DocumentStatus), default=DocumentStatus.PENDING, nullable=False
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    detection_results: Mapped[list["DetectionResult"]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<Document(id={self.id}, filename='{self.filename}', status='{self.status.value}')>"


class DetectionResult(Base, TimestampMixin):
    """Table detection result for a document."""

    __tablename__ = "detection_results"

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), nullable=False
    )
    page_number: Mapped[int] = mapped_column(nullable=False)
    table_count: Mapped[int] = mapped_column(default=0, nullable=False)
    status: Mapped[DetectionStatus] = mapped_column(
        Enum(DetectionStatus), default=DetectionStatus.PENDING, nullable=False
    )
    confidence_score: Mapped[float | None] = mapped_column(nullable=True)
    bounding_boxes: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON stored as text
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    document: Mapped["Document"] = relationship(back_populates="detection_results")

    def __repr__(self) -> str:
        """String representation."""
        return f"<DetectionResult(id={self.id}, document_id={self.document_id}, page={self.page_number}, tables={self.table_count})>"
