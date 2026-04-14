from datetime import datetime
from typing import Any, Dict, Optional
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import models


def _to_dict(obj: Any) -> Dict[str, Any]:
    if obj is None:
        return {}
    if isinstance(obj, dict):
        return obj
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    if hasattr(obj, "dict"):
        return obj.dict()
    return {key: value for key, value in vars(obj).items() if not key.startswith("_")}


class DocumentRepository:
    async def create(self, doc_data: Any, db: AsyncSession) -> models.Document:
        payload = _to_dict(doc_data)
        new_doc = models.Document(
            document_id=payload.get("document_id") or uuid4().hex,
            user_id=payload.get("user_id"),
            folder_id=payload.get("folder_id"),
            subject=payload.get("subject"),
            title=payload.get("title"),
            source_type=payload.get("source_type"),
            language=payload.get("language"),
            file_name=payload.get("file_name"),
            file_path=payload.get("file_path"),
            mime_type=payload.get("mime_type"),
            checksum_sha256=payload.get("checksum_sha256"),
            status=payload.get("status") or "uploaded",
            tags=payload.get("tags"),
            uploaded_at=payload.get("uploaded_at") or datetime.utcnow(),
        )
        try:
            db.add(new_doc)
            await db.commit()
            await db.refresh(new_doc)
            return new_doc
        except Exception:
            await db.rollback()
            raise

    async def get_by_id(self, document_id: str, db: AsyncSession) -> Optional[models.Document]:
        result = await db.execute(select(models.Document).where(models.Document.document_id == document_id))
        return result.scalars().first()

    async def list_by_user(self, user_id: str, db: AsyncSession):
        result = await db.execute(
            select(models.Document)
            .where(models.Document.user_id == user_id)
            .order_by(models.Document.uploaded_at.desc())
        )
        return result.scalars().all()
