from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix=settings.API_V1_STR)


@app.on_event("startup")
async def startup_event() -> None:
    log.info("Starting TutorRAG backend...")
    if not settings.AUTO_CREATE_TABLES:
        log.info("AUTO_CREATE_TABLES is disabled; skipping create_all_tables().")
        return

    try:
        await create_all_tables()
        log.info("Database tables initialized or already available.")
    except Exception:
        log.error("Failed to initialize database tables.", exc_info=True)
        raise


@app.get("/")
async def root() -> dict:
    return {
        "message": "TutorRAG backend is running.",
        "api_base": settings.API_V1_STR,
    }