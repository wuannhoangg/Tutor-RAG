from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class EvidenceItemSchema(BaseModel):
    """
    Evidence item schema used across retrieval, reasoning, and API responses.
    """

    model_config = ConfigDict(from_attributes=True, extra="allow")

    chunk_id: Optional[str] = Field(default=None, description="Chunk ID providing evidence.")
    document_id: Optional[str] = Field(default=None, description="Source document ID.")
    text: Optional[str] = Field(default=None, description="Full evidence text if available.")
    snippet: Optional[str] = Field(default=None, description="Short evidence snippet.")
    role: str = Field(default="support", description="Role of this evidence.")
    score: float = Field(default=0.0, description="Relevance score.")
    page_start: Optional[int] = Field(default=None, description="Starting page number.")
    page_end: Optional[int] = Field(default=None, description="Ending page number.")
    retrieved_for: Optional[str] = Field(default=None, description="Query this evidence was retrieved for.")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Flexible metadata.")

    @model_validator(mode="after")
    def _fill_snippet_and_pages(self) -> "EvidenceItemSchema":
        if self.snippet is None and self.text:
            self.snippet = self.text[:300]

        if self.page_end is None and self.page_start is not None:
            self.page_end = self.page_start

        return self


class EvidenceSet(BaseModel):
    """Container for a set of retrieved evidence items."""

    model_config = ConfigDict(from_attributes=True, extra="allow")

    items: List[EvidenceItemSchema] = Field(default_factory=list)
    average_score: Optional[float] = Field(default=None)

    @model_validator(mode="after")
    def _compute_average_score(self) -> "EvidenceSet":
        if self.average_score is None:
            if self.items:
                self.average_score = sum(item.score for item in self.items) / len(self.items)
            else:
                self.average_score = 0.0
        return self


Evidence = EvidenceItemSchema