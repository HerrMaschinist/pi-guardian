from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

from guardian.app.core.domain import GuardianSeverity
from guardian.app.policy.models import GuardianPolicyOutcome, GuardianPolicyVisibility


class GuardianAlertKind(StrEnum):
    NONE = "none"
    WARNING = "warning"
    CRITICAL = "critical"
    RECOVERY = "recovery"
    VISIBILITY = "visibility"


class GuardianAlertOutcome(StrEnum):
    SEND = "send"
    SUPPRESS = "suppress"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class GuardianAlertingConfig:
    enabled: bool
    cooldown_seconds: int = 900

    @classmethod
    def from_env(cls) -> "GuardianAlertingConfig":
        import os

        enabled_raw = os.getenv("GUARDIAN_ALERTING_ENABLED", "true").strip().lower()
        cooldown_raw = (
            os.getenv("GUARDIAN_ALERTING_COOLDOWN_SECONDS")
            or os.getenv("GUARDIAN_ALERT_COOLDOWN_SECONDS")
            or "900"
        ).strip()
        try:
            cooldown_seconds = int(cooldown_raw)
        except ValueError:
            cooldown_seconds = 900
        return cls(
            enabled=enabled_raw not in {"0", "false", "no", "off"},
            cooldown_seconds=max(cooldown_seconds, 0),
        )


class GuardianAlertSendResult(BaseModel):
    ok: bool
    chat_id: str | None = None
    message_id: int | None = None
    status_code: int | None = None
    sent_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    error: str | None = None


class GuardianAlertDecision(BaseModel):
    outcome: GuardianAlertOutcome
    alert_kind: GuardianAlertKind
    should_send: bool
    sent: bool = False
    suppressed: bool = False
    summary: str
    reason_codes: list[str] = Field(default_factory=list)
    alert_key: str
    dedupe_key: str
    cooldown_seconds: int = 0
    cooldown_remaining_seconds: int | None = None
    policy_outcome: GuardianPolicyOutcome
    current_status: GuardianSeverity
    previous_status: GuardianSeverity | None = None
    changed: bool = False
    transition_relevant: bool = False
    telegram_ready: bool = False
    telegram_ready_reason: str = "unconfigured"
    policy_visibility: GuardianPolicyVisibility = Field(default_factory=GuardianPolicyVisibility)
    message_text: str = ""
    send_result: GuardianAlertSendResult | None = None
    error: str | None = None
    context: dict[str, Any] = Field(default_factory=dict)
