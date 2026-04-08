from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import logging
from app.db.base import get_async_session
from app.db.repositories.document_repo import DocumentRepository
from app.schemas.document import DocumentCreate

router = APIRouter(tags=["Documents"])

doc_repo = DocumentRepository()


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_document(
    doc_data: DocumentCreate,
    db: AsyncSession = Depends(get_async_session),
):
    """
    Save document metadata.
    This endpoint currently stores metadata only, not the binary file itself.
    """
    try:
        new_doc = await doc_repo.create(doc_data, db)

        document_id = getattr(new_doc, "document_id", None)
        logging.logger.info("Document metadata created successfully: %s", document_id)

        return {
            "success": True,
            "message": "Document metadata saved successfully.",
            "data": jsonable_encoder(new_doc),
        }
    except Exception as exc:
        logging.logger.error("Error during document metadata creation.", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save document metadata: {exc}",
        ) from exc


@router.get("/{document_id}", status_code=status.HTTP_200_OK)
async def get_document(
    document_id: str,
    db: AsyncSession = Depends(get_async_session),
):
    """
    Retrieve document metadata by document ID.
    """
    try:
        doc = await doc_repo.get_by_id(document_id, db)

        if doc is None:
            logging.logger.warning("Document not found: %s", document_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document with ID '{document_id}' not found.",
            )

        return {
            "success": True,
            "data": jsonable_encoder(doc),
        }
    except HTTPException:
        raise
    except Exception as exc:
        logging.logger.error("Error while retrieving document %s.", document_id, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve document: {exc}",
        ) from exc