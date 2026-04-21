from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field

from guardian.app.core.domain import GuardianSeverity


class GuardianSnapshotInput(BaseModel):
    checked_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    guardian_status: GuardianSeverity
    router_status: GuardianSeverity
    system_status: GuardianSeverity
    overview_summary: str
    router_summary: str
    system_summary: str
    overview_reason_codes: list[str] = Field(default_factory=list)
    router_reason_codes: list[str] = Field(default_factory=list)
    system_reason_codes: list[str] = Field(default_factory=list)
    router_access_state: str
    router_readiness_state: str
    router_reachable: bool
    router_auth_required: bool
    system_running_as_root: bool
    system_cpu_usage_percent: float | None = None
    system_memory_usage_percent: float | None = None
    system_disk_usage_percent: float | None = None
    system_temperature_c: float | None = None
    evidence: dict[str, Any] = Field(default_factory=dict)


class GuardianSnapshotRecord(GuardianSnapshotInput):
    id: int
    stored_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class GuardianStateTransitionRecord(BaseModel):
    id: int
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    previous_snapshot_id: int | None = None
    current_snapshot_id: int
    from_status: GuardianSeverity
    to_status: GuardianSeverity
    reason_codes: list[str] = Field(default_factory=list)
    summary: str
    evidence: dict[str, Any] = Field(default_factory=dict)


class GuardianPersistenceReceipt(BaseModel):
    ok: bool
    database_path: str
    stored_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    snapshot_id: int | None = None
    transition_id: int | None = None
    changed: bool = False
    previous_status: GuardianSeverity | None = None
    current_status: GuardianSeverity | None = None
    error: str | None = None


class GuardianSnapshotHistory(BaseModel):
    items: list[GuardianSnapshotRecord] = Field(default_factory=list)
