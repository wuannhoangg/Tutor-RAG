from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Chunk(BaseModel):
    """
    Lightweight chunk schema used by ingestion/reasoning pipelines.
    This is intentionally simple: text + flexible metadata.
    """

    model_config = ConfigDict(from_attributes=True, extra="allow")

    text: str = Field(description="Normalized chunk text.")
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Flexible metadata attached to the chunk.",
    )


class ChunkBase(BaseModel):
    """Structured chunk schema for DB/API-facing operations."""

    model_config = ConfigDict(from_attributes=True, extra="allow")

    chunk_id: Optional[str] = Field(default=None, description="Unique ID for the chunk.")
    document_id: Optional[str] = Field(default=None, description="Associated document ID.")
    user_id: Optional[str] = Field(default="system_user", description="User ID.")
    subject: Optional[str] = Field(default=None, description="Subject matter.")
    chapter: Optional[str] = Field(default=None, description="Chapter context.")
    section: Optional[str] = Field(default=None, description="Section context.")
    page_start: Optional[int] = Field(default=None, description="Starting page number.")
    page_end: Optional[int] = Field(default=None, description="Ending page number.")
    content_type: str = Field(default="paragraph", description="Chunk content type.")
    text: str = Field(description="Normalized chunk text.")
    token_count: Optional[int] = Field(default=None, description="Estimated token count.")
    keywords: List[str] = Field(default_factory=list, description="Extracted keywords.")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Flexible extra metadata.")

    @model_validator(mode="after")
    def _populate_defaults(self) -> "ChunkBase":
        if self.token_count is None:
            self.token_count = len((self.text or "").split())

        if self.page_end is None and self.page_start is not None:
            self.page_end = self.page_start

        return self


class ChunkCreate(ChunkBase):
    """Schema used to create a chunk record."""
    pass


class ChunkRead(ChunkBase):
    """Schema used to read a chunk record."""
    pass


class EvidenceItemCreate(BaseModel):
    """Schema for evidence items linked to retrieval output."""

    model_config = ConfigDict(from_attributes=True, extra="allow")

    chunk_id: Optional[str] = None
    document_id: Optional[str] = None
    role: str = Field(default="support")
    score: float = Field(default=0.0)
    page_start: Optional[int] = None
    page_end: Optional[int] = None
    retrieved_for: Optional[str] = None
    text: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)