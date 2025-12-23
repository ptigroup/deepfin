"""Tests for detection service."""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.detection.detector import PageDetectionResult, TableBoundingBox
from app.detection.models import Document, DocumentStatus
from app.detection.schemas import DocumentCreate
from app.detection.service import DetectionService


@pytest.fixture
def mock_db_session():
    """Mock database session."""
    session = AsyncMock(spec=AsyncSession)
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.add = MagicMock()
    session.delete = AsyncMock()
    return session


@pytest.fixture
def detection_service(mock_db_session):
    """Create detection service with mocked database."""
    return DetectionService(mock_db_session)


class TestDetectionService:
    """Tests for DetectionService."""

    @pytest.mark.asyncio
    async def test_create_document(self, detection_service, mock_db_session):
        """Test creating a document."""
        doc_data = DocumentCreate(
            filename="test.pdf",
            file_path="/uploads/test.pdf",
            file_size=1024,
            mime_type="application/pdf",
        )

        # Mock refresh to set document id
        async def mock_refresh(doc):
            doc.id = 1

        mock_db_session.refresh.side_effect = mock_refresh

        document = await detection_service.create_document(doc_data)

        assert document.filename == "test.pdf"
        assert document.file_path == "/uploads/test.pdf"
        assert document.status == DocumentStatus.PENDING
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_document(self, detection_service, mock_db_session):
        """Test getting a document by ID."""
        mock_doc = Document(
            id=1,
            filename="test.pdf",
            file_path="/uploads/test.pdf",
            file_size=1024,
            mime_type="application/pdf",
            status=DocumentStatus.PENDING,
        )

        # Mock database query result
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_doc
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        document = await detection_service.get_document(1)

        assert document is not None
        assert document.id == 1
        assert document.filename == "test.pdf"
        mock_db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_document_not_found(self, detection_service, mock_db_session):
        """Test getting a non-existent document."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        document = await detection_service.get_document(999)

        assert document is None

    @pytest.mark.asyncio
    async def test_get_documents(self, detection_service, mock_db_session):
        """Test getting list of documents."""
        mock_docs = [
            Document(
                id=1,
                filename="test1.pdf",
                file_path="/uploads/test1.pdf",
                file_size=1024,
                mime_type="application/pdf",
                status=DocumentStatus.COMPLETED,
            ),
            Document(
                id=2,
                filename="test2.pdf",
                file_path="/uploads/test2.pdf",
                file_size=2048,
                mime_type="application/pdf",
                status=DocumentStatus.COMPLETED,
            ),
        ]

        mock_scalars = MagicMock()
        mock_scalars.all.return_value = mock_docs
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        documents = await detection_service.get_documents(
            status=DocumentStatus.COMPLETED,
            limit=10,
            offset=0,
        )

        assert len(documents) == 2
        assert documents[0].id == 1
        assert documents[1].id == 2

    @pytest.mark.asyncio
    async def test_update_document_status(self, detection_service, mock_db_session):
        """Test updating document status."""
        mock_doc = Document(
            id=1,
            filename="test.pdf",
            file_path="/uploads/test.pdf",
            file_size=1024,
            mime_type="application/pdf",
            status=DocumentStatus.PENDING,
        )

        # Mock get_document
        async def mock_get_document(_id):
            return mock_doc

        detection_service.get_document = mock_get_document

        updated_doc = await detection_service.update_document_status(
            1,
            DocumentStatus.PROCESSING,
        )

        assert updated_doc.status == DocumentStatus.PROCESSING
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_document_status_not_found(self, detection_service, mock_db_session):
        """Test updating status of non-existent document."""

        # Mock get_document to return None
        async def mock_get_document(_id):
            return None

        detection_service.get_document = mock_get_document

        updated_doc = await detection_service.update_document_status(
            999,
            DocumentStatus.PROCESSING,
        )

        assert updated_doc is None

    @pytest.mark.asyncio
    async def test_delete_document(self, detection_service, mock_db_session):
        """Test deleting a document."""
        mock_doc = Document(
            id=1,
            filename="test.pdf",
            file_path="/uploads/test.pdf",
            file_size=1024,
            mime_type="application/pdf",
            status=DocumentStatus.COMPLETED,
        )

        # Mock get_document
        async def mock_get_document(_id):
            return mock_doc

        detection_service.get_document = mock_get_document

        result = await detection_service.delete_document(1)

        assert result is True
        mock_db_session.delete.assert_called_once()
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_document_not_found(self, detection_service, mock_db_session):
        """Test deleting a non-existent document."""

        # Mock get_document to return None
        async def mock_get_document(_id):
            return None

        detection_service.get_document = mock_get_document

        result = await detection_service.delete_document(999)

        assert result is False

    @pytest.mark.asyncio
    @patch("app.detection.service.PDFTableDetector")
    async def test_process_document_success(
        self,
        mock_detector_class,
        detection_service,
        mock_db_session,
    ):
        """Test successful document processing."""
        # Create mock document
        mock_doc = Document(
            id=1,
            filename="test.pdf",
            file_path="test.pdf",
            file_size=1024,
            mime_type="application/pdf",
            status=DocumentStatus.PENDING,
        )

        # Mock get_document
        async def mock_get_document(_id, with_results=False):
            return mock_doc

        detection_service.get_document = mock_get_document

        # Mock detector results
        bb = TableBoundingBox(page=1, x0=10.0, y0=20.0, x1=100.0, y1=200.0, confidence=0.9)
        page_result = PageDetectionResult(
            page_number=1,
            table_count=1,
            confidence_score=0.9,
            bounding_boxes=[bb],
        )

        mock_detector = MagicMock()
        mock_detector.detect_tables.return_value = [page_result]
        detection_service.detector = mock_detector

        # Create temporary file
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            temp_path = f.name

        try:
            mock_doc.file_path = temp_path

            result = await detection_service.process_document(1)

            assert result is not None
            assert result.status == DocumentStatus.COMPLETED
            mock_db_session.add.assert_called()
            assert mock_db_session.commit.call_count >= 2  # At least 2 commits
        finally:
            Path(temp_path).unlink()

    @pytest.mark.asyncio
    async def test_process_document_file_not_found(self, detection_service, mock_db_session):
        """Test processing document with missing file."""
        mock_doc = Document(
            id=1,
            filename="test.pdf",
            file_path="/nonexistent/test.pdf",
            file_size=1024,
            mime_type="application/pdf",
            status=DocumentStatus.PENDING,
        )

        # Mock get_document
        async def mock_get_document(_id, with_results=False):
            return mock_doc

        detection_service.get_document = mock_get_document

        result = await detection_service.process_document(1)

        assert result is not None
        assert result.status == DocumentStatus.FAILED
        assert result.error_message is not None

    @pytest.mark.asyncio
    async def test_process_document_not_found(self, detection_service):
        """Test processing non-existent document."""

        # Mock get_document to return None
        async def mock_get_document(_id):
            return None

        detection_service.get_document = mock_get_document

        result = await detection_service.process_document(999)

        assert result is None
