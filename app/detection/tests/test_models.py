"""Tests for detection models."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.detection.models import DetectionResult, DetectionStatus, Document, DocumentStatus
from app.detection.schemas import (
    DetectionResultCreate,
    DetectionResultSchema,
    DocumentCreate,
    DocumentSchema,
    DocumentWithResults,
)


class TestDocumentModel:
    """Tests for Document model."""

    def test_document_creation(self):
        """Test creating a document."""
        doc = Document(
            filename="test.pdf",
            file_path="/uploads/test.pdf",
            file_size=1024,
            mime_type="application/pdf",
            status=DocumentStatus.PENDING,
        )
        assert doc.filename == "test.pdf"
        assert doc.file_path == "/uploads/test.pdf"
        assert doc.file_size == 1024
        assert doc.mime_type == "application/pdf"
        assert doc.status == DocumentStatus.PENDING
        assert doc.error_message is None

    def test_document_repr(self):
        """Test document string representation."""
        doc = Document(
            filename="test.pdf",
            file_path="/uploads/test.pdf",
            file_size=1024,
            mime_type="application/pdf",
            status=DocumentStatus.PENDING,
        )
        doc.id = 1
        repr_str = repr(doc)
        assert "Document" in repr_str
        assert "id=1" in repr_str
        assert "test.pdf" in repr_str
        assert "pending" in repr_str


class TestDetectionResultModel:
    """Tests for DetectionResult model."""

    def test_detection_result_creation(self):
        """Test creating a detection result."""
        result = DetectionResult(
            document_id=1,
            page_number=1,
            table_count=2,
            status=DetectionStatus.DETECTED,
            confidence_score=0.95,
        )
        assert result.document_id == 1
        assert result.page_number == 1
        assert result.table_count == 2
        assert result.status == DetectionStatus.DETECTED
        assert result.confidence_score == 0.95
        assert result.bounding_boxes is None
        assert result.error_message is None

    def test_detection_result_repr(self):
        """Test detection result string representation."""
        result = DetectionResult(
            document_id=1,
            page_number=2,
            table_count=3,
        )
        result.id = 5
        repr_str = repr(result)
        assert "DetectionResult" in repr_str
        assert "id=5" in repr_str
        assert "document_id=1" in repr_str
        assert "page=2" in repr_str
        assert "tables=3" in repr_str


class TestDocumentSchema:
    """Tests for Document Pydantic schemas."""

    def test_document_create_valid(self):
        """Test creating a valid document."""
        doc = DocumentCreate(
            filename="test.pdf",
            file_path="/uploads/test.pdf",
            file_size=1024,
            mime_type="application/pdf",
        )
        assert doc.filename == "test.pdf"
        assert doc.file_size == 1024

    def test_document_create_invalid_mime_type(self):
        """Test creating a document with invalid mime type."""
        with pytest.raises(ValidationError) as exc_info:
            DocumentCreate(
                filename="test.txt",
                file_path="/uploads/test.txt",
                file_size=1024,
                mime_type="text/plain",
            )
        assert "mime_type" in str(exc_info.value)

    def test_document_create_invalid_file_size(self):
        """Test creating a document with invalid file size."""
        with pytest.raises(ValidationError) as exc_info:
            DocumentCreate(
                filename="test.pdf",
                file_path="/uploads/test.pdf",
                file_size=0,
                mime_type="application/pdf",
            )
        assert "file_size" in str(exc_info.value)

    def test_document_schema_from_model(self):
        """Test creating schema from model."""
        now = datetime.now(UTC)
        doc = Document(
            filename="test.pdf",
            file_path="/uploads/test.pdf",
            file_size=1024,
            mime_type="application/pdf",
            status=DocumentStatus.PENDING,
        )
        doc.id = 1
        doc.created_at = now
        doc.updated_at = now
        schema = DocumentSchema.model_validate(doc)
        assert schema.id == 1
        assert schema.filename == "test.pdf"


class TestDetectionResultSchema:
    """Tests for DetectionResult Pydantic schemas."""

    def test_detection_result_create_valid(self):
        """Test creating a valid detection result."""
        result = DetectionResultCreate(
            document_id=1,
            page_number=1,
            table_count=2,
            confidence_score=0.95,
        )
        assert result.document_id == 1
        assert result.page_number == 1
        assert result.table_count == 2
        assert result.confidence_score == 0.95

    def test_detection_result_create_invalid_confidence(self):
        """Test creating detection result with invalid confidence score."""
        with pytest.raises(ValidationError) as exc_info:
            DetectionResultCreate(document_id=1, page_number=1, table_count=2, confidence_score=1.5)
        assert "confidence_score" in str(exc_info.value)

    def test_detection_result_create_negative_table_count(self):
        """Test creating detection result with negative table count."""
        with pytest.raises(ValidationError) as exc_info:
            DetectionResultCreate(document_id=1, page_number=1, table_count=-1)
        assert "table_count" in str(exc_info.value)

    def test_detection_result_schema_from_model(self):
        """Test creating schema from model."""
        now = datetime.now(UTC)
        result = DetectionResult(
            document_id=1,
            page_number=1,
            table_count=2,
            status=DetectionStatus.DETECTED,
            confidence_score=0.95,
        )
        result.id = 1
        result.created_at = now
        result.updated_at = now
        schema = DetectionResultSchema.model_validate(result)
        assert schema.id == 1
        assert schema.document_id == 1
        assert schema.table_count == 2
        assert schema.status == DetectionStatus.DETECTED

    def test_document_with_results(self):
        """Test document with nested detection results."""
        now = datetime.now(UTC)
        doc = Document(
            filename="test.pdf",
            file_path="/uploads/test.pdf",
            file_size=1024,
            mime_type="application/pdf",
            status=DocumentStatus.PENDING,
        )
        doc.id = 1
        doc.created_at = now
        doc.updated_at = now
        doc.detection_results = [
            DetectionResult(
                document_id=1,
                page_number=1,
                table_count=2,
                status=DetectionStatus.DETECTED,
            )
        ]
        doc.detection_results[0].id = 1
        doc.detection_results[0].created_at = now
        doc.detection_results[0].updated_at = now

        schema = DocumentWithResults.model_validate(doc)
        assert schema.id == 1
        assert len(schema.detection_results) == 1
        assert schema.detection_results[0].page_number == 1
