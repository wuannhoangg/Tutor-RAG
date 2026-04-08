from typing import Any, Dict, List, Optional
from qdrant_client import QdrantClient, models
from .base_store import BaseVectorStore
from app.core.config import get_settings

class QdrantVectorStore(BaseVectorStore):
    def __init__(self, collection_name: str = "tutorrag_chunks"):
        settings = get_settings()
        self.client = QdrantClient(host=settings.VECTOR_STORE_HOST, port=settings.VECTOR_STORE_PORT)
        self.collection = collection_name
        self._ensure_collection()

    def _ensure_collection(self):
        # Logic khởi tạo collection nếu chưa tồn tại
        pass

    def upsert_chunks(self, chunks, dense_vectors=None, sparse_vectors=None):
        points = []
        for i, chunk in enumerate(chunks):
            payload = chunk if isinstance(chunk, dict) else chunk.model_dump()
            points.append(models.PointStruct(
                id=payload.get("chunk_id", i),
                vector=dense_vectors[i] if dense_vectors else {},
                payload=payload
            ))
        self.client.upsert(collection_name=self.collection, points=points)

    def search_dense(self, query_embedding, top_k, filters=None):
        hits = self.client.search(
            collection_name=self.collection,
            query_vector=query_embedding,
            limit=top_k,
            query_filter=self._build_filter(filters)
        )
        return [{"score": hit.score, "payload": hit.payload} for hit in hits]

    def search_sparse(self, query_sparse, top_k, filters=None):
        # Qdrant hỗ trợ sparse vectors thông qua Named Vectors
        pass

    def _build_filter(self, filters):
        if not filters: return None
        return models.Filter(must=[
            models.FieldCondition(key=k, match=models.MatchValue(value=v))
            for k, v in filters.items()
        ])