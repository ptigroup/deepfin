"""Pydantic schemas for LLMWhisperer API requests and responses."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class ProcessingMode(str, Enum):
    """LLMWhisperer processing modes."""

    TEXT = "text"
    FORM = "form"
    HIGH_QUALITY = "high_quality"


class WhisperRequest(BaseModel):
    """Request schema for LLMWhisperer API."""

    file_path: str = Field(..., description="Path to the PDF file to process")
    processing_mode: ProcessingMode = Field(
        default=ProcessingMode.TEXT,
        description="Processing mode for text extraction",
    )
    output_format: str = Field(
        default="text",
        description="Output format (text, markdown, json)",
    )
    page_separator: str = Field(
        default="<<<",
        description="Separator between pages in output",
    )
    force_text_processing: bool = Field(
        default=False,
        description="Force text processing even if text layer exists",
    )
    pages_to_extract: str | None = Field(
        default=None,
        description="Page range to extract (e.g., '1-5,8,10-12')",
    )


class WhisperResponse(BaseModel):
    """Response schema from LLMWhisperer API."""

    whisper_hash: str = Field(..., description="Unique hash for this extraction")
    extracted_text: str = Field(..., description="Extracted text content")
    status_code: int = Field(..., description="HTTP status code")
    processing_time: float = Field(..., description="Processing time in seconds")
    page_count: int | None = Field(None, description="Number of pages processed")


class CachedWhisperResult(BaseModel):
    """Schema for cached whisper results."""

    whisper_hash: str
    extracted_text: str
    file_path: str
    cached_at: datetime
    processing_mode: ProcessingMode
    page_count: int | None = None

    model_config = {"from_attributes": True}


class WhisperError(BaseModel):
    """Error response from LLMWhisperer API."""

    error: str = Field(..., description="Error message")
    status_code: int = Field(..., description="HTTP status code")
    whisper_hash: str | None = Field(None, description="Hash if available")
