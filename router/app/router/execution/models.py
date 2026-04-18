from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class RouteExecutionMode(str, Enum):
    LLM = "llm"
    TOOL = "tool"
    INTERNET_PENDING = "internet_pending"


class RouteToolPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tool_name: str = Field(..., min_length=1)
    arguments: dict[str, Any] = Field(default_factory=dict)
    reason: str = Field(..., min_length=1)


class RoutePolicyTrace(BaseModel):
    model_config = ConfigDict(extra="forbid")

    can_use_llm: bool
    can_use_tools: bool
    can_use_internet: bool
    decision_classification: str
    tool_execution_allowed: bool
    internet_execution_allowed: bool


class RouteToolExecution(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tool_name: str = Field(..., min_length=1)
    arguments: dict[str, Any] = Field(default_factory=dict)
    reason: str = Field(..., min_length=1)
    success: bool
    duration_ms: int = Field(..., ge=0)
    output: Any = None
    error: str | None = None
