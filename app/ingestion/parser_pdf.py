from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Tuple

from ..schemas.document import DocumentMetadata


def _get_attr(obj: Any, *names: str, default: Any = None) -> Any:
    if obj is None:
        return default

    if isinstance(obj, dict):
        for name in names:
            if name in obj:
                return obj[name]
        return default

    for name in names:
        if hasattr(obj, name):
            return getattr(obj, name)
    return default


class PDFParser:
    """
    Extract text from PDF files using pypdf or PyPDF2.
    """

    def parse(self, file_path: str, source_metadata: DocumentMetadata) -> Tuple[str, List[dict]]:
        path = Path(file_path)

        if path.suffix.lower() != ".pdf":
            raise ValueError("Invalid file type for PDFParser.")
        if not path.exists():
            raise FileNotFoundError(f"PDF file not found: {file_path}")

        reader = self._get_reader(path)

        pieces: List[str] = []
        page_details: List[Dict[str, Any]] = []
        cursor = 0

        for page_index, page in enumerate(reader.pages, start=1):
            extracted = page.extract_text() or ""
            extracted = extracted.replace("\x00", "").strip()

            page_block = f"[Page {page_index}]\n{extracted}".strip()
            start_char = cursor
            pieces.append(page_block)
            cursor += len(page_block) + 2

            page_details.append(
                {
                    "page_number": page_index,
                    "start_char": start_char,
                    "end_char": cursor,
                    "text_excerpt": extracted[:300],
                }
            )

        raw_text = "\n\n".join(pieces).strip()
        return raw_text, page_details

    def _get_reader(self, path: Path):
        try:
            from pypdf import PdfReader  # type: ignore
            return PdfReader(str(path))
        except Exception:
            try:
                from PyPDF2 import PdfReader  # type: ignore
                return PdfReader(str(path))
            except Exception as exc:
                raise ImportError(
                    "PDF parsing requires 'pypdf' or 'PyPDF2' to be installed."
                ) from exc