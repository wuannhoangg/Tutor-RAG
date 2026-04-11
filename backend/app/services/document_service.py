from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Tuple
from uuid import uuid4

from ..ingestion.chunker import DocumentChunker
from ..ingestion.normalizer import DocumentNormalizer
from ..ingestion.parser_docx import DOCXParser
from ..ingestion.parser_pdf import PDFParser
from ..ingestion.parser_pptx import PPTXParser
from ..schemas.chunk import Chunk
from ..schemas.document import DocumentMetadata
from ..storage.file_manager import FileManager


class DocumentService:
    """
    Orchestrates document ingestion:
    store file -> parse -> normalize -> chunk.
    """

    def __init__(
        self,
        file_manager: Optional[FileManager] = None,
        normalizer: Optional[DocumentNormalizer] = None,
        chunker: Optional[DocumentChunker] = None,
    ) -> None:
        self.file_manager = file_manager or FileManager()
        self.normalizer = normalizer or DocumentNormalizer()
        self.chunker = chunker or DocumentChunker()
        self.pdf_parser = PDFParser()
        self.docx_parser = DOCXParser()
        self.pptx_parser = PPTXParser()

    def _get_parser(self, file_extension: str):
        file_extension = file_extension.lower()
        if file_extension == ".pdf":
            return self.pdf_parser
        if file_extension == ".docx":
            return self.docx_parser
        if file_extension == ".pptx":
            return self.pptx_parser
        raise NotImplementedError(f"Parsing not supported for file type: {file_extension}")

    def ingest_document(
        self,
        uploaded_bytes: bytes,
        original_filename: str,
        user_id: str = "system_user",
        subject: Optional[str] = None,
        language: str = "vi",
    ) -> Tuple[DocumentMetadata, List[Chunk]]:
        """
        Process a raw uploaded file into normalized chunks.
        """
        if not uploaded_bytes:
            raise ValueError("uploaded_bytes is empty.")
        if not original_filename:
            raise ValueError("original_filename is required.")

        file_path = self.file_manager.save_document_bytes(uploaded_bytes, original_filename)
        path_obj = Path(file_path)
        ext = path_obj.suffix.lower()

        doc_metadata = DocumentMetadata(
            document_id=uuid4().hex,
            file_path=str(path_obj),
            file_name=original_filename,
            user_id=user_id,
            subject=subject,
            language=language,
            title=path_obj.stem,
            source_type=ext.lstrip("."),
            metadata={"original_filename": original_filename},
        )

        parser = self._get_parser(ext)
        raw_text, page_details = parser.parse(str(path_obj), doc_metadata)

        normalized_text = self.normalizer.normalize(raw_text, doc_metadata)
        normalization_metadata = self.normalizer.get_metadata()
        doc_metadata.metadata.update(normalization_metadata)

        chunks = self.chunker.chunk_text(
            normalized_text=normalized_text,
            source_metadata=doc_metadata,
            page_details=page_details,
        )

        return doc_metadata, chunks