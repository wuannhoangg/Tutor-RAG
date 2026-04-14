from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from app.graph.concept_router import route_concept_async
from app.reasoning.citation_builder import clean_raw_chunk_citations
from app.reasoning.planner import generate_plan_steps_async
from app.reasoning.query_classifier import classify_query_with_reason_async
from app.reasoning.query_decomposer import decompose_query_async
from app.reasoning.synthesizer import synthesize_answer_async
from app.schemas.answer import AnswerResponse
from app.schemas.llm_config import LLMConfig
from app.schemas.query import QueryRequest
from app.services.retrieval_service import RetrievalService, get_retrieval_service
from app.verification.answer_verifier import verify_answer_async
from app.verification.claim_checker import check_claim_async


async def process_chat_query(
    query_request: Optional[QueryRequest] = None,
    user_query: Optional[str] = None,
    initial_context: str = "",
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    request_id: Optional[str] = None,
    subject_hint: Optional[str] = None,
    retrieval_service: Optional[RetrievalService] = None,
    user_config: Optional[LLMConfig] = None,
) -> Dict[str, Any]:
    retrieval_service = retrieval_service or get_retrieval_service()

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

    classification = await classify_query_with_reason_async(query_text, context=initial_context, user_config=user_config)
    label = classification.get("label", "FACTUAL_QA")

    plan_steps = await generate_plan_steps_async(goal=query_text, context=initial_context, user_config=user_config)

    if label == "GENERAL_CHAT":
        answer_text = "Hello! Ask me a question about your study materials and I will answer using grounded evidence."
        verified = {
            "is_supported": True,
            "reasoning": "Conversational response does not require evidence retrieval.",
            "corrected_answer": answer_text,
        }
        return {"query": query_text, "classification": classification, "sub_questions": [], "plan": plan_steps, "evidence": [], "answer": AnswerResponse(answer_text=answer_text).model_dump(), "verification": verified}

    if label == "OUT_OF_SCOPE":
        answer_text = "This question appears outside the grounded study-material scope of TutorRAG. Please ask about content supported by your uploaded learning documents."
        verified = {
            "is_supported": True,
            "reasoning": "Scoped refusal/redirect response.",
            "corrected_answer": answer_text,
        }
        return {"query": query_text, "classification": classification, "sub_questions": [], "plan": plan_steps, "evidence": [], "answer": AnswerResponse(answer_text=answer_text).model_dump(), "verification": verified}

    base_filters: Dict[str, Any] = {"user_id": query_request.user_id}
    if query_request.subject_hint:
        base_filters["subject"] = query_request.subject_hint

    target_concept = await route_concept_async(query_text, user_llm_config=user_config)

    def _filters_with_optional_concept() -> Tuple[Dict[str, Any], Dict[str, Any]]:
        concept_filters = dict(base_filters)
        if target_concept:
            concept_filters["concepts"] = [target_concept]
        return concept_filters, dict(base_filters)

    def _retrieve_with_fallback(query_value: Any, top_k: int) -> List[Any]:
        concept_filters, fallback_filters = _filters_with_optional_concept()
        if target_concept:
            filtered_results = retrieval_service.retrieve_and_build_evidence(query=query_value, filters=concept_filters, top_k=top_k)
            if filtered_results:
                return filtered_results
        return retrieval_service.retrieve_and_build_evidence(query=query_value, filters=fallback_filters, top_k=top_k)

    sub_questions: List[str] = []
    evidence_items: List[Any] = []

    if label == "DECOMPOSITION_REQUIRED":
        sub_questions = await decompose_query_async(query_text, user_config=user_config)
        seen_keys = set()
        for sub_query in sub_questions:
            retrieved = _retrieve_with_fallback(sub_query, top_k=3)
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
        evidence_items = _retrieve_with_fallback(query_request, top_k=5)

    evidence_dicts = [item.model_dump() if hasattr(item, "model_dump") else item for item in evidence_items]
    synthesized_answer = await synthesize_answer_async(query_text, evidence_dicts, user_config=user_config)
    verification_result = await verify_answer_async(synthesized_answer, evidence_dicts, user_config=user_config)

    final_answer_text = verification_result.get("corrected_answer") or synthesized_answer
    final_answer_text, _ = clean_raw_chunk_citations(final_answer_text)

    citations = []
    seen_citations = set()
    for item in evidence_items:
        document_id = getattr(item, "document_id", None)
        chunk_id = getattr(item, "chunk_id", None)
        page_start = getattr(item, "page_start", None)
        page_end = getattr(item, "page_end", None)
        if not document_id:
            continue
        citation_key = (document_id, chunk_id, page_start, page_end)
        if citation_key in seen_citations:
            continue
        seen_citations.add(citation_key)
        citations.append({"document_id": document_id, "chunk_id": chunk_id, "page_start": page_start, "page_end": page_end})

    answer_response = AnswerResponse(
        answer_text=final_answer_text,
        reasoning_summary=[classification.get("reason", ""), "Answer synthesized from retrieved evidence."],
        citations=citations,
        confidence=1.0 if verification_result.get("is_supported") else 0.5,
        metadata={
            "request_id": query_request.request_id,
            "session_id": query_request.session_id,
            "subject_hint": query_request.subject_hint,
            "target_concept": target_concept,
        },
    )

    claim_check_result = None
    if final_answer_text and evidence_dicts:
        claim_check_result = await check_claim_async(final_answer_text, evidence_dicts, user_config=user_config)

    return {
        "query": query_text,
        "target_concept": target_concept,
        "classification": classification,
        "sub_questions": sub_questions,
        "plan": plan_steps,
        "evidence": evidence_dicts,
        "answer": answer_response.model_dump(),
        "verification": verification_result,
        "claim_check": claim_check_result,
    }
