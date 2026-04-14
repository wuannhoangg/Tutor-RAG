from typing import Any, Dict, List

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


def _safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _safe_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _normalize_citations(value: Any) -> List[Dict[str, Any]]:
    if value is None:
        return []
    if isinstance(value, dict):
        return [value]
    if isinstance(value, list):
        return [_to_dict(item) for item in value]
    return []


class AnswerRepository:
    """Repository for handling Answer and Feedback CRUD operations."""

    async def create_answer(self, answer_data: Any, db: AsyncSession) -> models.Answer:
        payload = _to_dict(answer_data)

        new_answer = models.Answer(
            query_id=payload.get("query_id"),
            user_id=payload.get("user_id"),
            answer_text=(
                payload.get("answer_text")
                or payload.get("final_answer")
                or payload.get("response_text")
                or ""
            ),
            reasoning_summary=payload.get("reasoning_summary"),
            confidence=_safe_float(payload.get("confidence")),
            extra_metadata=payload.get("metadata") or payload.get("extra_metadata"),
        )

        try:
            db.add(new_answer)
            await db.flush()

            for citation in _normalize_citations(payload.get("citations")):
                citation_payload = dict(citation)
                snippet = citation_payload.pop("snippet", None) or citation_payload.pop("text", None)

                extra_metadata = citation_payload.get("metadata") or {}
                if not isinstance(extra_metadata, dict):
                    extra_metadata = {"raw_metadata": extra_metadata}

                if snippet:
                    extra_metadata["snippet"] = snippet

                db.add(
                    models.Citation(
                        answer_id=new_answer.answer_id,
                        document_id=citation.get("document_id"),
                        chunk_id=citation.get("chunk_id"),
                        page_start=_safe_int(citation.get("page_start")),
                        page_end=_safe_int(citation.get("page_end")),
                        extra_metadata=extra_metadata or citation_payload,
                    )
                )

            await db.commit()
            await db.refresh(new_answer)
            return new_answer
        except Exception:
            await db.rollback()
            raise

    async def record_feedback(self, feedback_data: Any, db: AsyncSession) -> models.Feedback:
        payload = _to_dict(feedback_data)

        new_feedback = models.Feedback(
            user_id=payload.get("user_id"),
            answer_id=_safe_int(payload.get("answer_id")),
            query_id=payload.get("query_id"),
            rating=_safe_int(payload.get("rating")),
            comment=payload.get("comment") or payload.get("feedback_text") or payload.get("text"),
        )

        try:
            db.add(new_feedback)
            await db.commit()
            await db.refresh(new_feedback)
            return new_feedback
        except Exception:
            await db.rollback()
            raise

    async def get_by_query_id(self, query_id: str, db: AsyncSession) -> List[models.Answer]:
        result = await db.execute(select(models.Answer).where(models.Answer.query_id == query_id))
        return result.scalars().all()