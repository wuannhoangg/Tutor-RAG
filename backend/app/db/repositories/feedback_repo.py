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


class FeedbackRepository:
    """Repository for handling user feedback records."""

    async def create(self, feedback_data: Any, db: AsyncSession) -> models.Feedback:
        payload = _to_dict(feedback_data)

        new_feedback = models.Feedback(
            user_id=payload.get("user_id"),
            query_id=payload.get("query_id"),
            feedback_text=payload.get("feedback_text") or payload.get("text") or "",
        )

        try:
            db.add(new_feedback)
            await db.commit()
            await db.refresh(new_feedback)
            return new_feedback
        except Exception:
            await db.rollback()
            raise

    async def get_user_feedback_for_query(self, query_id: str, db: AsyncSession) -> List[models.Feedback]:
        result = await db.execute(select(models.Feedback).where(models.Feedback.query_id == query_id))
        return result.scalars().all()
