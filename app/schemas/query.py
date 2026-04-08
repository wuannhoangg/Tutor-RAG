from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator


class ChatTurn(BaseModel):
    """One conversational turn used as query context."""

    model_config = ConfigDict(from_attributes=True, extra="allow")

    role: str = Field(default="user")
    content: str = Field(default="")


class QueryRequest(BaseModel):
    """
    Primary schema for chat/search requests.
    Supports aliases so it can accept both:
    - query_text / session_history
    - question / chat_history
    """

    model_config = ConfigDict(from_attributes=True, populate_by_name=True, extra="allow")

    query_text: str = Field(
        validation_alias=AliasChoices("query_text", "question"),
        serialization_alias="query_text",
        description="User question text.",
    )
    user_id: str = Field(default="system_user", description="User ID.")
    session_history: List[Union[str, ChatTurn]] = Field(
        default_factory=list,
        validation_alias=AliasChoices("session_history", "chat_history"),
        serialization_alias="session_history",
        description="Recent conversation history.",
    )
    context: Dict[str, Any] = Field(default_factory=dict, description="Optional explicit context.")
    request_id: Optional[str] = Field(default=None, description="Optional request ID.")
    session_id: Optional[str] = Field(default=None, description="Optional session ID.")
    subject_hint: Optional[str] = Field(default=None, description="Optional subject hint.")
    study_mode: Optional[str] = Field(default=None, description="Optional mode hint.")
    preferred_language: Optional[str] = Field(default=None, description="Preferred answer language.")

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
    """Structured understanding of the query."""

    model_config = ConfigDict(from_attributes=True, extra="allow")

    query_type: Optional[str] = Field(default=None, description="Classification label.")
    requires_multi_hop: bool = Field(default=False, description="Whether multiple reasoning hops are needed.")
    subject: Optional[str] = Field(default=None, description="Subject context.")
    preferred_content_types: List[str] = Field(default_factory=list, description="Preferred content types.")
    difficulty: Optional[str] = Field(default=None, description="Estimated difficulty.")
    reason: Optional[str] = Field(default=None, description="Why the query was classified this way.")


class QueryPlan(BaseModel):
    """Structured retrieval/reasoning plan."""

    model_config = ConfigDict(from_attributes=True, extra="allow")

    sub_queries: List[str] = Field(default_factory=list, description="Sub-queries derived from the question.")
    steps: List[Any] = Field(default_factory=list, description="Plan steps.")
    stop_conditions: List[str] = Field(default_factory=list, description="Optional stopping conditions.")


class QueryRead(QueryRequest):
    """Read schema for query request state."""
    pass


Query = QueryRequest