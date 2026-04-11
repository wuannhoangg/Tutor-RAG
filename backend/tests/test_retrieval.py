import pytest

from app.retrieval.embedder import Embedder
from app.retrieval.sparse_encoder import SparseEncoder
from app.retrieval.vector_store import VectorStore
from app.schemas.chunk import Chunk
from app.services.retrieval_service import RetrievalService


class StubEmbedder(Embedder):
    def __init__(self):
        self.model = None
        self.fallback_dim = 16
        self.model_name = "stub"

    def _token_value(self, token: str) -> int:
        return sum(ord(ch) for ch in token) % self.fallback_dim

    def embed_chunk(self, text: str):
        vector = [0.0] * self.fallback_dim
        for token in text.lower().split():
            vector[self._token_value(token)] += 1.0
        return vector

    def embed(self, texts):
        return [self.embed_chunk(text) for text in texts]


@pytest.mark.asyncio
async def test_full_retrieval_pipeline():
    embedder = StubEmbedder()
    vector_store = VectorStore(collection_name="test_chunks")
    sparse_encoder = SparseEncoder()

    service = RetrievalService(
        embedder=embedder,
        vector_store=vector_store,
        sparse_encoder=sparse_encoder,
    )

    chunks = [
        Chunk(
            text="BCNF is a stricter normal form than 3NF in database normalization.",
            metadata={
                "document_id": "doc_db",
                "chunk_id": "c1",
                "subject": "database",
                "user_id": "user_1",
                "page_start": 1,
                "page_end": 1,
            },
        ),
        Chunk(
            text="3NF removes transitive dependencies in many practical schemas.",
            metadata={
                "document_id": "doc_db",
                "chunk_id": "c2",
                "subject": "database",
                "user_id": "user_1",
                "page_start": 2,
                "page_end": 2,
            },
        ),
    ]

    indexed_count = await service.index_chunks("doc_db", chunks)
    assert indexed_count == 2

    evidence = service.retrieve_and_build_evidence(
        query="What is BCNF?",
        filters={"user_id": "user_1", "subject": "database"},
        top_k=2,
    )

    assert isinstance(evidence, list)
    assert len(evidence) >= 1
    assert evidence[0].document_id == "doc_db"
    assert evidence[0].retrieved_for == "What is BCNF?"