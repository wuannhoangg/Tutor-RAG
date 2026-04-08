"""
Deterministic answer synthesis from retrieved evidence.
Produces grounded text with citation markers without requiring an LLM.
"""

from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List, Tuple

from .citation_builder import attach_citation, build_citation_string


_STOPWORDS = {
    "the", "a", "an", "of", "to", "and", "or", "for", "in", "on", "at", "with",
    "is", "are", "was", "were", "be", "by", "as", "from", "that", "this", "these",
    "those", "what", "which", "who", "whom", "why", "how", "when", "where",
    "là", "và", "của", "cho", "trong", "từ", "một", "những", "các", "gì", "nào",
    "ra", "sao", "thế", "để", "được", "với", "về", "khi", "nếu", "thì", "hay",
}


def _to_dict(value: Any) -> Dict[str, Any]:
    if value is None:
        return {}

    if isinstance(value, dict):
        return value

    if hasattr(value, "model_dump"):
        return value.model_dump()

    if hasattr(value, "dict"):
        return value.dict()

    return {
        key: val
        for key, val in vars(value).items()
        if not key.startswith("_")
    }


def _normalize_chunk(chunk: Any) -> Dict[str, Any]:
    data = _to_dict(chunk)
    metadata = data.get("metadata")
    if not isinstance(metadata, dict):
        metadata = {}

    merged_metadata = dict(metadata)
    for key in (
        "document_id",
        "chunk_id",
        "page_start",
        "page_end",
        "source_file",
        "section",
        "chapter",
    ):
        if key in data and key not in merged_metadata:
            merged_metadata[key] = data[key]

    text = data.get("text") or data.get("content") or data.get("snippet") or ""
    return {
        "text": str(text).strip(),
        "metadata": merged_metadata,
    }


def _tokenize(text: str) -> List[str]:
    tokens = re.findall(r"[A-Za-zÀ-ỹ0-9_]+", (text or "").lower())
    return [token for token in tokens if token not in _STOPWORDS and len(token) > 1]


def _score_text(query_tokens: List[str], text: str) -> int:
    haystack = (text or "").lower()
    score = 0
    for token in query_tokens:
        if token in haystack:
            score += 1
    return score


def _split_sentences(text: str) -> List[str]:
    raw_parts = re.split(r"(?<=[.!?])\s+|\n+", (text or "").strip())
    result: List[str] = []
    for part in raw_parts:
        clean = re.sub(r"\s+", " ", part).strip()
        if clean:
            result.append(clean)
    return result


def _select_best_sentences(query: str, chunks: List[Dict[str, Any]], limit: int = 4) -> List[Tuple[str, Dict[str, Any], int]]:
    query_tokens = _tokenize(query)
    candidates: List[Tuple[str, Dict[str, Any], int]] = []

    for chunk in chunks:
        text = chunk["text"]
        metadata = chunk["metadata"]

        for sentence in _split_sentences(text):
            if len(sentence) < 25:
                continue
            score = _score_text(query_tokens, sentence)
            candidates.append((sentence, metadata, score))

    candidates.sort(key=lambda item: (item[2], len(item[0])), reverse=True)

    selected: List[Tuple[str, Dict[str, Any], int]] = []
    seen = set()

    for sentence, metadata, score in candidates:
        key = sentence.lower()
        if key in seen:
            continue
        seen.add(key)
        selected.append((sentence, metadata, score))
        if len(selected) >= limit:
            break

    return selected


def _fallback_from_chunks(chunks: List[Dict[str, Any]], limit: int = 2) -> List[Tuple[str, Dict[str, Any], int]]:
    fallback: List[Tuple[str, Dict[str, Any], int]] = []

    for chunk in chunks[:limit]:
        sentences = _split_sentences(chunk["text"])
        if sentences:
            fallback.append((sentences[0], chunk["metadata"], 0))

    return fallback


def synthesize_answer(query: str, context_chunks: List[dict]) -> str:
    """
    Build a grounded answer from retrieved chunks.
    Returns a plain string with citations appended inline.
    """
    normalized_chunks = [_normalize_chunk(chunk) for chunk in (context_chunks or [])]
    normalized_chunks = [chunk for chunk in normalized_chunks if chunk["text"]]

    if not normalized_chunks:
        return "The provided material is insufficient to answer this question."

    query_tokens = _tokenize(query)

    ranked_chunks = sorted(
        normalized_chunks,
        key=lambda item: _score_text(query_tokens, item["text"]),
        reverse=True,
    )

    selected_sentences = _select_best_sentences(query, ranked_chunks, limit=4)

    if not selected_sentences:
        selected_sentences = _fallback_from_chunks(ranked_chunks, limit=2)

    if not selected_sentences:
        return "The provided material is insufficient to answer this question."

    parts: List[str] = []
    for sentence, metadata, score in selected_sentences:
        parts.append(attach_citation(sentence, metadata))

    answer = " ".join(parts).strip()

    if not answer:
        return "The provided material is insufficient to answer this question."

    return answer