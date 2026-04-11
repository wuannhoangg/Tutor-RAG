from __future__ import annotations

from typing import Any, Dict, List

from app.core import logging
from app.schemas.evidence import Evidence


logger = logging.logger.getChild("evidence_builder")


class EvidenceBuilder:
    """
    Convert ranked retrieval results into structured evidence objects.
    """

    def build_evidence(self, ranked_candidates: List[Dict[str, Any]], original_query: str) -> List[Evidence]:
        evidence_list: List[Evidence] = []

        for candidate in ranked_candidates:
            payload = candidate.get("payload", {}) or {}
            metadata = payload.get("metadata", {}) or {}

            evidence = Evidence(
                chunk_id=payload.get("chunk_id") or metadata.get("chunk_id"),
                document_id=payload.get("document_id") or metadata.get("document_id") or payload.get("source_id"),
                text=payload.get("text"),
                snippet=payload.get("snippet") or payload.get("text", "")[:300],
                role=payload.get("role") or metadata.get("content_type") or "support",
                score=float(candidate.get("score", 0.0)),
                page_start=payload.get("page_start") or metadata.get("page_start"),
                page_end=payload.get("page_end") or metadata.get("page_end"),
                retrieved_for=original_query,
                metadata=metadata,
            )
            evidence_list.append(evidence)

        return evidence_list