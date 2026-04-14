from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class FeedbackCreate(BaseModel):
    """Schema for submitting user feedback."""

    model_config = ConfigDict(from_attributes=True, extra="allow")

    user_id: str = Field(default="system_user", description="User providing feedback.")
    answer_id: Optional[int] = Field(default=None, description="Related answer ID if available.")
    query_id: Optional[str] = Field(default=None, description="Related query ID if available.")
    rating: Optional[int] = Field(default=None, description="Optional numeric rating.")
    feedback_text: Optional[str] = Field(default=None, description="Feedback text content.")
    comment: Optional[str] = Field(default=None, description="Alternative feedback text field.")


class FeedbackRead(BaseModel):
    """Schema for reading stored feedback."""

    model_config = ConfigDict(from_attributes=True, extra="allow")

    feedback_id: int
    user_id: Optional[str] = None
    answer_id: Optional[int] = None
    query_id: Optional[str] = None
    rating: Optional[int] = None
    comment: Optional[str] = None
    created_at: Optional[datetime] = None