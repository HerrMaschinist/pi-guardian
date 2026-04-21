from __future__ import annotations

import hashlib
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

from guardian.app.alerting.models import (
    GuardianAlertDecision,
    GuardianAlertKind,
    GuardianAlertOutcome,
    GuardianAlertSendResult,
    GuardianAlertingConfig,
)
from guardian.app.alerting.telegram import GuardianTelegramClient
from guardian.app.core.domain import GuardianSeverity
from guardian.app.policy.models import GuardianPolicyDecision
from guardian.app.storage.models import GuardianAlertInput, GuardianAlertRecord, GuardianPersistenceReceipt
from guardian.app.storage.sqlite_store import GuardianSQLiteStore

if TYPE_CHECKING:
    from guardian.app.evaluators.overview import GuardianStatusResponse


class GuardianAlertingService:
    """Turns policy decisions into Telegram alerts with dedupe and cooldown."""

    def __init__(
        self,
        *,
        telegram_client: GuardianTelegramClient,
        config: GuardianAlertingConfig,
        store: GuardianSQLiteStore,
    ) -> None:
        self._telegram_client = telegram_client
        self._config = config
        self._store = store

    async def evaluate_and_dispatch(
        self,
        response: GuardianStatusResponse,
        policy: GuardianPolicyDecision,
        receipt: GuardianPersistenceReceipt,
    ) -> GuardianAlertDecision:
        alert_kind = self._classify_alert_kind(response, policy)
        telegram_ready, telegram_ready_reason = self._telegram_client.is_ready()
        alert_key = self._build_alert_key(response, policy, alert_kind)
        dedupe_key = self._dedupe_key(alert_key)
        reason_codes = [reason.code for reason in policy.reasons]
        decision_reason_codes = list(reason_codes)
        previous = await self._store.get_last_alert_for_key(alert_key)
        cooldown_remaining = self._cooldown_remaining_seconds(previous)
        should_send = self._should_send(
            response=response,
            policy=policy,
            receipt=receipt,
            alert_kind=alert_kind,
            telegram_ready=telegram_ready,
            cooldown_remaining_seconds=cooldown_remaining,
        )
        summary = self._summary_for(response, policy, alert_kind, should_send, cooldown_remaining)
        message_text = self._build_message_text(response, policy, alert_kind, alert_key, summary)
        outcome = GuardianAlertOutcome.SUPPRESS
        send_result: GuardianAlertSendResult | None = None
        sent = False
        suppressed_reason = self._suppressed_reason(
            response=response,
            policy=policy,
            receipt=receipt,
            alert_kind=alert_kind,
            telegram_ready=telegram_ready,
            cooldown_remaining_seconds=cooldown_remaining,
            should_send=should_send,
        )

        if should_send:
            send_result = await self._telegram_client.send_message(message_text)
            sent = send_result.ok
            if sent:
                outcome = GuardianAlertOutcome.SEND
            else:
                outcome = GuardianAlertOutcome.FAILED
                suppressed_reason = send_result.error
        else:
            outcome = GuardianAlertOutcome.SUPPRESS

        record = await self._store.record_alert(
            GuardianAlertInput(
                checked_at=response.checked_at,
                alert_key=alert_key,
                dedupe_key=dedupe_key,
                alert_kind=alert_kind.value,
                outcome=outcome.value,
                should_send=should_send,
                sent=sent,
                suppressed_reason=suppressed_reason,
                current_status=response.status,
                previous_status=policy.previous_status,
                policy_outcome=policy.outcome.value,
                changed=policy.changed,
                transition_relevant=policy.transition_relevant,
                cooldown_seconds=self._config.cooldown_seconds,
                cooldown_remaining_seconds=cooldown_remaining,
                telegram_ready=telegram_ready,
                telegram_ready_reason=telegram_ready_reason,
                telegram_chat_id=self._telegram_client.config.chat_id,
                telegram_message_id=send_result.message_id if send_result else None,
                telegram_error=send_result.error if send_result and not send_result.ok else None,
                reason_codes=decision_reason_codes,
                summary=summary,
                message_text=message_text,
                evidence={
                    "policy_visibility": policy.visibility.model_dump(mode="json"),
                    "policy_context": policy.context,
                    "persistence_ok": receipt.ok,
                    "last_alert_id": previous.id if previous else None,
                },
            )
        )

        return GuardianAlertDecision(
            outcome=outcome,
            alert_kind=alert_kind,
            should_send=should_send,
            sent=sent,
            suppressed=not should_send or not sent,
            summary=summary,
            reason_codes=reason_codes,
            alert_key=record.alert_key,
            dedupe_key=record.dedupe_key,
            cooldown_seconds=record.cooldown_seconds,
            cooldown_remaining_seconds=record.cooldown_remaining_seconds,
            policy_outcome=policy.outcome,
            current_status=response.status,
            previous_status=policy.previous_status,
            changed=policy.changed,
            transition_relevant=policy.transition_relevant,
            telegram_ready=telegram_ready,
            telegram_ready_reason=telegram_ready_reason,
            policy_visibility=policy.visibility,
            message_text=message_text,
            send_result=send_result,
            error=send_result.error if send_result and not send_result.ok else None,
            context={
                "snapshot_id": receipt.snapshot_id,
                "transition_id": receipt.transition_id,
                "persistence_ok": receipt.ok,
                "last_alert_id": previous.id if previous else None,
                "cooldown_remaining_seconds": cooldown_remaining,
                "alert_record_id": record.id,
            },
        )

    def _classify_alert_kind(self, response: GuardianStatusResponse, policy: GuardianPolicyDecision) -> GuardianAlertKind:
        if response.status == GuardianSeverity.CRITICAL:
            return GuardianAlertKind.CRITICAL
        if response.status == GuardianSeverity.WARN and policy.candidate_alert:
            if policy.visibility.auth_limited or policy.visibility.privilege_limited:
                return GuardianAlertKind.VISIBILITY
            return GuardianAlertKind.WARNING
        if (
            response.status == GuardianSeverity.OK
            and policy.previous_status in {GuardianSeverity.WARN, GuardianSeverity.CRITICAL}
            and policy.changed
        ):
            return GuardianAlertKind.RECOVERY
        return GuardianAlertKind.NONE

    def _should_send(
        self,
        *,
        response: GuardianStatusResponse,
        policy: GuardianPolicyDecision,
        receipt: GuardianPersistenceReceipt,
        alert_kind: GuardianAlertKind,
        telegram_ready: bool,
        cooldown_remaining_seconds: int | None,
    ) -> bool:
        if not self._config.enabled:
            return False
        if not telegram_ready:
            return False
        if not receipt.ok:
            return False
        if alert_kind == GuardianAlertKind.NONE:
            return False
        if cooldown_remaining_seconds is not None and cooldown_remaining_seconds > 0:
            return False
        if alert_kind == GuardianAlertKind.VISIBILITY:
            return False
        if alert_kind == GuardianAlertKind.WARNING:
            return policy.candidate_alert and not policy.visibility.auth_limited and not policy.visibility.privilege_limited
        if alert_kind == GuardianAlertKind.CRITICAL:
            return response.status == GuardianSeverity.CRITICAL
        if alert_kind == GuardianAlertKind.RECOVERY:
            return True
        return False

    def _suppressed_reason(
        self,
        *,
        response: GuardianStatusResponse,
        policy: GuardianPolicyDecision,
        receipt: GuardianPersistenceReceipt,
        alert_kind: GuardianAlertKind,
        telegram_ready: bool,
        cooldown_remaining_seconds: int | None,
        should_send: bool,
    ) -> str:
        if not self._config.enabled:
            return "alerting disabled"
        if not telegram_ready:
            return "telegram not configured"
        if not receipt.ok:
            return "persistence unavailable"
        if alert_kind == GuardianAlertKind.NONE:
            return "no alert-worthy condition"
        if alert_kind == GuardianAlertKind.VISIBILITY:
            return "visibility-limited state is suppressed"
        if cooldown_remaining_seconds is not None and cooldown_remaining_seconds > 0:
            return f"cooldown active for {cooldown_remaining_seconds}s"
        if response.status == GuardianSeverity.OK and policy.previous_status not in {GuardianSeverity.WARN, GuardianSeverity.CRITICAL}:
            return "stable ok state"
        if response.status == GuardianSeverity.WARN and (policy.visibility.auth_limited or policy.visibility.privilege_limited):
            return "auth or privilege limited warning suppressed"
        if not should_send:
            return "alert conditions not met"
        return ""

    def _summary_for(
        self,
        response: GuardianStatusResponse,
        policy: GuardianPolicyDecision,
        alert_kind: GuardianAlertKind,
        should_send: bool,
        cooldown_remaining_seconds: int | None,
    ) -> str:
        base = f"{response.status.value.upper()} via {policy.outcome.value}"
        if alert_kind == GuardianAlertKind.RECOVERY:
            return f"Recovery notification: {base}"
        if alert_kind == GuardianAlertKind.CRITICAL:
            return f"Critical alert: {base}"
        if alert_kind == GuardianAlertKind.WARNING:
            return f"Warning alert: {base}"
        if alert_kind == GuardianAlertKind.VISIBILITY:
            return f"Visibility-limited warning suppressed: {base}"
        if cooldown_remaining_seconds is not None and cooldown_remaining_seconds > 0:
            return f"Alert suppressed by cooldown: {base}"
        return f"Alert suppressed: {base}"

    def _build_alert_key(
        self,
        response: GuardianStatusResponse,
        policy: GuardianPolicyDecision,
        alert_kind: GuardianAlertKind,
    ) -> str:
        reason_codes = sorted({reason.code for reason in policy.reasons})
        visibility = policy.visibility
        stable = "|".join(
            [
                alert_kind.value,
                response.status.value,
                policy.outcome.value,
                policy.previous_status.value if policy.previous_status else "none",
                "changed" if policy.changed else "unchanged",
                "transition" if policy.transition_relevant else "notransition",
                "auth" if visibility.auth_limited else "noauth",
                "priv" if visibility.privilege_limited else "noroot",
                "data" if visibility.data_limited else "fulldata",
                ",".join(reason_codes) if reason_codes else "noreasons",
            ]
        )
        return stable

    def _dedupe_key(self, alert_key: str) -> str:
        return hashlib.sha256(alert_key.encode("utf-8")).hexdigest()

    def _cooldown_remaining_seconds(self, previous: GuardianAlertRecord | None) -> int | None:
        if previous is None:
            return None
        if self._config.cooldown_seconds <= 0:
            return None
        anchor = previous.sent_at or previous.checked_at
        expires_at = anchor + timedelta(seconds=self._config.cooldown_seconds)
        now = datetime.now(UTC)
        remaining = int((expires_at - now).total_seconds())
        return max(remaining, 0) if remaining > 0 else None

    def _build_message_text(
        self,
        response: GuardianStatusResponse,
        policy: GuardianPolicyDecision,
        alert_kind: GuardianAlertKind,
        alert_key: str,
        summary: str,
    ) -> str:
        router = response.router_evaluation
        system = response.system_evaluation
        lines = [
            "PI Guardian",
            f"Time: {response.checked_at.isoformat()}",
            f"Status: {response.status.value.upper()}",
            f"Policy: {policy.outcome.value} | Alert: {alert_kind.value}",
            f"Summary: {summary}",
            f"Router: {router.status.value} | {router.summary}",
            f"System: {system.status.value} | {system.summary}",
            f"Reasons: {', '.join(reason.code for reason in policy.reasons) or 'none'}",
            f"Policy changed: {policy.changed} | transition relevant: {policy.transition_relevant}",
            f"Visibility: auth={policy.visibility.auth_limited} root_limited={policy.visibility.privilege_limited} data_limited={policy.visibility.data_limited}",
            f"Alert key: {alert_key}",
        ]
        return "\n".join(lines)
