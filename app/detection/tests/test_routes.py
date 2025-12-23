"""Tests for detection API routes."""

import tempfile
from datetime import UTC, datetime
from io import BytesIO
from pathlib import Path
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.detection.models import Document, DocumentStatus
from app.main import app

client = TestClient(app)


class TestUploadEndpoint:
    """Tests for document upload endpoint."""

    def test_upload_pdf_success(self):
        """Test successful PDF upload."""
        # Create a mock PDF file
        pdf_content = b"%PDF-1.4 mock content"
        files = {"file": ("test.pdf", BytesIO(pdf_content), "application/pdf")}

        with patch("app.detection.routes.DetectionService") as mock_service:
            now = datetime.now(UTC)
            mock_doc = Document(
                id=1,
                filename="test.pdf",
                file_path="/uploads/test.pdf",
                file_size=len(pdf_content),
                mime_type="application/pdf",
                status=DocumentStatus.PENDING,
            )
            mock_doc.created_at = now
            mock_doc.updated_at = now

            mock_service_instance = AsyncMock()
            mock_service_instance.create_document = AsyncMock(return_value=mock_doc)
            mock_service.return_value = mock_service_instance

            response = client.post("/detection/upload", files=files)

            assert response.status_code == 201
            data = response.json()
            assert data["success"] is True
            assert "test.pdf" in data["message"]

    def test_upload_invalid_file_type(self):
        """Test upload with invalid file type."""
        # Create a mock text file
        files = {"file": ("test.txt", BytesIO(b"text content"), "text/plain")}

        response = client.post("/detection/upload", files=files)

        assert response.status_code == 400
        data = response.json()
        assert "invalid file type" in data["detail"].lower()

    def test_upload_empty_file(self):
        """Test upload with empty file."""
        files = {"file": ("test.pdf", BytesIO(b""), "application/pdf")}

        response = client.post("/detection/upload", files=files)

        assert response.status_code == 400
        data = response.json()
        assert "empty" in data["detail"].lower()

    def test_upload_no_filename(self):
        """Test upload with no filename."""
        files = {"file": ("", BytesIO(b"content"), "application/pdf")}

        response = client.post("/detection/upload", files=files)

        # FastAPI returns 422 for validation errors
        assert response.status_code in [400, 422]

    def test_upload_file_too_large(self):
        """Test upload with file exceeding size limit."""
        # Create a file larger than 10 MB
        large_content = b"x" * (11 * 1024 * 1024)
        files = {"file": ("large.pdf", BytesIO(large_content), "application/pdf")}

        response = client.post("/detection/upload", files=files)

        assert response.status_code == 413
        data = response.json()
        assert "too large" in data["detail"].lower()


class TestProcessEndpoint:
    """Tests for document processing endpoint."""

    def test_process_document_success(self):
        """Test successful document processing."""
        with patch("app.detection.routes.DetectionService") as mock_service:
            now = datetime.now(UTC)
            mock_doc = Document(
                id=1,
                filename="test.pdf",
                file_path="/uploads/test.pdf",
                file_size=1024,
                mime_type="application/pdf",
                status=DocumentStatus.COMPLETED,
            )
            mock_doc.created_at = now
            mock_doc.updated_at = now

            mock_service_instance = AsyncMock()
            mock_service_instance.get_document = AsyncMock(return_value=mock_doc)
            mock_service_instance.process_document = AsyncMock(return_value=mock_doc)
            mock_service.return_value = mock_service_instance

            response = client.post("/detection/documents/1/process")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "completed" in data["message"].lower()

    def test_process_document_not_found(self):
        """Test processing non-existent document."""
        with patch("app.detection.routes.DetectionService") as mock_service:
            mock_service_instance = AsyncMock()
            mock_service_instance.get_document = AsyncMock(return_value=None)
            mock_service.return_value = mock_service_instance

            response = client.post("/detection/documents/999/process")

            assert response.status_code == 404
            data = response.json()
            assert "not found" in data["detail"].lower()

    def test_process_document_already_processing(self):
        """Test processing document that is already being processed."""
        with patch("app.detection.routes.DetectionService") as mock_service:
            mock_doc = Document(
                id=1,
                filename="test.pdf",
                file_path="/uploads/test.pdf",
                file_size=1024,
                mime_type="application/pdf",
                status=DocumentStatus.PROCESSING,
            )

            mock_service_instance = AsyncMock()
            mock_service_instance.get_document = AsyncMock(return_value=mock_doc)
            mock_service.return_value = mock_service_instance

            response = client.post("/detection/documents/1/process")

            assert response.status_code == 409
            data = response.json()
            assert "already being processed" in data["detail"].lower()


class TestListDocumentsEndpoint:
    """Tests for listing documents endpoint."""

    def test_list_documents_success(self):
        """Test successful document listing."""
        with patch("app.detection.routes.DetectionService") as mock_service:
            now = datetime.now(UTC)
            mock_doc1 = Document(
                id=1,
                filename="test1.pdf",
                file_path="/uploads/test1.pdf",
                file_size=1024,
                mime_type="application/pdf",
                status=DocumentStatus.COMPLETED,
            )
            mock_doc1.created_at = now
            mock_doc1.updated_at = now

            mock_doc2 = Document(
                id=2,
                filename="test2.pdf",
                file_path="/uploads/test2.pdf",
                file_size=2048,
                mime_type="application/pdf",
                status=DocumentStatus.PENDING,
            )
            mock_doc2.created_at = now
            mock_doc2.updated_at = now

            mock_docs = [mock_doc1, mock_doc2]

            mock_service_instance = AsyncMock()
            mock_service_instance.get_documents = AsyncMock(return_value=mock_docs)
            mock_service.return_value = mock_service_instance

            response = client.get("/detection/documents")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["total"] == 2
            assert len(data["data"]) == 2

    def test_list_documents_with_status_filter(self):
        """Test listing documents with status filter."""
        with patch("app.detection.routes.DetectionService") as mock_service:
            now = datetime.now(UTC)
            mock_doc = Document(
                id=1,
                filename="test1.pdf",
                file_path="/uploads/test1.pdf",
                file_size=1024,
                mime_type="application/pdf",
                status=DocumentStatus.COMPLETED,
            )
            mock_doc.created_at = now
            mock_doc.updated_at = now

            mock_docs = [mock_doc]

            mock_service_instance = AsyncMock()
            mock_service_instance.get_documents = AsyncMock(return_value=mock_docs)
            mock_service.return_value = mock_service_instance

            response = client.get("/detection/documents?status_filter=completed")

            assert response.status_code == 200
            data = response.json()
            assert data["total"] == 1

    def test_list_documents_empty(self):
        """Test listing documents when none exist."""
        with patch("app.detection.routes.DetectionService") as mock_service:
            mock_service_instance = AsyncMock()
            mock_service_instance.get_documents = AsyncMock(return_value=[])
            mock_service.return_value = mock_service_instance

            response = client.get("/detection/documents")

            assert response.status_code == 200
            data = response.json()
            assert data["total"] == 0
            assert len(data["data"]) == 0


class TestGetDocumentEndpoint:
    """Tests for getting single document endpoint."""

    def test_get_document_success(self):
        """Test successful document retrieval."""
        with patch("app.detection.routes.DetectionService") as mock_service:
            now = datetime.now(UTC)
            mock_doc = Document(
                id=1,
                filename="test.pdf",
                file_path="/uploads/test.pdf",
                file_size=1024,
                mime_type="application/pdf",
                status=DocumentStatus.COMPLETED,
            )
            mock_doc.created_at = now
            mock_doc.updated_at = now

            mock_service_instance = AsyncMock()
            mock_service_instance.get_document = AsyncMock(return_value=mock_doc)
            mock_service.return_value = mock_service_instance

            response = client.get("/detection/documents/1")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["id"] == 1
            assert data["data"]["filename"] == "test.pdf"

    def test_get_document_not_found(self):
        """Test getting non-existent document."""
        with patch("app.detection.routes.DetectionService") as mock_service:
            mock_service_instance = AsyncMock()
            mock_service_instance.get_document = AsyncMock(return_value=None)
            mock_service.return_value = mock_service_instance

            response = client.get("/detection/documents/999")

            assert response.status_code == 404
            data = response.json()
            assert "not found" in data["detail"].lower()


class TestDeleteDocumentEndpoint:
    """Tests for deleting document endpoint."""

    def test_delete_document_success(self):
        """Test successful document deletion."""
        with patch("app.detection.routes.DetectionService") as mock_service:
            # Create temp file
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
                temp_path = f.name

            try:
                mock_doc = Document(
                    id=1,
                    filename="test.pdf",
                    file_path=temp_path,
                    file_size=1024,
                    mime_type="application/pdf",
                    status=DocumentStatus.COMPLETED,
                )

                mock_service_instance = AsyncMock()
                mock_service_instance.get_document = AsyncMock(return_value=mock_doc)
                mock_service_instance.delete_document = AsyncMock(return_value=True)
                mock_service.return_value = mock_service_instance

                response = client.delete("/detection/documents/1")

                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
                assert "deleted" in data["message"].lower()
            finally:
                # Clean up temp file if it still exists
                if Path(temp_path).exists():
                    Path(temp_path).unlink()

    def test_delete_document_not_found(self):
        """Test deleting non-existent document."""
        with patch("app.detection.routes.DetectionService") as mock_service:
            mock_service_instance = AsyncMock()
            mock_service_instance.get_document = AsyncMock(return_value=None)
            mock_service.return_value = mock_service_instance

            response = client.delete("/detection/documents/999")

            assert response.status_code == 404
            data = response.json()
            assert "not found" in data["detail"].lower()
