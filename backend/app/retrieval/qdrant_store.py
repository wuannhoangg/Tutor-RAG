from __future__ import annotations

import hashlib
import uuid
from typing import Any, Dict, List, Optional

from qdrant_client import QdrantClient, models

from app.core.config import get_settings

from .base_store import BaseVectorStore


class QdrantVectorStore(BaseVectorStore):
    def __init__(self, collection_name: str = "tutorrag_chunks", vector_size: int = 1024):
        settings = get_settings()
        self.collection = collection_name
        self.vector_size = vector_size

        if settings.QDRANT_URL:
            self.client = QdrantClient(
                url=settings.QDRANT_URL,
                api_key=settings.QDRANT_API_KEY,
            )
        else:
            self.client = QdrantClient(
                host=settings.VECTOR_STORE_HOST,
                port=settings.VECTOR_STORE_PORT,
                api_key=settings.VECTOR_STORE_API_KEY,
            )

        self._ensure_collection()
        self._ensure_payload_indexes()

    def _ensure_collection(self) -> None:
        if not self.client.collection_exists(self.collection):
            self.client.create_collection(
                collection_name=self.collection,
                vectors_config=models.VectorParams(
                    size=self.vector_size,
                    distance=models.Distance.COSINE,
                ),
            )

    def _safe_create_payload_index(self, field_name: str, field_schema: Any) -> None:
        """
        Create payload index in a version-tolerant way.
        """
        try:
            self.client.create_payload_index(
                collection_name=self.collection,
                field_name=field_name,
                field_schema=field_schema,
                wait=True,
            )
        except TypeError:
            self.client.create_payload_index(
                collection_name=self.collection,
                field_name=field_name,
                field_schema=field_schema,
            )

    def _ensure_payload_indexes(self) -> None:
        """
        Qdrant requires payload indexes for fields used in filtering.
        Current retrieval filters use at least:
        - user_id
        - subject
        - concepts
        """
        keyword_fields = [
            "document_id",
            "chunk_id",
            "subject",
            "source_type",
            "concepts",
        ]

        for field_name in keyword_fields:
            self._safe_create_payload_index(
                field_name=field_name,
                field_schema=models.PayloadSchemaType.KEYWORD,
            )

        # user_id from Supabase is UUID-like, but keyword is the safest compatible option
        self._safe_create_payload_index(
            field_name="user_id",
            field_schema=models.PayloadSchemaType.KEYWORD,
        )

    def _payload_from_chunk(self, chunk: Any) -> Dict[str, Any]:
        payload = chunk if isinstance(chunk, dict) else chunk.model_dump()
        metadata = payload.get("metadata", {}) or {}

        flattened = dict(payload)
        for key in (
            "chunk_id",
            "document_id",
            "source_document_id",
            "user_id",
            "subject",
            "source_type",
            "language",
            "concepts",
            "page_start",
            "page_end",
            "source_file",
        ):
            if key not in flattened and key in metadata:
                flattened[key] = metadata[key]

        return flattened

    def _point_uuid(self, payload: Dict[str, Any], index: int) -> str:
        chunk_id = payload.get("chunk_id")
        if chunk_id:
            return str(uuid.uuid5(uuid.NAMESPACE_DNS, str(chunk_id)))

        document_id = payload.get("document_id", "doc")
        text = payload.get("text", "")
        digest_seed = f"{document_id}:{index}:{hashlib.sha256(text.encode('utf-8')).hexdigest()}"
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, digest_seed))

    def upsert_chunks(
        self,
        chunks: List[Any],
        dense_vectors: Optional[List[List[float]]] = None,
        sparse_vectors: Optional[List[Dict[str, float]]] = None,
    ) -> None:
        if not chunks:
            return
        if not dense_vectors:
            raise ValueError("QdrantVectorStore requires dense_vectors for upsert.")
        if len(chunks) != len(dense_vectors):
            raise ValueError("dense_vectors length must match chunks length.")

        points: List[models.PointStruct] = []

        for i, chunk in enumerate(chunks):
            payload = self._payload_from_chunk(chunk)
            point_id = self._point_uuid(payload, i)

            points.append(
                models.PointStruct(
                    id=point_id,
                    vector=dense_vectors[i],
                    payload=payload,
                )
            )

        self.client.upsert(collection_name=self.collection, points=points)

    def search_dense(
        self,
        query_embedding: List[float],
        top_k: int,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        query_response = self.client.query_points(
            collection_name=self.collection,
            query=query_embedding,
            limit=top_k,
            query_filter=self._build_filter(filters),
            with_payload=True,
            with_vectors=False,
        )

        hits = getattr(query_response, "points", None)
        if hits is None and isinstance(query_response, dict):
            hits = query_response.get("points", [])

        results: List[Dict[str, Any]] = []
        for hit in hits or []:
            score = getattr(hit, "score", None)
            payload = getattr(hit, "payload", None)

            if score is None and isinstance(hit, dict):
                score = hit.get("score")
            if payload is None and isinstance(hit, dict):
                payload = hit.get("payload")

            results.append(
                {
                    "score": float(score or 0.0),
                    "payload": payload or {},
                }
            )

        return results

    def search_sparse(
        self,
        query_sparse: Dict[str, float],
        top_k: int,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        return []

    def _build_filter(self, filters: Optional[Dict[str, Any]]) -> Optional[models.Filter]:
        if not filters:
            return None

        must_conditions: List[models.FieldCondition] = []

        for key, value in filters.items():
            if key == "concepts":
                values = value if isinstance(value, list) else [value]
                must_conditions.append(
                    models.FieldCondition(
                        key="concepts",
                        match=models.MatchAny(any=values),
                    )
                )
                continue

            if isinstance(value, list):
                must_conditions.append(
                    models.FieldCondition(
                        key=key,
                        match=models.MatchAny(any=value),
                    )
                )
            else:
                must_conditions.append(
                    models.FieldCondition(
                        key=key,
                        match=models.MatchValue(value=value),
                    )
                )

        return models.Filter(must=must_conditions)