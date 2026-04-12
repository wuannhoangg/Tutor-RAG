from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

from .local_storage import LocalStorage


class FileManager:
    """
    Central manager for file operations using LocalStorage.
    """

    def __init__(self, base_storage_dir: str = "local_storage") -> None:
        self.storage = LocalStorage(base_dir=base_storage_dir)

    def _sanitize_filename(self, original_filename: str) -> str:
        name = (original_filename or "").strip()
        if not name:
            return "unnamed_document"

        # Keep alphanumeric, dot, dash, underscore.
        name = re.sub(r"[^A-Za-z0-9._-]+", "_", name)
        name = name.strip("._")
        return name or "unnamed_document"

    def save_document_bytes(self, file_bytes: bytes, original_filename: str) -> str:
        """
        Save raw document bytes and return the canonical local file path.
        """
        if not isinstance(file_bytes, (bytes, bytearray)) or len(file_bytes) == 0:
            raise ValueError("file_bytes must be non-empty bytes.")

        sanitized_filename = self._sanitize_filename(original_filename)
        return self.storage.save_file(bytes(file_bytes), sanitized_filename)

    def load_document_bytes(self, file_path: str) -> Optional[bytes]:
        """
        Load document bytes from a previously saved path.
        Returns None if the file cannot be read.
        """
        try:
            return self.storage.read_file(file_path)
        except FileNotFoundError:
            return None
        except Exception:
            return None