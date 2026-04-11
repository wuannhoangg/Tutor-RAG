from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ConceptBase(BaseModel):
    """Base schema for a concept."""

    model_config = ConfigDict(from_attributes=True, extra="allow")

    concept_id: str = Field(description="Unique identifier for the concept.")
    document_id: Optional[str] = Field(default=None, description="Source document ID.")
    subject: Optional[str] = Field(default=None, description="Subject domain.")
    text: str = Field(description="Textual concept content.")
    definition: Optional[str] = Field(default=None, description="Formal definition if available.")


class ConceptCreate(ConceptBase):
    """Schema for creating/updating a concept record."""
    pass


class ConceptRead(ConceptBase):
    """Schema for reading a concept record."""
    pass


class Prerequisite(BaseModel):
    """Dependency relationship between two concepts."""

    model_config = ConfigDict(from_attributes=True, extra="allow")

    prerequisite_concept_id: str = Field(description="Concept that should be understood first.")
    dependent_concept_id: str = Field(description="Concept depending on the prerequisite.")
    reasoning: Optional[str] = Field(default=None, description="Explanation for the dependency.")


class ConceptGraphData(BaseModel):
    """Container for concept graph relationships."""

    model_config = ConfigDict(from_attributes=True, extra="allow")

    prerequisites: List[Prerequisite] = Field(default_factory=list)
    related_concepts: List[str] = Field(default_factory=list)