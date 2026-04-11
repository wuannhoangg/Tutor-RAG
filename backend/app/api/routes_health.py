from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import logging
from app.db.base import get_async_session

router = APIRouter(tags=["Health"])


@router.get("/", status_code=status.HTTP_200_OK)
async def health_check(db: AsyncSession = Depends(get_async_session)):
    """
    Basic health check.
    Only verifies that the app can talk to the database.
    """
    try:
        await db.execute(text("SELECT 1"))
        logging.logger.info("Health check passed: database connection successful.")
        return {
            "status": "ok",
            "service": "TutorRAG",
            "database": "connected",
        }
    except SQLAlchemyError as exc:
        logging.logger.error("Health check failed: database connection error.", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection failed.",
        ) from exc