from inspect import isawaitable

from fastapi import APIRouter, HTTPException, status
from fastapi.encoders import jsonable_encoder

from app.core import logging
from app.schemas.query import QueryRequest
from app.services.tutoring_service import process_chat_query

router = APIRouter(tags=["Chat"])


def _build_initial_context(chat_history: list) -> str:
    """
    Convert chat history objects into a plain text context block.
    """
    if not chat_history:
        return ""

    lines: list[str] = []

    for turn in chat_history:
        role = getattr(turn, "role", "user")
        content = getattr(turn, "content", "")
        if content:
            lines.append(f"{role}: {content}")

    return "\n".join(lines)


@router.post("/ask", status_code=status.HTTP_200_OK)
async def ask_question(query_data: QueryRequest):
    """
    Handle the main Q&A flow.
    Supports both async and sync service implementations.
    """
    logging.logger.info(
        "Received query request_id=%s user_id=%s session_id=%s",
        query_data.request_id,
        query_data.user_id,
        query_data.session_id,
    )

    try:
        initial_context = _build_initial_context(query_data.chat_history)

        try:
            result = process_chat_query(
                query_request=query_data,
                initial_context=initial_context,
            )
        except TypeError:
            try:
                result = process_chat_query(
                    user_query=query_data.question,
                    initial_context=initial_context,
                    user_id=query_data.user_id,
                    session_id=query_data.session_id,
                    request_id=query_data.request_id,
                    subject_hint=query_data.subject_hint,
                )
            except TypeError:
                result = process_chat_query(
                    user_query=query_data.question,
                    initial_context=initial_context,
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
    except Exception as exc:
        logging.logger.error("Unhandled error in chat endpoint.", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process query: {exc}",
        ) from exc