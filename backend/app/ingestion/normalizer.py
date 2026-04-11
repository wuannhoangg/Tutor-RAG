from __future__ import annotations

import re
import unicodedata
from datetime import datetime
from typing import Any, Dict

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


class DocumentNormalizer:
    """
    Normalize extracted text while preserving useful document structure.
    """

    def __init__(self) -> None:
        self._metadata: Dict[str, Any] = {}

    def normalize(self, raw_text: str, source_metadata: DocumentMetadata) -> str:
        """
        Clean extracted text but keep paragraphs and line structure.
        """
        if raw_text is None:
            raw_text = ""

        text = unicodedata.normalize("NFKC", raw_text)
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        text = text.replace("\x00", "")
        text = text.replace("\ufeff", "")
        text = text.replace("\u00ad", "")

        lines = text.split("\n")
        cleaned_lines = []

        for line in lines:
            line = line.replace("\t", " ")
            line = re.sub(r"[ ]{2,}", " ", line).strip()
            cleaned_lines.append(line)

        text = "\n".join(cleaned_lines)

        # Merge excessive blank lines but preserve paragraph structure.
        text = re.sub(r"\n{3,}", "\n\n", text)

        # Fix common hyphenation breaks from extraction.
        text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)

        # Trim spaces around newlines.
        text = re.sub(r"[ \t]+\n", "\n", text)
        text = re.sub(r"\n[ \t]+", "\n", text)

        normalized_text = text.strip()

        self._metadata = {
            "document_id": _get_attr(source_metadata, "document_id"),
            "normalized_at": datetime.utcnow().isoformat() + "Z",
            "raw_length": len(raw_text),
            "normalized_length": len(normalized_text),
        }

        return normalized_text

    def get_metadata(self) -> Dict[str, Any]:
        """Return metadata collected during the last normalization run."""
        return dict(self._metadata)