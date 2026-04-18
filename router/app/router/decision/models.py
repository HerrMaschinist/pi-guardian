from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class RequestClassification(str, Enum):
    LLM_ONLY = "llm_only"
    TOOL_REQUIRED = "tool_required"
    INTERNET_REQUIRED = "internet_required"
    BLOCKED = "blocked"


class RequestDecision(BaseModel):
    classification: RequestClassification
    selected_model: str | None = None
    reasons: list[str] = Field(default_factory=list)
    tool_hints: list[str] = Field(default_factory=list)
    internet_hints: list[str] = Field(default_factory=list)
    blocked: bool = False
