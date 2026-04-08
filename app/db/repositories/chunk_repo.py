from typing import Any, Dict, List
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import constants
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

    return {
        key: value
        for key, value in vars(obj).items()
        if not key.startswith("_")
    }


def _safe_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


class ChunkRepository:
    """Repository for handling Chunk metadata CRUD operations."""

    async def save_chunks(
        self,
        document_id: str,
        chunks: List[Any],
        db: AsyncSession,
    ) -> List[models.Chunk]:
        """
        Create multiple chunk records for a document.
        Works with slightly different chunk schema shapes.
        """
        chunk_objects: List[models.Chunk] = []

        try:
            for item in chunks:
                payload = _to_dict(item)
                metadata = _to_dict(payload.get("metadata"))

                text = payload.get("text") or payload.get("content") or ""
                if not text:
                    continue

                page_start = (
                    _safe_int(payload.get("page_start"))
                    or _safe_int(metadata.get("page_start"))
                    or _safe_int(metadata.get("page_number_hint"))
                )
                page_end = (
                    _safe_int(payload.get("page_end"))
                    or _safe_int(metadata.get("page_end"))
                    or page_start
                )

                chunk_id = (
                    payload.get("chunk_id")
                    or metadata.get("chunk_id")
                    or f"{document_id}_chunk_{uuid4().hex}"
                )

                chunk_obj = models.Chunk(
                    chunk_id=chunk_id,
                    document_id=document_id,
                    user_id=payload.get("user_id") or metadata.get("user_id"),
                    subject=payload.get("subject") or metadata.get("subject"),
                    chapter=payload.get("chapter") or metadata.get("chapter"),
                    section=payload.get("section") or metadata.get("section"),
                    page_start=page_start,
                    page_end=page_end,
                    content_type=(
                        payload.get("content_type")
                        or metadata.get("content_type")
                        or constants.CHUNK_TYPE_PARAGRAPH
                    ),
                    text=text,
                    token_count=payload.get("token_count") or len(text.split()),
                    keywords=payload.get("keywords") or metadata.get("keywords"),
                )
                chunk_objects.append(chunk_obj)

            if chunk_objects:
                db.add_all(chunk_objects)
                await db.commit()

            result = await db.execute(
                select(models.Chunk).where(models.Chunk.document_id == document_id)
            )
            return result.scalars().all()

        except Exception:
            await db.rollback()
            raise

    async def get_by_document_id(
        self,
        document_id: str,
        db: AsyncSession,
    ) -> List[models.Chunk]:
        """Retrieve all chunks for a document ID."""
        result = await db.execute(
            select(models.Chunk).where(models.Chunk.document_id == document_id)
        )
        return result.scalars().all()