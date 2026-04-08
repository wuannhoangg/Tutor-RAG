from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.reasoning import (
    classify_query_with_reason,
    decompose_query,
    generate_plan_steps,
    synthesize_answer,
)
from app.schemas.answer import AnswerResponse
from app.schemas.query import QueryRequest
from app.services.retrieval_service import RetrievalService
from app.verification import check_claim, verify_answer


async def process_chat_query(
    query_request: Optional[QueryRequest] = None,
    user_query: Optional[str] = None,
    initial_context: str = "",
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    request_id: Optional[str] = None,
    subject_hint: Optional[str] = None,
    retrieval_service: Optional[RetrievalService] = None,
) -> Dict[str, Any]:
    """
    Execute the end-to-end tutoring flow without requiring an LLM.
    """
    retrieval_service = retrieval_service or RetrievalService()

    if query_request is None:
        query_request = QueryRequest(
            query_text=user_query or "",
            user_id=user_id or "system_user",
            session_id=session_id,
            request_id=request_id,
            subject_hint=subject_hint,
            context={"initial_context": initial_context} if initial_context else {},
        )

    query_text = query_request.query_text.strip()
    classification = classify_query_with_reason(query_text, context=initial_context)
    label = classification["label"]

    plan_steps = generate_plan_steps(goal=query_text, context=initial_context)

    if label == "GENERAL_CHAT":
        answer_text = "Hello! Ask me a question about your study materials and I will answer using grounded evidence."
        verified = {
            "is_supported": True,
            "reasoning": "Conversational response does not require evidence retrieval.",
            "corrected_answer": answer_text,
        }
        return {
            "query": query_text,
            "classification": classification,
            "sub_questions": [],
            "plan": plan_steps,
            "evidence": [],
            "answer": AnswerResponse(answer_text=answer_text).model_dump(),
            "verification": verified,
        }

    if label == "OUT_OF_SCOPE":
        answer_text = (
            "This question appears outside the grounded study-material scope of TutorRAG. "
            "Please ask about content supported by your uploaded learning documents."
        )
        verified = {
            "is_supported": True,
            "reasoning": "Scoped refusal/redirect response.",
            "corrected_answer": answer_text,
        }
        return {
            "query": query_text,
            "classification": classification,
            "sub_questions": [],
            "plan": plan_steps,
            "evidence": [],
            "answer": AnswerResponse(answer_text=answer_text).model_dump(),
            "verification": verified,
        }

    filters: Dict[str, Any] = {"user_id": query_request.user_id}
    if query_request.subject_hint:
        filters["subject"] = query_request.subject_hint

    sub_questions: List[str] = []
    evidence_items: List[Any] = []

    if label == "DECOMPOSITION_REQUIRED":
        sub_questions = decompose_query(query_text)
        seen_keys = set()

        for sub_query in sub_questions:
            retrieved = retrieval_service.retrieve_and_build_evidence(
                query=sub_query,
                filters=filters,
                top_k=3,
            )
            for item in retrieved:
                key = (
                    getattr(item, "document_id", None),
                    getattr(item, "chunk_id", None),
                    getattr(item, "snippet", None) or getattr(item, "text", None),
                )
                if key not in seen_keys:
                    seen_keys.add(key)
                    evidence_items.append(item)
    else:
        evidence_items = retrieval_service.retrieve_and_build_evidence(
            query=query_request,
            filters=filters,
            top_k=5,
        )

    evidence_dicts = [item.model_dump() if hasattr(item, "model_dump") else item for item in evidence_items]

    synthesized_answer = synthesize_answer(query_text, evidence_dicts)
    verification_result = verify_answer(synthesized_answer, evidence_dicts)

    final_answer_text = verification_result.get("corrected_answer") or synthesized_answer

    citations = []
    for item in evidence_items:
        document_id = getattr(item, "document_id", None)
        chunk_id = getattr(item, "chunk_id", None)
        page_start = getattr(item, "page_start", None)
        page_end = getattr(item, "page_end", None)
        if document_id:
            citations.append(
                {
                    "document_id": document_id,
                    "chunk_id": chunk_id,
                    "page_start": page_start,
                    "page_end": page_end,
                }
            )

    answer_response = AnswerResponse(
        answer_text=final_answer_text,
        reasoning_summary=[
            classification.get("reason", ""),
            "Answer synthesized from retrieved evidence.",
        ],
        citations=citations,
        confidence=1.0 if verification_result.get("is_supported") else 0.5,
        metadata={
            "request_id": query_request.request_id,
            "session_id": query_request.session_id,
            "subject_hint": query_request.subject_hint,
        },
    )

    claim_check_result = None
    if final_answer_text and evidence_dicts:
        claim_check_result = check_claim(final_answer_text, evidence_dicts)

    return {
        "query": query_text,
        "classification": classification,
        "sub_questions": sub_questions,
        "plan": plan_steps,
        "evidence": evidence_dicts,
        "answer": answer_response.model_dump(),
        "verification": verification_result,
        "claim_check": claim_check_result,
    }