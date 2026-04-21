from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

from guardian.app.core.domain import GuardianSeverity, GuardianSignalSource


class GuardianPolicyOutcome(StrEnum):
    IGNORE = "ignore"
    LOG_ONLY = "log_only"
    OBSERVE = "observe"
    ALERT_CANDIDATE = "alert_candidate"
    ACTION_CANDIDATE = "action_candidate"
    DEFERRED = "deferred"


class GuardianPolicyVisibility(BaseModel):
    auth_limited: bool = False
    privilege_limited: bool = False
    data_limited: bool = False
    reduced_confidence: bool = False
    notes: list[str] = Field(default_factory=list)


class GuardianPolicyReason(BaseModel):
    code: str
    summary: str
    severity: GuardianSeverity
    source: GuardianSignalSource
    detail: str | None = None
    evidence: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class GuardianPolicyDecision(BaseModel):
    outcome: GuardianPolicyOutcome
    relevance: GuardianSeverity
    checked_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    summary: str
    reasons: list[GuardianPolicyReason] = Field(default_factory=list)
    visibility: GuardianPolicyVisibility = Field(default_factory=GuardianPolicyVisibility)
    changed: bool = False
    transition_relevant: bool = False
    candidate_alert: bool = False
    candidate_action: bool = False
    deferred: bool = False
    confidence: float = 1.0
    current_status: GuardianSeverity
    previous_status: GuardianSeverity | None = None
    snapshot_id: int | None = None
    transition_id: int | None = None
    persistence_ok: bool = True
    context: dict[str, Any] = Field(default_factory=dict)
