from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.agent_models import AgentPolicySettings


class ToolExecutionContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    agent_name: str = Field(..., min_length=1)
    tool_name: str = Field(..., min_length=1)
    step_number: int = Field(..., ge=1)
    request_id: str | None = None
    allowed_tools: list[str] = Field(default_factory=list)
    tool_call_number: int = Field(default=1, ge=1)
    policy: AgentPolicySettings = Field(default_factory=AgentPolicySettings)


class ToolExecutionRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tool_name: str = Field(..., min_length=1)
    success: bool
    duration_ms: int = Field(..., ge=0)
    output: Any = None
    error: str | None = None
