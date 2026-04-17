from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ActionProposal(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action_name: str = Field(..., min_length=1, pattern=r"^[a-z][a-z0-9_]*$")
    arguments: dict[str, Any] = Field(default_factory=dict)
    reason: str = Field(..., min_length=1)
    target: str | None = None
    requires_approval: bool = True


class ActionDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=1, pattern=r"^[a-z][a-z0-9_]*$")
    description: str = Field(..., min_length=1)
    allowed_targets: list[str] = Field(default_factory=list)
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]
    read_only: bool = False
    requires_approval: bool = True
    version: str = Field(default="1.0", min_length=1)
    enabled: bool = True


class ActionResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action_name: str = Field(..., min_length=1, pattern=r"^[a-z][a-z0-9_]*$")
    success: bool
    output: Any = None
    error: str | None = None


class ActionExecutionContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    agent_name: str = Field(..., min_length=1)
    action_name: str = Field(..., min_length=1)
    request_id: str | None = None
    approved: bool = False
    target: str | None = None


class ActionProposeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    agent_name: str = Field(..., min_length=1, pattern=r"^[a-z][a-z0-9_]*$")
    action_name: str = Field(..., min_length=1, pattern=r"^[a-z][a-z0-9_]*$")
    arguments: dict[str, Any] = Field(default_factory=dict)
    reason: str = Field(..., min_length=1)
    target: str | None = None


class ActionProposalRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    agent_name: str = Field(..., min_length=1, pattern=r"^[a-z][a-z0-9_]*$")
    action_name: str = Field(..., min_length=1, pattern=r"^[a-z][a-z0-9_]*$")
    arguments: dict[str, Any] = Field(default_factory=dict)
    reason: str = Field(..., min_length=1)
    target: str | None = None


class ActionExecuteRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    agent_name: str = Field(..., min_length=1, pattern=r"^[a-z][a-z0-9_]*$")
    action_name: str = Field(..., min_length=1, pattern=r"^[a-z][a-z0-9_]*$")
    arguments: dict[str, Any] = Field(default_factory=dict)
    reason: str = Field(..., min_length=1)
    target: str | None = None
    approved: bool = Field(default=False)
    proposal_id: str | None = None


class ActionProposalResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    proposal_id: str | None = None
    agent_name: str = Field(..., min_length=1, pattern=r"^[a-z][a-z0-9_]*$")
    proposal: ActionProposal
    action: ActionDefinition
