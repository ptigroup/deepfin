"""Pydantic schemas for table detection."""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.detection.models import DetectionStatus, DocumentStatus
from app.shared.schemas import BaseResponse


class DocumentCreate(BaseModel):
    """Schema for creating a document."""

    filename: str = Field(..., min_length=1, max_length=255)
    file_path: str = Field(..., min_length=1, max_length=500)
    file_size: int = Field(..., gt=0)
    mime_type: str = Field(..., min_length=1, max_length=100)

    @field_validator("mime_type")
    @classmethod
    def validate_mime_type(cls, v: str) -> str:
        """Validate that mime_type is PDF."""
        allowed_types = ["application/pdf"]
        if v not in allowed_types:
            raise ValueError(f"mime_type must be one of {allowed_types}")
        return v


class DocumentUpdate(BaseModel):
    """Schema for updating a document."""

    status: DocumentStatus | None = None
    error_message: str | None = None


class DocumentSchema(BaseModel):
    """Schema for document response."""

    id: int
    filename: str
    file_path: str
    file_size: int
    mime_type: str
    status: DocumentStatus
    error_message: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DetectionResultCreate(BaseModel):
    """Schema for creating a detection result."""

    document_id: int = Field(..., gt=0)
    page_number: int = Field(..., gt=0)
    table_count: int = Field(default=0, ge=0)
    confidence_score: float | None = Field(None, ge=0.0, le=1.0)
    bounding_boxes: str | None = None

    @field_validator("confidence_score")
    @classmethod
    def validate_confidence(cls, v: float | None) -> float | None:
        """Validate confidence score is between 0 and 1."""
        if v is not None and not 0.0 <= v <= 1.0:
            raise ValueError("confidence_score must be between 0.0 and 1.0")
        return v


class DetectionResultUpdate(BaseModel):
    """Schema for updating a detection result."""

    status: DetectionStatus | None = None
    table_count: int | None = Field(None, ge=0)
    confidence_score: float | None = Field(None, ge=0.0, le=1.0)
    bounding_boxes: str | None = None
    error_message: str | None = None


class DetectionResultSchema(BaseModel):
    """Schema for detection result response."""

    id: int
    document_id: int
    page_number: int
    table_count: int
    status: DetectionStatus
    confidence_score: float | None
    bounding_boxes: str | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DocumentWithResults(DocumentSchema):
    """Schema for document with detection results."""

    detection_results: list[DetectionResultSchema] = []

    model_config = {"from_attributes": True}


class DocumentResponse(BaseResponse):
    """Response schema for document."""

    data: DocumentSchema


class DocumentListResponse(BaseResponse):
    """Response schema for list of documents."""

    data: list[DocumentSchema]
    total: int = 0


class DetectionResultResponse(BaseResponse):
    """Response schema for detection result."""

    data: DetectionResultSchema


class DetectionResultListResponse(BaseResponse):
    """Response schema for list of detection results."""

    data: list[DetectionResultSchema]
    total: int = 0
