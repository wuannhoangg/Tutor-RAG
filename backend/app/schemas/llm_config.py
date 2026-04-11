from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class LLMConfig(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="allow")

    mode: str = Field(default="platform_default")
    provider: Optional[str] = Field(default=None)
    api_key: Optional[str] = Field(default=None)
    base_url: Optional[str] = Field(default=None)
    model: Optional[str] = Field(default=None)