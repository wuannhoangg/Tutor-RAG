from __future__ import annotations

from pathlib import Path
from typing import Optional


class LocalStorage:
    """
    Handle local persistence of uploaded files.
    """

    def __init__(self, base_dir: str = "local_storage") -> None:
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _resolve_unique_path(self, filename: str) -> Path:
        candidate = self.base_dir / filename
        if not candidate.exists():
            return candidate

        stem = candidate.stem
        suffix = candidate.suffix
        counter = 1

        while True:
            new_candidate = self.base_dir / f"{stem}_{counter}{suffix}"
            if not new_candidate.exists():
                return new_candidate
            counter += 1

    def save_file(self, file_bytes: bytes, filename: str) -> str:
        """
        Save file bytes to disk and return the absolute file path.
        """
        if not filename:
            raise ValueError("filename is required.")
        if not isinstance(file_bytes, (bytes, bytearray)):
            raise TypeError("file_bytes must be bytes-like.")

        path = self._resolve_unique_path(filename)
        path.write_bytes(bytes(file_bytes))
        return str(path.resolve())

    def read_file(self, file_path_or_name: str) -> bytes:
        """
        Read file bytes from an absolute path or from a filename under base_dir.
        """
        path = Path(file_path_or_name)
        if not path.is_absolute():
            path = self.base_dir / file_path_or_name

        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        return path.read_bytes()

    def get_file_path(self, filename: str) -> Optional[str]:
        """
        Get the absolute path for a file if it exists.
        """
        path = self.base_dir / filename
        if path.exists():
            return str(path.resolve())
        return None

    def exists(self, filename: str) -> bool:
        """
        Check whether a file exists under the storage directory.
        """
        return (self.base_dir / filename).exists()