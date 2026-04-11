from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import logging
from app.core.auth import AuthenticatedUser, get_current_user
from app.db.base import get_async_session
from app.schemas.ingestion import IngestionResponse, IngestionResponseData
from app.services.ingestion_service import IngestionService, get_ingestion_service

router = APIRouter(tags=["Upload"])


@router.post("/file", response_model=IngestionResponse, status_code=status.HTTP_201_CREATED)
async def upload_and_ingest_file(
    file: UploadFile = File(..., description="The document file to upload (PDF, DOCX, PPTX)."),
    subject: Optional[str] = Form(None, description="Subject domain of the document."),
    language: str = Form("vi", description="Primary language of the document."),
    db: AsyncSession = Depends(get_async_session),
    ingestion_service: IngestionService = Depends(get_ingestion_service),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    logger = logging.logger.getChild("routes_upload")

    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No filename provided.",
        )

    try:
        file_bytes = await file.read()
        logger.info(
            "Received upload request for file=%s (size=%d bytes), user_id=%s",
            file.filename,
            len(file_bytes),
            current_user.user_id,
        )

        doc_metadata, chunks = await ingestion_service.ingest_and_index(
            uploaded_bytes=file_bytes,
            original_filename=file.filename,
            db=db,
            user_id=current_user.user_id,
            subject=subject,
            language=language,
            persist_to_db=True,
            index_for_retrieval=True,
            user_config=None,
        )

        if not chunks:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="The uploaded file produced no indexable text chunks.",
            )

        if not doc_metadata.document_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Ingestion completed but document_id was not assigned.",
            )

        response_data = IngestionResponseData(
            document_id=doc_metadata.document_id,
            chunk_count=len(chunks),
            metadata={
                "original_filename": file.filename,
                "subject": subject,
                "language": language,
            },
        )

        return IngestionResponse(data=response_data)
    except HTTPException:
        raise
    except Exception:
        logger.error("Failed to ingest uploaded file: %s", file.filename, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during file ingestion.",
        )
