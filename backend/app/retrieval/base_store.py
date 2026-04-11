from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

class BaseVectorStore(ABC):
    """
    Abstract interface for all vector store implementations.
    Guarantees that both in-memory fallback and production Qdrant 
    will expose the exact same methods to the RetrievalService.
    """

    @abstractmethod
    def upsert_chunks(
        self,
        chunks: List[Any],
        dense_vectors: Optional[List[List[float]]] = None,
        sparse_vectors: Optional[List[Dict[str, float]]] = None,
    ) -> None:
        """Insert or update chunks along with their vector representations."""
        pass

    @abstractmethod
    def search_dense(
        self,
        query_embedding: List[float],
        top_k: int,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Perform semantic search using dense embeddings."""
        pass

    @abstractmethod
    def search_sparse(
        self,
        query_sparse: Dict[str, float],
        top_k: int,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Perform lexical/keyword search using sparse vectors."""
        pass