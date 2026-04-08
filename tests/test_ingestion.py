import pytest
from unittest.mock import AsyncMock, MagicMock

from app.schemas.chunk import Chunk
from app.schemas.document import DocumentMetadata
from app.services.ingestion_service import IngestionService


@pytest.mark.asyncio
async def test_ingestion_pipeline_success():
    mock_doc_service = MagicMock()
    mock_chunk_repo = MagicMock()
    mock_document_repo = MagicMock()
    mock_retrieval_service = MagicMock()

    doc_metadata = DocumentMetadata(
        document_id="test_doc_id",
        file_path="/fake/path/test.pdf",
        file_name="test.pdf",
        user_id="user_1",
        subject="database",
        source_type="pdf",
    )
    chunks = [
        Chunk(
            text="Normalization is the process of organizing data.",
            metadata={
                "document_id": "test_doc_id",
                "source_file": "test.pdf",
                "page_start": 1,
                "page_end": 1,
            },
        )
    ]

    mock_doc_service.ingest_document.return_value = (doc_metadata, chunks)
    mock_document_repo.create = AsyncMock(return_value=doc_metadata)
    mock_chunk_repo.save_chunks = AsyncMock(return_value=[])
    mock_retrieval_service.index_chunks = AsyncMock(return_value=1)

    service = IngestionService(
        doc_service=mock_doc_service,
        chunk_repo=mock_chunk_repo,
        document_repo=mock_document_repo,
        retrieval_service=mock_retrieval_service,
    )

    db = AsyncMock()
    result = await service.ingest_and_index(
        uploaded_bytes=b"dummy pdf bytes",
        original_filename="test.pdf",
        db=db,
        user_id="user_1",
        subject="database",
    )

    assert len(result) == 1
    assert result[0].text.startswith("Normalization")

    mock_doc_service.ingest_document.assert_called_once()
    mock_document_repo.create.assert_awaited_once()
    mock_chunk_repo.save_chunks.assert_awaited_once()
    mock_retrieval_service.index_chunks.assert_awaited_once()


@pytest.mark.asyncio
async def test_ingestion_pipeline_returns_empty_when_no_chunks():
    mock_doc_service = MagicMock()
    mock_chunk_repo = MagicMock()
    mock_document_repo = MagicMock()
    mock_retrieval_service = MagicMock()

    doc_metadata = DocumentMetadata(
        document_id="empty_doc",
        file_path="/fake/path/empty.pdf",
        file_name="empty.pdf",
        source_type="pdf",
    )

    mock_doc_service.ingest_document.return_value = (doc_metadata, [])

    service = IngestionService(
        doc_service=mock_doc_service,
        chunk_repo=mock_chunk_repo,
        document_repo=mock_document_repo,
        retrieval_service=mock_retrieval_service,
    )

    result = await service.ingest_and_index(
        uploaded_bytes=b"dummy pdf bytes",
        original_filename="empty.pdf",
        db=None,
    )

    assert result == []
    assert not mock_chunk_repo.save_chunks.called
    assert not mock_retrieval_service.index_chunks.called