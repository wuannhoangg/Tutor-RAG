from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from ..schemas.chunk import Chunk
from ..schemas.document import DocumentMetadata


def _get_attr(obj: Any, *names: str, default: Any = None) -> Any:
    if obj is None:
        return default

    if isinstance(obj, dict):
        for name in names:
            if name in obj:
                return obj[name]
        return default

    for name in names:
        if hasattr(obj, name):
            return getattr(obj, name)
    return default


class DocumentChunker:
    """
    Split normalized text into chunks while preserving source traceability.
    """

    def __init__(self, chunk_size: int = 1200, chunk_overlap: int = 150) -> None:
        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than 0.")
        if chunk_overlap < 0:
            raise ValueError("chunk_overlap cannot be negative.")
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be smaller than chunk_size.")

        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_text(
        self,
        normalized_text: str,
        source_metadata: DocumentMetadata,
        page_details: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Chunk]:
        """
        Split text into chunks using a soft boundary strategy.
        """
        if not normalized_text or not normalized_text.strip():
            return []

        text = normalized_text.strip()
        chunks: List[Chunk] = []
        start = 0
        chunk_index = 0
        text_length = len(text)

        while start < text_length:
            tentative_end = min(start + self.chunk_size, text_length)
            end = self._find_best_split_point(text, start, tentative_end)

            if end <= start:
                end = tentative_end

            chunk_text = text[start:end].strip()

            if chunk_text:
                page_start, page_end = self._resolve_page_range(
                    page_details=page_details,
                    chunk_start=start,
                    chunk_end=end,
                )

                chunk_metadata = {
                    "document_id": _get_attr(source_metadata, "document_id"),
                    "source_document_id": _get_attr(source_metadata, "document_id"),
                    "source_file": _get_attr(
                        source_metadata,
                        "original_filename",
                        "file_name",
                        "title",
                        default="unknown",
                    ),
                    "chunk_index": chunk_index,
                    "chunk_start_char": start,
                    "chunk_end_char": end,
                    "page_start": page_start,
                    "page_end": page_end,
                    "page_number_hint": page_start,
                    "content_type": "paragraph",
                }

                chunks.append(
                    Chunk(
                        text=chunk_text,
                        metadata=chunk_metadata,
                    )
                )
                chunk_index += 1

            if end >= text_length:
                break

            next_start = max(0, end - self.chunk_overlap)
            if next_start <= start:
                next_start = end

            start = next_start

        return chunks

    def _find_best_split_point(self, text: str, start: int, tentative_end: int) -> int:
        """
        Prefer paragraph, newline, sentence, or whitespace boundaries near the end.
        """
        if tentative_end >= len(text):
            return len(text)

        search_window_start = max(start, tentative_end - 250)
        region = text[search_window_start:tentative_end]

        paragraph_break = region.rfind("\n\n")
        if paragraph_break != -1:
            return search_window_start + paragraph_break + 2

        newline_break = region.rfind("\n")
        if newline_break != -1:
            return search_window_start + newline_break + 1

        sentence_matches = list(re.finditer(r"[.!?]\s+", region))
        if sentence_matches:
            return search_window_start + sentence_matches[-1].end()

        space_break = region.rfind(" ")
        if space_break != -1:
            return search_window_start + space_break + 1

        return tentative_end

    def _resolve_page_range(
        self,
        page_details: Optional[List[Dict[str, Any]]],
        chunk_start: int,
        chunk_end: int,
    ) -> tuple[Optional[int], Optional[int]]:
        """
        Map chunk character offsets back to source page/slide numbers when available.
        """
        if not page_details:
            return None, None

        overlapping_pages: List[int] = []

        for item in page_details:
            page_number = item.get("page_number")
            start_char = item.get("start_char")
            end_char = item.get("end_char")

            if page_number is None:
                continue

            if start_char is None or end_char is None:
                overlapping_pages.append(page_number)
                continue

            if not (chunk_end <= start_char or chunk_start >= end_char):
                overlapping_pages.append(page_number)

        if not overlapping_pages:
            fallback_page = page_details[0].get("page_number")
            return fallback_page, fallback_page

        return min(overlapping_pages), max(overlapping_pages)