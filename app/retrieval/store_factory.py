from app.core.config import get_settings
from .base_store import BaseVectorStore
from .in_memory_store import InMemoryVectorStore
from .qdrant_store import QdrantVectorStore

def get_vector_store() -> BaseVectorStore:
    settings = get_settings()
    # Nếu có cấu hình HOST thì ưu tiên Qdrant, nếu không thì dùng In-Memory
    if settings.VECTOR_STORE_HOST and settings.VECTOR_STORE_HOST != "localhost":
        try:
            return QdrantVectorStore()
        except Exception:
            return InMemoryVectorStore()
    return InMemoryVectorStore()