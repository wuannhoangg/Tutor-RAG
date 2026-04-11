from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, model_validator


class DocumentMetadata(BaseModel):
    """
    Flexible document metadata used by ingestion, DB, and API layers.
    """

    model_config = ConfigDict(from_attributes=True, populate_by_name=True, extra="allow")

    document_id: Optional[str] = Field(default=None, description="Unique document ID.")
    user_id: str = Field(default="system_user", description="Uploader or owner user ID.")
    subject: Optional[str] = Field(default=None, description="Document subject/domain.")
    title: Optional[str] = Field(default=None, description="Human-readable title.")
    source_type: Optional[str] = Field(default=None, description="Source type, e.g. pdf/docx/slides.")
    language: str = Field(default="vi", description="Language code.")
    file_name: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("file_name", "original_filename"),
        serialization_alias="file_name",
        description="Original file name.",
    )
    file_path: Optional[str] = Field(default=None, description="Storage path to the document.")
    mime_type: Optional[str] = Field(default=None, description="MIME type.")
    checksum_sha256: Optional[str] = Field(default=None, description="Optional SHA256 checksum.")
    tags: List[str] = Field(default_factory=list, description="User/system tags.")
    status: str = Field(default="uploaded", description="Current ingestion state.")
    uploaded_at: Optional[datetime] = Field(default=None, description="Upload timestamp.")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Flexible metadata payload.")

    @model_validator(mode="after")
    def _fill_file_name_from_path(self) -> "DocumentMetadata":
        if not self.file_name and self.file_path:
            self.file_name = Path(self.file_path).name
        return self

    @property
    def original_filename(self) -> Optional[str]:
        return self.file_name


class DocumentCreate(DocumentMetadata):
    """Schema used when creating a document record."""
    pass


class DocumentRead(DocumentMetadata):
    """Schema used when reading a document record."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True, extra="allow")