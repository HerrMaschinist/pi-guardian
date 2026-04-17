from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.agent_models import AgentPolicySettings


class SkillCall(BaseModel):
    model_config = ConfigDict(extra="forbid")

    skill_name: str = Field(..., min_length=1, pattern=r"^[a-z][a-z0-9_]*$")
    arguments: dict[str, Any] = Field(default_factory=dict)
    reason: str = Field(..., min_length=1)


class SkillDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=1, pattern=r"^[a-z][a-z0-9_]*$")
    description: str = Field(..., min_length=1)
    allowed_tools: list[str] = Field(default_factory=list)
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]
    read_only: bool = True
    version: str = Field(default="1.0", min_length=1)
    enabled: bool = True


class SkillResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    skill_name: str = Field(..., min_length=1, pattern=r"^[a-z][a-z0-9_]*$")
    success: bool
    output: Any = None
    error: str | None = None


class SkillExecutionContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    agent_name: str = Field(..., min_length=1)
    skill_name: str = Field(..., min_length=1)
    step_number: int = Field(..., ge=1)
    request_id: str | None = None
    allowed_skills: list[str] = Field(default_factory=list)
    policy: AgentPolicySettings = Field(default_factory=AgentPolicySettings)
