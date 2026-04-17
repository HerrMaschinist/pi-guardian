from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class MemoryStepRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    step_number: int
    action_type: str
    observation: str | None = None
    raw_payload: dict[str, Any]
    created_at: datetime


class MemoryToolCallRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    step_number: int
    tool_name: str
    arguments: dict[str, Any]
    reason: str
    created_at: datetime


class MemoryToolResultRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    step_number: int
    tool_name: str
    success: bool
    output: dict[str, Any] | list[Any] | str | int | float | bool | None
    error: str | None = None
    created_at: datetime


class MemorySkillRunRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    step_number: int
    skill_name: str
    arguments: dict[str, Any]
    reason: str
    success: bool
    output: dict[str, Any] | list[Any] | str | int | float | bool | None
    error: str | None = None
    created_at: datetime


class MemoryActionProposalRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    proposal_id: str
    run_id: str | None = None
    agent_name: str
    action_name: str
    arguments: dict[str, Any]
    reason: str
    target: str | None = None
    requires_approval: bool = True
    created_at: datetime


class MemoryActionExecutionRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    proposal_id: str
    run_id: str | None = None
    action_name: str
    approved: bool
    success: bool
    output: dict[str, Any] | list[Any] | str | int | float | bool | None
    error: str | None = None
    created_at: datetime


class MemoryApprovalRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    proposal_id: str
    approved_by: str | None = None
    approved_at: datetime
    decision: str
    comment: str | None = None


class MemoryRunSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str
    agent_name: str
    input: str
    used_model: str | None = None
    success: bool
    final_answer: str
    started_at: datetime
    finished_at: datetime | None = None


class MemoryRunDetail(MemoryRunSummary):
    steps: list[MemoryStepRead] = Field(default_factory=list)
    tool_calls: list[MemoryToolCallRead] = Field(default_factory=list)
    tool_results: list[MemoryToolResultRead] = Field(default_factory=list)
    skill_runs: list[MemorySkillRunRead] = Field(default_factory=list)
    action_proposals: list[MemoryActionProposalRead] = Field(default_factory=list)
    action_executions: list[MemoryActionExecutionRead] = Field(default_factory=list)
    approvals: list[MemoryApprovalRead] = Field(default_factory=list)


class MemoryIncidentFindingRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_type: str
    source_ref: str
    finding_type: str
    content: str
    confidence: float


class MemoryIncidentRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int
    title: str
    summary: str
    severity: str
    status: str
    related_run_id: str | None = None
    created_at: datetime
    updated_at: datetime
    findings: list[MemoryIncidentFindingRead] = Field(default_factory=list)


class MemoryKnowledgeEntryRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int
    title: str
    pattern: str
    probable_cause: str
    recommended_checks: str
    recommended_actions: str
    confidence: float
    confirmed: bool
    source: str
    created_at: datetime
    updated_at: datetime


class MemoryFeedbackEntryRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int
    related_run_id: str | None = None
    related_incident_id: int | None = None
    verdict: str
    comment: str
    created_by: str
    created_at: datetime


class MemoryIncidentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    summary: str = ""
    severity: str = "medium"
    status: str = "open"
    related_run_id: str | None = None


class MemoryIncidentFindingCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_type: str
    source_ref: str
    finding_type: str = ""
    content: str = ""
    confidence: float = 0.0


class MemoryKnowledgeCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    pattern: str = ""
    probable_cause: str = ""
    recommended_checks: str = ""
    recommended_actions: str = ""
    confidence: float = 0.0
    confirmed: bool = False
    source: str = ""


class MemoryFeedbackCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    related_run_id: str | None = None
    related_incident_id: int | None = None
    verdict: str
    comment: str = ""
    created_by: str = ""
