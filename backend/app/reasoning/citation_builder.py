from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List, Optional, Tuple


def _to_dict(value: Any) -> Dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    if hasattr(value, "model_dump"):
        return value.model_dump()
    if hasattr(value, "dict"):
        return value.dict()
    return {key: val for key, val in vars(value).items() if not key.startswith("_")}


def _extract_metadata(value: Any) -> Dict[str, Any]:
    data = _to_dict(value)
    metadata = data.get("metadata")
    if isinstance(metadata, dict):
        merged = dict(metadata)
        for key, val in data.items():
            if key != "metadata" and key not in merged:
                merged[key] = val
        return merged
    return data


def _format_page_range(page_start: Any, page_end: Any) -> Optional[str]:
    if page_start is None and page_end is None:
        return None
    if page_start is not None and page_end is not None:
        if str(page_start) == str(page_end):
            return str(page_start)
        return f"{page_start}-{page_end}"
    return str(page_start if page_start is not None else page_end)


def build_citation_payload(value: Any) -> Dict[str, Any]:
    metadata = _extract_metadata(value)
    source_identifier = (
        metadata.get("document_id")
        or metadata.get("source_document_id")
        or metadata.get("doc_id")
        or metadata.get("source")
        or metadata.get("source_file")
    )
    chunk_id = (
        metadata.get("chunk_id")
        or metadata.get("id")
        or metadata.get("chunk_index")
        or metadata.get("source_chunk_id")
    )
    page_start = metadata.get("page_start") or metadata.get("page")
    page_end = metadata.get("page_end")
    section = metadata.get("section")
    chapter = metadata.get("chapter")
    return {
        "document_id": source_identifier,
        "chunk_id": chunk_id,
        "page_start": page_start,
        "page_end": page_end,
        "section": section,
        "chapter": chapter,
    }


def build_citation_string(value: Any) -> str:
    payload = build_citation_payload(value)
    parts: List[str] = []
    if payload.get("document_id"):
        parts.append(f"Source: {payload['document_id']}")
    if payload.get("chunk_id") is not None:
        parts.append(f"Chunk: {payload['chunk_id']}")
    page_range = _format_page_range(payload.get("page_start"), payload.get("page_end"))
    if page_range is not None:
        parts.append(f"Page: {page_range}")
    if payload.get("section"):
        parts.append(f"Section: {payload['section']}")
    if payload.get("chapter"):
        parts.append(f"Chapter: {payload['chapter']}")
    if not parts:
        return ""
    return "[" + ", ".join(parts) + "]"


def format_citations_from_chunks(chunks: Iterable[Any]) -> str:
    seen = set()
    ordered: List[str] = []
    for chunk in chunks:
        citation = build_citation_string(chunk)
        if citation and citation not in seen:
            seen.add(citation)
            ordered.append(citation)
    return ", ".join(ordered)


def attach_citation(text: str, value: Any) -> str:
    clean_text = (text or "").strip()
    if not clean_text:
        return ""
    citation = build_citation_string(value)
    if not citation:
        return clean_text
    return f"{clean_text} {citation}"


RAW_CHUNK_PATTERN = re.compile(r"\[([A-Za-z0-9]+_chunk_\d+)\]")
BARE_CHUNK_PATTERN = re.compile(r"\b([A-Za-z0-9]+_chunk_\d+)\b")


def clean_raw_chunk_citations(text: str) -> Tuple[str, List[str]]:
    if not text:
        return text, []

    ordered: List[str] = []

    def replace(match: re.Match[str]) -> str:
        chunk_id = match.group(1)
        if chunk_id not in ordered:
            ordered.append(chunk_id)
        return f"[{ordered.index(chunk_id) + 1}]"

    cleaned = RAW_CHUNK_PATTERN.sub(replace, text)
    cleaned = BARE_CHUNK_PATTERN.sub("", cleaned)
    cleaned = re.sub(r"[ \t]{2,}", " ", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    cleaned = re.sub(r"\s+([.,;:!?])", r"\1", cleaned)
    return cleaned.strip(), ordered
