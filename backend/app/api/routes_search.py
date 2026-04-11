from __future__ import annotations

from inspect import isawaitable
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.encoders import jsonable_encoder

from app.core import logging
from app.core.auth import AuthenticatedUser, get_current_user
from app.schemas.query import QueryRequest
from app.services.retrieval_service import RetrievalService, get_retrieval_service

router = APIRouter(tags=["Search"])


@router.post("/", status_code=status.HTTP_200_OK)
async def search_document(
    query_data: QueryRequest,
    top_k: int = Query(default=5, ge=1, le=20),
    retrieval_service: RetrievalService = Depends(get_retrieval_service),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    if not query_data.question or not query_data.question.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question is required.",
        )

    query_data.user_id = current_user.user_id

    filters: dict[str, Any] = {"user_id": current_user.user_id}
    if query_data.subject_hint:
        filters["subject"] = query_data.subject_hint

    try:
        result = retrieval_service.retrieve_and_build_evidence(
            query=query_data,
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
    except Exception:
        logging.logger.error("Unhandled error in search endpoint.", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to perform search.",
        )
