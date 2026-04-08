from __future__ import annotations
from typing import Any, Dict, List, Optional

from app.core import logging
from app.retrieval.dense_retriever import DenseRetriever
from app.retrieval.embedder import Embedder
from app.retrieval.evidence_builder import EvidenceBuilder
from app.retrieval.hybrid_retriever import HybridRetriever
from app.retrieval.reranker import Reranker
from app.retrieval.bm25_index import BM25Index
from app.retrieval.sparse_retriever import SparseRetriever
from app.retrieval.store_factory import get_vector_store
from app.retrieval.base_store import BaseVectorStore
from app.retrieval.cross_encoder_reranker import CrossEncoderReranker

logger = logging.logger.getChild("retrieval_service")

class RetrievalService:
    """
    Orchestrates retrieval:
    hybrid retrieve -> rerank -> evidence build.
    """

    def __init__(
        self,
        retriever: Optional[HybridRetriever] = None,
        reranker: Any = None,
        evidence_builder: Optional[EvidenceBuilder] = None,
        embedder: Optional[Embedder] = None,
        vector_store: Optional[BaseVectorStore] = None,
        bm25_index: Optional[BM25Index] = None,
    ) -> None:
        self.embedder = embedder or Embedder()
        self.vector_store = vector_store or get_vector_store()
        self.bm25_index = bm25_index or BM25Index()

        dense_retriever = DenseRetriever(
            embedder=self.embedder,
            vector_store=self.vector_store,
        )
        sparse_retriever = SparseRetriever(
            bm25_index=self.bm25_index,
        )

        self.retriever = retriever or HybridRetriever(
            dense_retriever=dense_retriever,
            sparse_retriever=sparse_retriever,
        )
        
        if reranker:
            self.reranker = reranker
        else:
            cross_encoder = CrossEncoderReranker()
            if cross_encoder.model is not None:
                self.reranker = cross_encoder
            else:
                logger.info("Falling back to deterministic lexical Reranker.")
                self.reranker = Reranker()

        self.evidence_builder = evidence_builder or EvidenceBuilder()

    async def index_chunks(self, document_id: str, chunks: List[Any]) -> int:
        """
        Generate dense representations for DB and update BM25 index on RAM.
        """
        texts: List[str] = []
        normalized_chunks: List[Any] = []

        for chunk in chunks:
            text = getattr(chunk, "text", None)
            if text is None and isinstance(chunk, dict):
                text = chunk.get("text")
            if not text or not str(text).strip():
                continue
            texts.append(str(text))
            normalized_chunks.append(chunk)

        if not normalized_chunks:
            return 0

        # 1. Tạo Dense Vector và đưa vào VectorStore (Qdrant/In-Memory)
        dense_vectors = self.embedder.embed(texts)
        
        for chunk in normalized_chunks:
            if hasattr(chunk, "metadata"):
                chunk.metadata.setdefault("document_id", document_id)
            elif isinstance(chunk, dict):
                chunk.setdefault("metadata", {})
                chunk["metadata"].setdefault("document_id", document_id)

        self.vector_store.upsert_chunks(
            chunks=normalized_chunks,
            dense_vectors=dense_vectors,
            sparse_vectors=None, # Không cần lưu sparse vector nữa do BM25 quản lý riêng
        )
        
        # 2. Cập nhật tập BM25
        self.bm25_index.add_chunks(normalized_chunks)

        return len(normalized_chunks)

    def retrieve_and_build_evidence(
        self,
        query: Any,
        filters: Optional[Dict[str, Any]] = None,
        top_k: int = 5,
    ) -> List[Any]:
        
        if isinstance(query, str):
            query_text = query.strip()
        else:
            query_text = getattr(query, "query_text", None) or getattr(query, "question", None) or ""
            query_text = str(query_text).strip()

        if not query_text:
            logger.warning("Cannot run retrieval: query text is missing.")
            return []

        raw_candidates = self.retriever.retrieve(
            query_text=query_text,
            top_k=max(top_k * 2, top_k),
            filters=filters or {},
        )
        
        if not raw_candidates:
            return []

        reranked_candidates = self.reranker.re_rank(
            candidates=raw_candidates,
            query_text=query_text,
            top_k=top_k,
        )

        evidence_list = self.evidence_builder.build_evidence(
            ranked_candidates=reranked_candidates,
            original_query=query_text,
        )
        return evidence_list