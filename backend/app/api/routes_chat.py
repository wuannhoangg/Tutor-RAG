from __future__ import annotations

from inspect import isawaitable

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import StreamingResponse

from app.core import logging
from app.core.auth import AuthenticatedUser, get_current_user
from app.schemas.query import QueryRequest
from app.services.retrieval_service import RetrievalService, get_retrieval_service
from app.services.tutoring_service import process_chat_query
from app.services.tutoring_stream_service import process_chat_query_stream

router = APIRouter(tags=["Chat"])


def _build_initial_context(chat_history: list) -> str:
    if not chat_history:
        return ""

    lines: list[str] = []
    for turn in chat_history:
        if isinstance(turn, str):
            content = turn.strip()
            if content:
                lines.append(f"user: {content}")
            continue

        role = getattr(turn, "role", "user")
        content = getattr(turn, "content", "")
        if content:
            lines.append(f"{role}: {content}")

    return "\n".join(lines)


@router.post("/ask", status_code=status.HTTP_200_OK)
async def ask_question(
    query_data: QueryRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    retrieval_service: RetrievalService = Depends(get_retrieval_service),
):
    query_data.user_id = current_user.user_id

    logging.logger.info(
        "Received query request_id=%s user_id=%s session_id=%s",
        query_data.request_id,
        current_user.user_id,
        query_data.session_id,
    )

    try:
        initial_context = _build_initial_context(query_data.chat_history)
        result = process_chat_query(
            query_request=query_data,
            initial_context=initial_context,
            retrieval_service=retrieval_service,
            user_config=query_data.llm_config,
        )

        if isawaitable(result):
            result = await result

        return {
            "success": True,
            "message": "Query processed successfully.",
            "data": jsonable_encoder(result),
        }
    except HTTPException:
        raise
    except Exception:
        logging.logger.error("Unhandled error in chat endpoint.", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process query.",
        )


@router.post("/ask/stream", status_code=status.HTTP_200_OK)
async def ask_question_stream(
    query_data: QueryRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    retrieval_service: RetrievalService = Depends(get_retrieval_service),
):
    query_data.user_id = current_user.user_id

    logging.logger.info(
        "Received STREAM query request_id=%s user_id=%s session_id=%s",
        query_data.request_id,
        current_user.user_id,
        query_data.session_id,
    )

    initial_context = _build_initial_context(query_data.chat_history)

    async def event_generator():
        try:
            async for chunk in process_chat_query_stream(
                query_request=query_data,
                initial_context=initial_context,
                retrieval_service=retrieval_service,
                user_config=query_data.llm_config,
            ):
                yield chunk
        except HTTPException:
            raise
        except Exception:
            logging.logger.error("Unhandled error in stream chat endpoint.", exc_info=True)
            yield 'event: error\ndata: {"message":"Failed to process streaming query."}\n\n'

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )