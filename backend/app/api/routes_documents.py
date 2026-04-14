from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import logging
from app.core.auth import AuthenticatedUser, get_current_user
from app.db.base import get_async_session
from app.db.repositories.document_repo import DocumentRepository
from app.db.repositories.folder_repo import FolderRepository

router = APIRouter(tags=["Documents"])

doc_repo = DocumentRepository()
folder_repo = FolderRepository()


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_document(
    doc_data: dict,
    db: AsyncSession = Depends(get_async_session),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    try:
        payload = dict(doc_data or {})
        payload["user_id"] = current_user.user_id

        new_doc = await doc_repo.create(payload, db)

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


@router.post("/folders", status_code=status.HTTP_201_CREATED)
async def create_folder(
    payload: dict,
    db: AsyncSession = Depends(get_async_session),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    name = (payload.get("name") or "").strip()
    if not name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Folder name is required.",
        )

    existing = await folder_repo.get_by_name_for_user(current_user.user_id, name, db)
    if existing:
        return {
            "success": True,
            "message": "Folder already exists.",
            "data": jsonable_encoder(existing),
        }

    folder = await folder_repo.create(
        user_id=current_user.user_id,
        name=name,
        is_system=False,
        db=db,
    )
    return {
        "success": True,
        "message": "Folder created successfully.",
        "data": jsonable_encoder(folder),
    }


@router.get("/folders", status_code=status.HTTP_200_OK)
async def list_folders(
    db: AsyncSession = Depends(get_async_session),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    await folder_repo.get_or_create_system_folder(
        user_id=current_user.user_id,
        name="Uploads",
        db=db,
    )

    folders = await folder_repo.list_by_user(current_user.user_id, db)
    data = [
        {
            "folder_id": folder.folder_id,
            "name": folder.name,
            "system": str(folder.is_system).lower() == "true",
        }
        for folder in folders
    ]

    return {
        "success": True,
        "data": data,
    }


@router.get("", status_code=status.HTTP_200_OK)
async def list_documents(
    db: AsyncSession = Depends(get_async_session),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    documents = await doc_repo.list_by_user(current_user.user_id, db)
    data = [
        {
            "document_id": doc.document_id,
            "name": doc.file_name or doc.title or "Untitled",
            "status": doc.status or "indexed",
            "folder_id": doc.folder_id,
            "subject": doc.subject,
            "language": doc.language,
            "uploaded_at": doc.uploaded_at.isoformat() if doc.uploaded_at else None,
        }
        for doc in documents
    ]
    return {
        "success": True,
        "data": data,
    }


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
        logging.logger.error("Error during document retrieval.", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve document metadata.",
        )
