from fastapi import APIRouter

from . import routes_chat, routes_documents, routes_health, routes_search, routes_upload

router = APIRouter()

router.include_router(routes_health.router, prefix="/health")
router.include_router(routes_documents.router, prefix="/documents")
router.include_router(routes_upload.router, prefix="/upload")
router.include_router(routes_chat.router, prefix="/chat")
router.include_router(routes_search.router, prefix="/search")

__all__ = ["router"]