from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator

from .llm_config import LLMConfig


class ChatTurn(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="allow")

    role: str = Field(default="user")
    content: str = Field(default="")


class QueryRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True, extra="allow")

    query_text: str = Field(
        validation_alias=AliasChoices("query_text", "question"),
        serialization_alias="query_text",
        description="User question text.",
    )
    session_history: List[Union[str, ChatTurn]] = Field(
        default_factory=list,
        validation_alias=AliasChoices("session_history", "chat_history"),
        serialization_alias="session_history",
        description="Recent conversation history.",
    )
    context: Dict[str, Any] = Field(default_factory=dict)
    request_id: Optional[str] = None
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    subject_hint: Optional[str] = None
    study_mode: Optional[str] = None
    preferred_language: Optional[str] = None
    llm_config: Optional[LLMConfig] = None

    @field_validator("session_history", mode="before")
    @classmethod
    def _coerce_history(cls, value: Any) -> List[Union[str, ChatTurn]]:
        if value is None:
            return []
        if isinstance(value, list):
            return value
        return [value]

    @property
    def question(self) -> str:
        return self.query_text

    @property
    def chat_history(self) -> List[Union[str, ChatTurn]]:
        return self.session_history


class QueryAnalysis(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="allow")

    query_type: Optional[str] = None
    requires_multi_hop: bool = False
    subject: Optional[str] = None
    preferred_content_types: List[str] = Field(default_factory=list)
    difficulty: Optional[str] = None
    reason: Optional[str] = None


class QueryPlan(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="allow")

    sub_queries: List[str] = Field(default_factory=list)
    steps: List[Any] = Field(default_factory=list)
    stop_conditions: List[str] = Field(default_factory=list)


class QueryRead(QueryRequest):
    pass


Query = QueryRequest
