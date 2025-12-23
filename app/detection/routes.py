"""REST API endpoints for table detection."""

import logging
import os
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.detection.models import DocumentStatus
from app.detection.schemas import (
    DocumentCreate,
    DocumentListResponse,
    DocumentResponse,
)
from app.detection.service import DetectionService
from app.shared.schemas import BaseResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/detection", tags=["detection"])

# Upload directory configuration
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# File size limit (10 MB)
MAX_FILE_SIZE = 10 * 1024 * 1024


@router.post(
    "/upload",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload PDF for table detection",
)
async def upload_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
) -> DocumentResponse:
    """
    Upload a PDF document for table detection.

    Args:
        file: PDF file to upload
        db: Database session

    Returns:
        Created document record

    Raises:
        HTTPException: If file is invalid or upload fails
    """
    # Validate file type
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type: {file.content_type}. Only PDF files are allowed.",
        )

    # Validate filename
    if not file.filename or file.filename == "":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is required",
        )

    try:
        # Read file content
        content = await file.read()
        file_size = len(content)

        # Validate file size
        if file_size == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File is empty",
            )

        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Maximum size is {MAX_FILE_SIZE / 1024 / 1024:.0f} MB",
            )

        # Generate unique filename
        import uuid

        unique_id = uuid.uuid4().hex[:8]
        safe_filename = f"{unique_id}_{file.filename}"
        file_path = UPLOAD_DIR / safe_filename

        # Save file
        with open(file_path, "wb") as f:
            f.write(content)

        logger.info(f"Saved file: {file_path} ({file_size} bytes)")

        # Create document record
        service = DetectionService(db)
        doc_data = DocumentCreate(
            filename=file.filename,
            file_path=str(file_path),
            file_size=file_size,
            mime_type=file.content_type,
        )

        document = await service.create_document(doc_data)

        return DocumentResponse(
            success=True,
            message=f"Document uploaded successfully: {file.filename}",
            data=document,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file: {str(e)}",
        ) from e


@router.post(
    "/documents/{document_id}/process",
    response_model=DocumentResponse,
    summary="Process document for table detection",
)
async def process_document(
    document_id: int,
    db: AsyncSession = Depends(get_db),
) -> DocumentResponse:
    """
    Process a document for table detection.

    Args:
        document_id: Document ID to process
        db: Database session

    Returns:
        Processed document with detection results

    Raises:
        HTTPException: If document not found or processing fails
    """
    service = DetectionService(db)

    # Check document exists
    document = await service.get_document(document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document not found: {document_id}",
        )

    # Check if already processing
    if document.status == DocumentStatus.PROCESSING:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Document is already being processed",
        )

    # Process document
    try:
        processed_doc = await service.process_document(document_id)
        if not processed_doc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Processing failed",
            )

        # Reload with results
        document = await service.get_document(document_id, with_results=True)

        return DocumentResponse(
            success=True,
            message=f"Document processed successfully. Status: {document.status.value}",
            data=document,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing document {document_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Processing failed: {str(e)}",
        ) from e


@router.get(
    "/documents",
    response_model=DocumentListResponse,
    summary="List all documents",
)
async def list_documents(
    status_filter: DocumentStatus | None = None,
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
) -> DocumentListResponse:
    """
    Get list of all documents.

    Args:
        status_filter: Optional status filter
        limit: Maximum number of results (default 100)
        offset: Number of results to skip (default 0)
        db: Database session

    Returns:
        List of documents
    """
    service = DetectionService(db)
    documents = await service.get_documents(
        status=status_filter,
        limit=limit,
        offset=offset,
    )

    return DocumentListResponse(
        success=True,
        message=f"Found {len(documents)} documents",
        data=documents,
        total=len(documents),
    )


@router.get(
    "/documents/{document_id}",
    response_model=DocumentResponse,
    summary="Get document with detection results",
)
async def get_document(
    document_id: int,
    db: AsyncSession = Depends(get_db),
) -> DocumentResponse:
    """
    Get a specific document with its detection results.

    Args:
        document_id: Document ID
        db: Database session

    Returns:
        Document with detection results

    Raises:
        HTTPException: If document not found
    """
    service = DetectionService(db)
    document = await service.get_document(document_id, with_results=True)

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document not found: {document_id}",
        )

    return DocumentResponse(
        success=True,
        message="Document retrieved successfully",
        data=document,
    )


@router.delete(
    "/documents/{document_id}",
    response_model=BaseResponse,
    summary="Delete document",
)
async def delete_document(
    document_id: int,
    db: AsyncSession = Depends(get_db),
) -> BaseResponse:
    """
    Delete a document and its detection results.

    Args:
        document_id: Document ID
        db: Database session

    Returns:
        Success response

    Raises:
        HTTPException: If document not found
    """
    service = DetectionService(db)

    # Get document to get file path
    document = await service.get_document(document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document not found: {document_id}",
        )

    # Delete file from disk
    file_path = Path(document.file_path)
    if file_path.exists():
        try:
            os.remove(file_path)
            logger.info(f"Deleted file: {file_path}")
        except Exception as e:
            logger.warning(f"Failed to delete file {file_path}: {e}")

    # Delete from database
    deleted = await service.delete_document(document_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete document",
        )

    return BaseResponse(
        success=True,
        message=f"Document {document_id} deleted successfully",
    )
