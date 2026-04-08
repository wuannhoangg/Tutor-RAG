from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, AliasChoices, field_validator


class Citation(BaseModel):
    """Represents a single source citation mapping to a chunk."""

    model_config = ConfigDict(from_attributes=True, extra="allow")

    document_id: str = Field(description="ID of the source document.")
    chunk_id: Optional[str] = Field(default=None, description="ID of the chunk supporting the claim.")
    page_start: Optional[int] = Field(default=None, description="Starting page number of the evidence.")
    page_end: Optional[int] = Field(default=None, description="Ending page number of the evidence.")

    @field_validator("page_end", mode="before")
    @classmethod
    def _normalize_page_end(cls, value: Any) -> Any:
        return value


class AnswerResponse(BaseModel):
    """Final synthesized answer returned to the API/UI layer."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True, extra="allow")

    answer_text: str = Field(
        validation_alias=AliasChoices("answer_text", "answer"),
        serialization_alias="answer_text",
        description="The synthesized answer.",
    )
    reasoning_summary: List[str] = Field(
        default_factory=list,
        description="Short reasoning summary or evidence-backed steps.",
    )
    citations: List[Citation] = Field(
        default_factory=list,
        description="List of citations supporting the answer.",
    )
    confidence: Optional[float] = Field(
        default=None,
        description="Confidence score in the answer, if available.",
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional answer metadata.",
    )

    @field_validator("reasoning_summary", mode="before")
    @classmethod
    def _coerce_reasoning_summary(cls, value: Any) -> List[str]:
        if value is None:
            return []
        if isinstance(value, list):
            return [str(item) for item in value if str(item).strip()]
        if isinstance(value, str):
            text = value.strip()
            return [text] if text else []
        return [str(value)]

    @field_validator("confidence", mode="before")
    @classmethod
    def _coerce_confidence(cls, value: Any) -> Optional[float]:
        if value is None or value == "":
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None


class AnswerCreate(BaseModel):
    """Schema used when persisting an answer."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True, extra="allow")

    query_id: Optional[int] = None
    user_id: Optional[str] = None
    answer_text: str = Field(
        validation_alias=AliasChoices("answer_text", "answer"),
        serialization_alias="answer_text",
    )
    reasoning_summary: List[str] = Field(default_factory=list)
    citations: List[Citation] = Field(default_factory=list)
    confidence: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("reasoning_summary", mode="before")
    @classmethod
    def _coerce_reasoning_summary_create(cls, value: Any) -> List[str]:
        if value is None:
            return []
        if isinstance(value, list):
            return [str(item) for item in value if str(item).strip()]
        if isinstance(value, str):
            text = value.strip()
            return [text] if text else []
        return [str(value)]

    @field_validator("confidence", mode="before")
    @classmethod
    def _coerce_confidence_create(cls, value: Any) -> Optional[float]:
        if value is None or value == "":
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None