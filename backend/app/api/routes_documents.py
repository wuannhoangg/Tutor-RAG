from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import logging
from app.core.auth import AuthenticatedUser, get_current_user
from app.db.base import get_async_session
from app.db.repositories.document_repo import DocumentRepository
from app.schemas.document import DocumentCreate

router = APIRouter(tags=["Documents"])

doc_repo = DocumentRepository()


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_document(
    doc_data: DocumentCreate,
    db: AsyncSession = Depends(get_async_session),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    try:
        safe_doc_data = doc_data.model_copy(update={"user_id": current_user.user_id})
        new_doc = await doc_repo.create(safe_doc_data, db)

        document_id = getattr(new_doc, "document_id", None)
        logging.logger.info(
            "Document metadata created successfully: %s for user_id=%s",
            document_id,
            current_user.user_id,
        )

        return {
            "success": True,
            "message": "Document metadata saved successfully.",
            "data": jsonable_encoder(new_doc),
        }
    except HTTPException:
        raise
    except Exception:
        logging.logger.error("Error during document metadata creation.", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save document metadata.",
        )


@router.get("/{document_id}", status_code=status.HTTP_200_OK)
async def get_document(
    document_id: str,
    db: AsyncSession = Depends(get_async_session),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    try:
        doc = await doc_repo.get_by_id(document_id, db)

        if doc is None:
            logging.logger.warning("Document not found: %s", document_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document with ID '{document_id}' not found.",
            )

        if getattr(doc, "user_id", None) != current_user.user_id:
            logging.logger.warning(
                "Unauthorized document access attempt. document_id=%s requester=%s owner=%s",
                document_id,
                current_user.user_id,
                getattr(doc, "user_id", None),
            )
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
    except Exception:
        logging.logger.error("Error while retrieving document %s.", document_id, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve document.",
        )
