from inspect import isawaitable
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.encoders import jsonable_encoder

from app.core import logging
from app.schemas.query import QueryRequest
from app.services.retrieval_service import RetrievalService

router = APIRouter(tags=["Search"])


def get_retrieval_service() -> RetrievalService:
    """
    Dependency provider for retrieval service.
    """
    return RetrievalService()


@router.post("/", status_code=status.HTTP_200_OK)
async def search_document(
    query_data: QueryRequest,
    top_k: int = Query(default=5, ge=1, le=20),
    retrieval_service: RetrievalService = Depends(get_retrieval_service),
):
    """
    Perform search over the knowledge base.
    This version is intentionally flexible so it can work with slightly
    different RetrievalService method signatures.
    """
    if not query_data.question or not query_data.question.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question is required.",
        )

    filters: dict[str, Any] = {"user_id": query_data.user_id}
    if query_data.subject_hint:
        filters["subject"] = query_data.subject_hint

    try:
        try:
            result = retrieval_service.retrieve_and_build_evidence(
                query=query_data,
                filters=filters,
                top_k=top_k,
            )
        except TypeError:
            try:
                result = retrieval_service.retrieve_and_build_evidence(
                    query_request=query_data,
                    filters=filters,
                    top_k=top_k,
                )
            except TypeError:
                result = retrieval_service.retrieve_and_build_evidence(
                    user_query=query_data.question,
                    user_id=query_data.user_id,
                    subject_hint=query_data.subject_hint,
                    filters=filters,
                    top_k=top_k,
                )

        if isawaitable(result):
            result = await result

        return {
            "success": True,
            "message": "Search completed successfully.",
            "data": jsonable_encoder(result),
        }

    except HTTPException:
        raise
    except Exception as exc:
        logging.logger.error("Unhandled error in search endpoint.", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to perform search: {exc}",
        ) from exc