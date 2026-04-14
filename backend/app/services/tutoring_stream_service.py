from __future__ import annotations

import json
from typing import Any, AsyncIterator, Dict, List, Optional, Tuple

from app.core.llm_client import LLMClient
from app.core.provider_config import resolve_llm_config
from app.graph.concept_router import route_concept_async
from app.reasoning.citation_builder import clean_raw_chunk_citations
from app.reasoning.planner import generate_plan_steps_async
from app.reasoning.query_classifier import classify_query_with_reason_async
from app.reasoning.query_decomposer import decompose_query_async
from app.reasoning.synthesizer import _synthesize_answer_deterministic
from app.schemas.answer import AnswerResponse
from app.schemas.llm_config import LLMConfig
from app.schemas.query import QueryRequest
from app.services.retrieval_service import RetrievalService, get_retrieval_service
from app.verification.answer_verifier import verify_answer_async
from app.verification.claim_checker import check_claim_async


def _sse(event: str, data: Dict[str, Any]) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def _build_streaming_messages(query_text: str, normalized_chunks: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    context_lines: List[str] = []
    for idx, item in enumerate(normalized_chunks, start=1):
        metadata = item.get("metadata", {}) or {}
        document_id = metadata.get("document_id") or "unknown_document"
        chunk_id = metadata.get("chunk_id") or f"chunk_{idx}"
        page_start = metadata.get("page_start")
        page_end = metadata.get("page_end")
        page_label = ""
        if page_start is not None and page_end is not None:
            page_label = f" (pages {page_start}-{page_end})"
        elif page_start is not None:
            page_label = f" (page {page_start})"

        context_lines.append(
            f"[{idx}] document_id={document_id}, chunk_id={chunk_id}{page_label}\n{item['text']}"
        )

    context_block = "\n\n".join(context_lines).strip()

    system_prompt = (
        "You are a grounded tutoring assistant.\n"
        "Use only the provided evidence.\n"
        "Do not output JSON.\n"
        "Do not fabricate citations.\n"
        "If evidence is insufficient, say so clearly.\n"
        "Answer in plain text."
    )

    user_prompt = (
        f"User question:\n{query_text}\n\n"
        f"Evidence:\n{context_block}\n\n"
        "Write a concise grounded answer in plain text."
    )

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


async def process_chat_query_stream(
    query_request: Optional[QueryRequest] = None,
    user_query: Optional[str] = None,
    initial_context: str = "",
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    request_id: Optional[str] = None,
    subject_hint: Optional[str] = None,
    retrieval_service: Optional[RetrievalService] = None,
    user_config: Optional[LLMConfig] = None,
) -> AsyncIterator[str]:
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

    yield _sse(
        "meta",
        {
            "request_id": query_request.request_id,
            "session_id": query_request.session_id,
            "query": query_text,
        },
    )

    yield _sse("status", {"stage": "classifying", "message": "Đang phân loại câu hỏi."})
    classification = await classify_query_with_reason_async(
        query_text,
        context=initial_context,
        user_config=user_config,
    )
    label = classification.get("label", "FACTUAL_QA")

    yield _sse("status", {"stage": "planning", "message": "Đang lập kế hoạch truy hồi."})
    plan_steps = await generate_plan_steps_async(
        goal=query_text,
        context=initial_context,
        user_config=user_config,
    )

    if label == "GENERAL_CHAT":
        answer_text = "Hello! Ask me a question about your study materials and I will answer using grounded evidence."
        yield _sse("token", {"text": answer_text})
        yield _sse(
            "final",
            {
                "query": query_text,
                "classification": classification,
                "sub_questions": [],
                "plan": plan_steps,
                "evidence": [],
                "answer": AnswerResponse(answer_text=answer_text).model_dump(),
                "verification": {
                    "is_supported": True,
                    "reasoning": "Conversational response does not require evidence retrieval.",
                    "corrected_answer": answer_text,
                },
                "claim_check": None,
            },
        )
        return

    if label == "OUT_OF_SCOPE":
        answer_text = "This question appears outside the grounded study-material scope of TutorRAG. Please ask about content supported by your uploaded learning documents."
        yield _sse("token", {"text": answer_text})
        yield _sse(
            "final",
            {
                "query": query_text,
                "classification": classification,
                "sub_questions": [],
                "plan": plan_steps,
                "evidence": [],
                "answer": AnswerResponse(answer_text=answer_text).model_dump(),
                "verification": {
                    "is_supported": True,
                    "reasoning": "Scoped refusal/redirect response.",
                    "corrected_answer": answer_text,
                },
                "claim_check": None,
            },
        )
        return

    base_filters: Dict[str, Any] = {"user_id": query_request.user_id}
    if query_request.subject_hint:
        base_filters["subject"] = query_request.subject_hint

    yield _sse("status", {"stage": "routing", "message": "Đang định tuyến khái niệm."})
    target_concept = await route_concept_async(query_text, user_llm_config=user_config)

    def _filters_with_optional_concept() -> Tuple[Dict[str, Any], Dict[str, Any]]:
        concept_filters = dict(base_filters)
        if target_concept:
            concept_filters["concepts"] = [target_concept]
        return concept_filters, dict(base_filters)

    def _retrieve_with_fallback(query_value: Any, top_k: int) -> List[Any]:
        concept_filters, fallback_filters = _filters_with_optional_concept()
        if target_concept:
            filtered_results = retrieval_service.retrieve_and_build_evidence(
                query=query_value,
                filters=concept_filters,
                top_k=top_k,
            )
            if filtered_results:
                return filtered_results
        return retrieval_service.retrieve_and_build_evidence(
            query=query_value,
            filters=fallback_filters,
            top_k=top_k,
        )

    yield _sse("status", {"stage": "retrieving", "message": "Đang truy hồi tài liệu."})

    sub_questions: List[str] = []
    evidence_items: List[Any] = []

    if label == "DECOMPOSITION_REQUIRED":
        sub_questions = await decompose_query_async(query_text, user_config=user_config)
        seen_keys = set()
        for sub_query in sub_questions:
            yield _sse(
                "status",
                {"stage": "retrieving", "message": f"Đang truy hồi cho câu con: {sub_query}"},
            )
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

    yield _sse(
        "retrieval",
        {
            "target_concept": target_concept,
            "evidence_count": len(evidence_dicts),
            "sub_questions": sub_questions,
        },
    )

    resolved = resolve_llm_config(user_config)
    client = LLMClient(resolved)

    normalized_chunks = []
    for item in evidence_dicts:
        text = item.get("text") or item.get("content") or item.get("snippet") or ""
        metadata = item.get("metadata", {}) if isinstance(item.get("metadata"), dict) else {}
        for key in ("document_id", "chunk_id", "page_start", "page_end", "source_file", "section", "chapter"):
            if key in item and key not in metadata:
                metadata[key] = item[key]
        if str(text).strip():
            normalized_chunks.append({"text": str(text).strip(), "metadata": metadata})

    if not normalized_chunks:
        final_answer_text = "The provided material is insufficient to answer this question."
        verification_result = {
            "is_supported": True,
            "reasoning": "No evidence available for grounded synthesis.",
            "corrected_answer": final_answer_text,
        }
        answer_response = AnswerResponse(
            answer_text=final_answer_text,
            reasoning_summary=[classification.get("reason", ""), "No retrieved evidence was available."],
            citations=[],
            confidence=0.5,
            metadata={
                "request_id": query_request.request_id,
                "session_id": query_request.session_id,
                "subject_hint": query_request.subject_hint,
                "target_concept": target_concept,
            },
        )
        yield _sse(
            "final",
            {
                "query": query_text,
                "target_concept": target_concept,
                "classification": classification,
                "sub_questions": sub_questions,
                "plan": plan_steps,
                "evidence": evidence_dicts,
                "answer": answer_response.model_dump(),
                "verification": verification_result,
                "claim_check": None,
            },
        )
        return

    messages = _build_streaming_messages(query_text=query_text, normalized_chunks=normalized_chunks)

    yield _sse("status", {"stage": "generating", "message": "Đang sinh câu trả lời..."})

    full_answer_parts: List[str] = []
    try:
        async for piece in client.chat_stream(messages=messages, temperature=0.0):
            if not piece:
                continue
            full_answer_parts.append(piece)
            yield _sse("token", {"text": piece})
    except Exception:
        synthesized_answer = _synthesize_answer_deterministic(query_text, normalized_chunks)
        yield _sse("token", {"text": synthesized_answer})
        full_answer_parts = [synthesized_answer]

    synthesized_answer = "".join(full_answer_parts).strip()
    if not synthesized_answer:
        synthesized_answer = _synthesize_answer_deterministic(query_text, normalized_chunks)
    synthesized_answer, _ = clean_raw_chunk_citations(synthesized_answer)

    yield _sse("status", {"stage": "verifying", "message": "Đang kiểm chứng câu trả lời."})
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
            "Answer synthesized from retrieved evidence via streaming.",
        ],
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

    yield _sse(
        "final",
        {
            "query": query_text,
            "target_concept": target_concept,
            "classification": classification,
            "sub_questions": sub_questions,
            "plan": plan_steps,
            "evidence": evidence_dicts,
            "answer": answer_response.model_dump(),
            "verification": verification_result,
            "claim_check": claim_check_result,
        },
    )