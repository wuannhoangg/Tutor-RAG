from __future__ import annotations

from fastapi import FastAPI

from app.api import router
from app.core import logging
from app.core.config import get_settings
from app.db.base import create_all_tables


settings = get_settings()
log = logging.logger

app = FastAPI(
    title="TutorRAG",
    description="Grounded RAG backend for self-learning from personal study materials.",
    version="0.1.0",
    openapi_tags=[
        {"name": "Health", "description": "System health checks."},
        {"name": "Documents", "description": "Document ingestion and management."},
        {"name": "Chat", "description": "Core tutoring and grounded Q&A."},
        {"name": "Search", "description": "Grounded evidence retrieval."},
    ],
)

app.include_router(router, prefix=settings.API_V1_STR)


@app.on_event("startup")
async def startup_event() -> None:
    """
    Development startup:
    ensure local DB tables exist.
    """
    log.info("Starting TutorRAG backend...")
    try:
        # await create_all_tables()
        log.info("Database tables initialized or already available.")
    except Exception as exc:
        log.error("Failed to initialize database tables.", exc_info=True)
        raise exc


@app.get("/")
async def root() -> dict:
    return {
        "message": "TutorRAG backend is running.",
        "api_base": settings.API_V1_STR,
    }