from __future__ import annotations

import re
import json
import asyncio
from typing import Any, Dict, List, Tuple, Optional

from app.core.llm_client import LLMClient
from app.prompts.reasoning_prompts import build_synthesizer_prompt
from .citation_builder import attach_citation


_STOPWORDS = {
    "the", "a", "an", "of", "to", "and", "or", "for", "in", "on", "at", "with",
    "is", "are", "was", "were", "be", "by", "as", "from", "that", "this", "these",
    "those", "what", "which", "who", "whom", "why", "how", "when", "where",
    "là", "và", "của", "cho", "trong", "từ", "một", "những", "các", "gì", "nào",
    "ra", "sao", "thế", "để", "được", "với", "về", "khi", "nếu", "thì", "hay",
}

def _to_dict(value: Any) -> Dict[str, Any]:
    if value is None: return {}
    if isinstance(value, dict): return value
    if hasattr(value, "model_dump"): return value.model_dump()
    if hasattr(value, "dict"): return value.dict()
    return {k: v for k, v in vars(value).items() if not k.startswith("_")}

def _normalize_chunk(chunk: Any) -> Dict[str, Any]:
    data = _to_dict(chunk)
    metadata = data.get("metadata", {})
    if not isinstance(metadata, dict): metadata = {}
    merged_metadata = dict(metadata)
    
    for key in ("document_id", "chunk_id", "page_start", "page_end", "source_file", "section", "chapter"):
        if key in data and key not in merged_metadata:
            merged_metadata[key] = data[key]

    text = data.get("text") or data.get("content") or data.get("snippet") or ""
    return {"text": str(text).strip(), "metadata": merged_metadata}

def _tokenize(text: str) -> List[str]:
    tokens = re.findall(r"[A-Za-zÀ-ỹ0-9_]+", (text or "").lower())
    return [t for t in tokens if t not in _STOPWORDS and len(t) > 1]

def _score_text(query_tokens: List[str], text: str) -> int:
    haystack = (text or "").lower()
    return sum(1 for token in query_tokens if token in haystack)

def _split_sentences(text: str) -> List[str]:
    raw_parts = re.split(r"(?<=[.!?])\s+|\n+", (text or "").strip())
    return [re.sub(r"\s+", " ", p).strip() for p in raw_parts if re.sub(r"\s+", " ", p).strip()]

def _select_best_sentences(query: str, chunks: List[Dict[str, Any]], limit: int = 4) -> List[Tuple[str, Dict[str, Any], int]]:
    query_tokens = _tokenize(query)
    candidates: List[Tuple[str, Dict[str, Any], int]] = []
    
    for chunk in chunks:
        for sentence in _split_sentences(chunk["text"]):
            if len(sentence) < 25: continue
            score = _score_text(query_tokens, sentence)
            candidates.append((sentence, chunk["metadata"], score))

    candidates.sort(key=lambda item: (item[2], len(item[0])), reverse=True)
    selected, seen = [], set()
    for sentence, metadata, score in candidates:
        key = sentence.lower()
        if key not in seen:
            seen.add(key)
            selected.append((sentence, metadata, score))
            if len(selected) >= limit: break
    return selected

def _fallback_from_chunks(chunks: List[Dict[str, Any]], limit: int = 2) -> List[Tuple[str, Dict[str, Any], int]]:
    fallback = []
    for chunk in chunks[:limit]:
        sentences = _split_sentences(chunk["text"])
        if sentences:
            fallback.append((sentences[0], chunk["metadata"], 0))
    return fallback


def _synthesize_answer_deterministic(query: str, context_chunks: List[dict]) -> str:
    """Fallback logic when LLM is unavailable."""
    normalized_chunks = [c for c in (_normalize_chunk(ch) for ch in (context_chunks or [])) if c["text"]]
    if not normalized_chunks:
        return "The provided material is insufficient to answer this question."

    query_tokens = _tokenize(query)
    ranked_chunks = sorted(normalized_chunks, key=lambda item: _score_text(query_tokens, item["text"]), reverse=True)
    selected_sentences = _select_best_sentences(query, ranked_chunks, limit=4)

    if not selected_sentences:
        selected_sentences = _fallback_from_chunks(ranked_chunks, limit=2)
    if not selected_sentences:
        return "The provided material is insufficient to answer this question."

    parts = [attach_citation(sentence, metadata) for sentence, metadata, score in selected_sentences]
    answer = " ".join(parts).strip()
    return answer if answer else "The provided material is insufficient to answer this question."


async def synthesize_answer_async(
    query: str, 
    context_chunks: List[dict], 
    user_api_key: Optional[str] = None
) -> str:
    """Try LLM first to synthesize a fluent, grounded answer."""
    normalized_chunks = [c for c in (_normalize_chunk(ch) for ch in (context_chunks or [])) if c["text"]]
    if not normalized_chunks:
        return "The provided material is insufficient to answer this question."

    client = LLMClient(user_api_key=user_api_key)
    prompt = build_synthesizer_prompt(query=query, context_chunks=normalized_chunks)
    messages = [
        {"role": "system", "content": "You are a helpful assistant that outputs strictly in JSON."},
        {"role": "user", "content": prompt}
    ]

    llm_response = await client.chat(messages=messages, temperature=0.0, json_mode=True)
    
    if llm_response:
        try:
            result = json.loads(llm_response)
            if "answer" in result:
                return result["answer"]
        except json.JSONDecodeError:
            pass

    return _synthesize_answer_deterministic(query, context_chunks)


def synthesize_answer(
    query: str, 
    context_chunks: List[dict], 
    user_api_key: Optional[str] = None
) -> str:
    """Synchronous wrapper for backward compatibility."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        # Trả về task nếu chạy trong loop, có thể gây lỗi nều API cũ mong string.
        # Ở môi trường production thực sự, endpoint gọi file này sẽ phải await nó.
        return loop.create_task(synthesize_answer_async(query, context_chunks, user_api_key))
    else:
        return asyncio.run(synthesize_answer_async(query, context_chunks, user_api_key))