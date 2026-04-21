from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field

from guardian.app.core.domain import GuardianSeverity, GuardianSignalSource


class GuardianEvaluationReason(BaseModel):
    code: str
    summary: str
    severity: GuardianSeverity
    source: GuardianSignalSource
    detail: str | None = None
    evidence: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
