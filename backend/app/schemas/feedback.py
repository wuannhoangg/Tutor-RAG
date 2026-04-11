from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class FeedbackCreate(BaseModel):
    """Schema for submitting user feedback."""

    model_config = ConfigDict(from_attributes=True, extra="allow")

    user_id: str = Field(default="system_user", description="User providing feedback.")
    query_id: Optional[str] = Field(default=None, description="Related query ID if available.")
    feedback_text: str = Field(description="Feedback text content.")


class FeedbackRead(BaseModel):
    """Schema for reading stored feedback."""

    model_config = ConfigDict(from_attributes=True, extra="allow")

    feedback_id: int
    user_id: Optional[str] = None
    query_id: Optional[str] = None
    feedback_text: str
    submitted_at: Optional[datetime] = None
