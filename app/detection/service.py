"""Business logic for table detection service."""

import json
import logging
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.detection.detector import PDFTableDetector
from app.detection.models import DetectionResult, DetectionStatus, Document, DocumentStatus
from app.detection.schemas import DocumentCreate

logger = logging.getLogger(__name__)


class DetectionService:
    """Service for managing document detection."""

    def __init__(self, db_session: AsyncSession):
        """
        Initialize detection service.

        Args:
            db_session: Async database session
        """
        self.db = db_session
        self.detector = PDFTableDetector()

    async def create_document(self, doc_data: DocumentCreate) -> Document:
        """
        Create a new document record.

        Args:
            doc_data: Document creation data

        Returns:
            Created document
        """
        document = Document(
            filename=doc_data.filename,
            file_path=doc_data.file_path,
            file_size=doc_data.file_size,
            mime_type=doc_data.mime_type,
            status=DocumentStatus.PENDING,
        )

        self.db.add(document)
        await self.db.commit()
        await self.db.refresh(document)

        logger.info(f"Created document: {document.id} - {document.filename}")
        return document

    async def get_document(self, document_id: int, with_results: bool = False) -> Document | None:
        """
        Get document by ID.

        Args:
            document_id: Document ID
            with_results: Whether to load detection results

        Returns:
            Document if found, None otherwise
        """
        query = select(Document).where(Document.id == document_id)

        if with_results:
            query = query.options(selectinload(Document.detection_results))

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_documents(
        self,
        status: DocumentStatus | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Document]:
        """
        Get list of documents.

        Args:
            status: Filter by status
            limit: Maximum number of documents
            offset: Number of documents to skip

        Returns:
            List of documents
        """
        query = select(Document)

        if status:
            query = query.where(Document.status == status)

        query = query.limit(limit).offset(offset).order_by(Document.created_at.desc())

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_document_status(
        self,
        document_id: int,
        status: DocumentStatus,
        error_message: str | None = None,
    ) -> Document | None:
        """
        Update document status.

        Args:
            document_id: Document ID
            status: New status
            error_message: Optional error message

        Returns:
            Updated document if found
        """
        document = await self.get_document(document_id)
        if not document:
            return None

        document.status = status
        if error_message:
            document.error_message = error_message

        await self.db.commit()
        await self.db.refresh(document)

        logger.info(f"Updated document {document_id} status to {status.value}")
        return document

    async def process_document(self, document_id: int) -> Document | None:
        """
        Process a document for table detection.

        Args:
            document_id: Document ID

        Returns:
            Processed document with detection results
        """
        # Get document
        document = await self.get_document(document_id)
        if not document:
            logger.error(f"Document not found: {document_id}")
            return None

        # Update status to processing
        document.status = DocumentStatus.PROCESSING
        await self.db.commit()

        try:
            # Check file exists
            file_path = Path(document.file_path)
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")

            # Detect tables using PyMuPDF
            logger.info(f"Starting detection for document {document_id}")
            results = self.detector.detect_tables(file_path)

            # Save detection results to database
            for page_result in results:
                # Convert bounding boxes to JSON
                bounding_boxes_json = json.dumps(
                    [bb.to_dict() for bb in page_result.bounding_boxes]
                )

                # Determine status based on table count
                if page_result.table_count > 0:
                    status = DetectionStatus.DETECTED
                else:
                    status = DetectionStatus.NO_TABLES

                detection_result = DetectionResult(
                    document_id=document_id,
                    page_number=page_result.page_number,
                    table_count=page_result.table_count,
                    status=status,
                    confidence_score=page_result.confidence_score,
                    bounding_boxes=bounding_boxes_json,
                )

                self.db.add(detection_result)

            # Update document status to completed
            document.status = DocumentStatus.COMPLETED
            await self.db.commit()
            await self.db.refresh(document, attribute_names=["detection_results"])

            logger.info(
                f"Completed detection for document {document_id}: {len(results)} pages processed"
            )

            return document

        except Exception as e:
            logger.error(f"Error processing document {document_id}: {e}")

            # Update document status to failed
            document.status = DocumentStatus.FAILED
            document.error_message = str(e)
            await self.db.commit()

            return document

    async def get_detection_results(
        self,
        document_id: int,
    ) -> list[DetectionResult]:
        """
        Get all detection results for a document.

        Args:
            document_id: Document ID

        Returns:
            List of detection results
        """
        query = (
            select(DetectionResult)
            .where(DetectionResult.document_id == document_id)
            .order_by(DetectionResult.page_number)
        )

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def delete_document(self, document_id: int) -> bool:
        """
        Delete a document and its detection results.

        Args:
            document_id: Document ID

        Returns:
            True if deleted, False if not found
        """
        document = await self.get_document(document_id)
        if not document:
            return False

        await self.db.delete(document)
        await self.db.commit()

        logger.info(f"Deleted document {document_id}")
        return True
