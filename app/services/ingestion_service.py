from __future__ import annotations

from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from ..db.repositories.chunk_repo import ChunkRepository
from ..db.repositories.document_repo import DocumentRepository
from ..schemas.chunk import Chunk
from ..schemas.document import DocumentCreate, DocumentMetadata
from ..services.document_service import DocumentService
from .retrieval_service import RetrievalService


class IngestionService:
    """
    High-level ingestion flow:
    document processing -> optional DB persistence -> optional retrieval indexing.
    """

    def __init__(
        self,
        doc_service: Optional[DocumentService] = None,
        chunk_repo: Optional[ChunkRepository] = None,
        document_repo: Optional[DocumentRepository] = None,
        retrieval_service: Optional[RetrievalService] = None,
    ) -> None:
        self.document_service = doc_service or DocumentService()
        self.chunk_repo = chunk_repo or ChunkRepository()
        self.document_repo = document_repo or DocumentRepository()
        self.retrieval_service = retrieval_service or RetrievalService()

    async def ingest_and_index(
        self,
        uploaded_bytes: bytes,
        original_filename: str,
        db: Optional[AsyncSession] = None,
        user_id: str = "system_user",
        subject: Optional[str] = None,
        language: str = "vi",
        persist_to_db: bool = True,
        index_for_retrieval: bool = True,
    ) -> List[Chunk]:
        """
        Run the full ingestion flow.
        If db is None, DB persistence is skipped.
        """
        doc_metadata, chunks = self.document_service.ingest_document(
            uploaded_bytes=uploaded_bytes,
            original_filename=original_filename,
            user_id=user_id,
            subject=subject,
            language=language,
        )

        actual_chunks = [chunk for chunk in chunks if chunk.text.strip()]
        if not actual_chunks:
            return []

        if persist_to_db and db is not None:
            doc_create = DocumentCreate.model_validate(doc_metadata.model_dump())
            stored_doc = await self.document_repo.create(doc_create, db)

            for chunk in actual_chunks:
                chunk.metadata.setdefault("document_id", stored_doc.document_id)
                chunk.metadata.setdefault("user_id", user_id)
                chunk.metadata.setdefault("subject", subject)

            await self.chunk_repo.save_chunks(stored_doc.document_id, actual_chunks, db)
            doc_metadata.document_id = stored_doc.document_id

        if index_for_retrieval:
            await self.retrieval_service.index_chunks(
                document_id=doc_metadata.document_id or "unknown_document",
                chunks=actual_chunks,
            )

        return actual_chunks