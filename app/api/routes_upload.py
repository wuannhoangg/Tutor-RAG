from typing import Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import logging
from app.db.base import get_async_session
from app.schemas.ingestion import IngestionResponse, IngestionResponseData
from app.services.ingestion_service import IngestionService

router = APIRouter(tags=["Upload"])

def get_ingestion_service() -> IngestionService:
    return IngestionService()

@router.post("/file", response_model=IngestionResponse, status_code=status.HTTP_201_CREATED)
async def upload_and_ingest_file(
    file: UploadFile = File(..., description="The document file to upload (PDF, DOCX, PPTX)."),
    user_id: str = Form("system_user", description="ID of the user uploading the file."),
    subject: Optional[str] = Form(None, description="Subject domain of the document."),
    language: str = Form("vi", description="Primary language of the document."),
    db: AsyncSession = Depends(get_async_session),
    ingestion_service: IngestionService = Depends(get_ingestion_service),
):
    """
    Upload a binary file, parse its content, normalize, chunk, and index it.
    """
    logger = logging.logger.getChild("routes_upload")
    
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="No filename provided."
        )

    try:
        # Read the file bytes into memory
        file_bytes = await file.read()
        
        logger.info(
            "Received upload request for file=%s (size=%d bytes), user_id=%s", 
            file.filename, len(file_bytes), user_id
        )

        # Execute the full ingestion pipeline
        chunks = await ingestion_service.ingest_and_index(
            uploaded_bytes=file_bytes,
            original_filename=file.filename,
            db=db,
            user_id=user_id,
            subject=subject,
            language=language,
            persist_to_db=True,
            index_for_retrieval=True,
        )

        if not chunks:
            logger.warning("File %s yielded 0 chunks after parsing.", file.filename)

        # Extract the document_id assigned during the ingestion process
        # We look at the first chunk to find the document_id
        document_id = "unknown"
        if chunks and chunks[0].metadata and "document_id" in chunks[0].metadata:
            document_id = chunks[0].metadata["document_id"]

        response_data = IngestionResponseData(
            document_id=document_id,
            chunk_count=len(chunks),
            metadata={
                "original_filename": file.filename,
                "subject": subject,
                "language": language
            }
        )

        return IngestionResponse(data=response_data)

    except Exception as exc:
        logger.error("Failed to ingest uploaded file: %s", file.filename, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during file ingestion: {str(exc)}"
        ) from exc