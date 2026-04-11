from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field


class BaseMetadata(BaseModel):
    """Common metadata fields shared across entities."""

    model_config = ConfigDict(from_attributes=True, extra="allow")

    user_id: str = Field(default="system_user", description="Associated user ID.")
    subject: Optional[str] = Field(default=None, description="Primary subject domain.")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Flexible metadata payload.")


class CommonQueryMetadata(BaseMetadata):
    """Metadata fields commonly attached to a query."""

    query_type: Optional[str] = Field(default=None, description="Query classification.")
    difficulty: Optional[str] = Field(default=None, description="Estimated difficulty.")


class CommonChunkMetadata(BaseMetadata):
    """Metadata fields commonly attached to a chunk."""

    chapter: Optional[str] = Field(default=None, description="Chapter context.")
    section: Optional[str] = Field(default=None, description="Section context.")
    page_start: Optional[int] = Field(default=None, description="Starting page number.")
    page_end: Optional[int] = Field(default=None, description="Ending page number.")