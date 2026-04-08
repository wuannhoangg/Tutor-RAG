from __future__ import annotations

from typing import Any, Dict, List, Optional


class MetadataFilters:
    """
    Helpers for building simple metadata filters.
    """

    @staticmethod
    def from_document_id(document_id: str) -> Dict[str, Any]:
        return {"document_id": document_id}

    @staticmethod
    def from_source_type(source_type: Optional[str] = None) -> Dict[str, Any]:
        if not source_type:
            return {}
        return {"source_type": source_type}

    @staticmethod
    def from_user_id(user_id: Optional[str] = None) -> Dict[str, Any]:
        if not user_id:
            return {}
        return {"user_id": user_id}

    @staticmethod
    def from_subject(subject: Optional[str] = None) -> Dict[str, Any]:
        if not subject:
            return {}
        return {"subject": subject}

    @staticmethod
    def combine_filters(filters: List[Dict[str, Any]]) -> Dict[str, Any]:
        combined: Dict[str, Any] = {}
        for filter_dict in filters:
            combined.update(filter_dict or {})
        return combined

    @staticmethod
    def build_complex_filter(
        document_id: Optional[str] = None,
        source_type: Optional[str] = None,
        user_id: Optional[str] = None,
        subject: Optional[str] = None,
    ) -> Dict[str, Any]:
        return MetadataFilters.combine_filters(
            [
                MetadataFilters.from_document_id(document_id) if document_id else {},
                MetadataFilters.from_source_type(source_type),
                MetadataFilters.from_user_id(user_id),
                MetadataFilters.from_subject(subject),
            ]
        )