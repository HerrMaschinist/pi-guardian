from __future__ import annotations

from typing import TYPE_CHECKING

from guardian.app.core.domain import GuardianSeverity, GuardianSignalSource
from guardian.app.policy.models import (
    GuardianPolicyDecision,
    GuardianPolicyOutcome,
    GuardianPolicyReason,
    GuardianPolicyVisibility,
)
from guardian.app.storage.models import GuardianPersistenceReceipt, GuardianSnapshotHistory, GuardianStateTransitionRecord
from guardian.app.storage.sqlite_store import GuardianSQLiteStore

if TYPE_CHECKING:
    from guardian.app.evaluators.overview import GuardianStatusResponse


class GuardianPolicyEvaluator:
    """Turns Guardian assessments and persistence state into an operational policy decision."""

    async def evaluate(
        self,
        response: GuardianStatusResponse,
        receipt: GuardianPersistenceReceipt,
        store: GuardianSQLiteStore,
    ) -> GuardianPolicyDecision:
        snapshots = await store.list_snapshots(limit=5)
        transitions = await store.list_transitions(limit=5)
        previous_snapshot = snapshots.items[1] if len(snapshots.items) > 1 else None
        latest_transition = transitions[0] if transitions else None
        current_status = response.status
        previous_status = receipt.previous_status or (previous_snapshot.guardian_status if previous_snapshot else None)
        changed = bool(receipt.changed)
        transition_relevant = bool(changed or receipt.transition_id is not None)
        sustained_count = self._count_sustained_status(snapshots, current_status)

        visibility = self._build_visibility(response)
        confidence = self._confidence_for(visibility, receipt, sustained_count)
        reasons: list[GuardianPolicyReason] = []

        if not receipt.ok:
            reasons.append(
                GuardianPolicyReason(
                    code="policy_persistence_failed",
                    summary="Persistence failed, so policy is deferred.",
                    severity=GuardianSeverity.WARN,
                    source=GuardianSignalSource.STORAGE,
                    detail=receipt.error or "unknown persistence error",
                    evidence={"database_path": receipt.database_path, "snapshot_id": receipt.snapshot_id},
                )
            )
            return GuardianPolicyDecision(
                outcome=GuardianPolicyOutcome.DEFERRED,
                relevance=GuardianSeverity.WARN,
                summary="Policy deferred because persistence was not available.",
                reasons=reasons,
                visibility=GuardianPolicyVisibility(
                    auth_limited=visibility.auth_limited,
                    privilege_limited=visibility.privilege_limited,
                    data_limited=True,
                    reduced_confidence=True,
                    notes=visibility.notes + ["persistence unavailable"],
                ),
                changed=changed,
                transition_relevant=transition_relevant,
                candidate_alert=False,
                candidate_action=False,
                deferred=True,
                confidence=0.2,
                current_status=current_status,
                previous_status=previous_status,
                snapshot_id=receipt.snapshot_id,
                transition_id=receipt.transition_id,
                persistence_ok=False,
                context=self._build_context(
                    response,
                    receipt,
                    snapshots,
                    transitions,
                    sustained_count,
                    previous_status,
                ),
            )

        auth_limited = visibility.auth_limited
        privilege_limited = visibility.privilege_limited
        data_limited = visibility.data_limited

        if current_status == GuardianSeverity.OK:
            if previous_status in {GuardianSeverity.WARN, GuardianSeverity.CRITICAL}:
                reasons.append(
                    GuardianPolicyReason(
                        code="policy_recovery_observed",
                        summary="Guardian recovered to OK.",
                        severity=GuardianSeverity.OK,
                        source=GuardianSignalSource.EXTERNAL,
                        detail="A prior warning or critical condition improved back to OK.",
                        evidence={
                            "previous_status": previous_status.value if previous_status else None,
                            "current_status": current_status.value,
                            "transition_id": receipt.transition_id,
                        },
                    )
                )
                outcome = GuardianPolicyOutcome.OBSERVE
                candidate_alert = False
                candidate_action = False
                deferred = False
            elif auth_limited or privilege_limited or data_limited:
                reasons.append(
                    GuardianPolicyReason(
                        code="policy_visibility_limited_ok",
                        summary="OK state is visible but context is limited.",
                        severity=GuardianSeverity.INFO,
                        source=GuardianSignalSource.EXTERNAL,
                        detail="The state is healthy, but one or more visibility limits are present.",
                        evidence={
                            "auth_limited": auth_limited,
                            "privilege_limited": privilege_limited,
                            "data_limited": data_limited,
                        },
                    )
                )
                outcome = GuardianPolicyOutcome.OBSERVE
                candidate_alert = False
                candidate_action = False
                deferred = False
            else:
                outcome = GuardianPolicyOutcome.LOG_ONLY
                candidate_alert = False
                candidate_action = False
                deferred = False
                reasons.append(
                    GuardianPolicyReason(
                        code="policy_log_only_ok",
                        summary="Stable OK state is logged only.",
                        severity=GuardianSeverity.OK,
                        source=GuardianSignalSource.EXTERNAL,
                        evidence={
                            "changed": changed,
                            "transition_relevant": transition_relevant,
                            "sustained_count": sustained_count,
                        },
                    )
                )
        elif current_status == GuardianSeverity.WARN:
            hard_warning = self._is_hard_warning(response)
            if auth_limited and self._warn_is_auth_only(response):
                outcome = GuardianPolicyOutcome.OBSERVE
                candidate_alert = False
                candidate_action = False
                deferred = False
                reasons.append(
                    GuardianPolicyReason(
                        code="policy_auth_only_warning",
                        summary="Warning is driven by auth-limited observation only.",
                        severity=GuardianSeverity.INFO,
                        source=GuardianSignalSource.ROUTER,
                        detail="Base health is available; only extended router reads are auth-gated.",
                        evidence={
                            "router_reason_codes": [reason.code for reason in response.router_evaluation.reasons],
                            "status": current_status.value,
                        },
                    )
                )
            elif privilege_limited and not hard_warning:
                outcome = GuardianPolicyOutcome.OBSERVE
                candidate_alert = False
                candidate_action = False
                deferred = False
                reasons.append(
                    GuardianPolicyReason(
                        code="policy_privilege_limited_warning",
                        summary="Warning is influenced by limited privileges.",
                        severity=GuardianSeverity.INFO,
                        source=GuardianSignalSource.SYSTEM,
                        detail="Guardian is not running as root, so some system checks remain limited.",
                        evidence={"running_as_root": response.system.running_as_root},
                    )
                )
            else:
                candidate_alert = True
                candidate_action = False
                deferred = True
                if changed or previous_status is None:
                    outcome = GuardianPolicyOutcome.OBSERVE
                    reasons.append(
                        GuardianPolicyReason(
                            code="policy_new_warning",
                            summary="New warning observed and should be watched.",
                            severity=GuardianSeverity.WARN,
                            source=GuardianSignalSource.EXTERNAL,
                            evidence={
                                "previous_status": previous_status.value if previous_status else None,
                                "current_status": current_status.value,
                                "sustained_count": sustained_count,
                            },
                        )
                    )
                elif sustained_count >= 2:
                    outcome = GuardianPolicyOutcome.ALERT_CANDIDATE
                    reasons.append(
                        GuardianPolicyReason(
                            code="policy_sustained_warning",
                            summary="Warning persisted across multiple snapshots.",
                            severity=GuardianSeverity.WARN,
                            source=GuardianSignalSource.EXTERNAL,
                            evidence={
                                "sustained_count": sustained_count,
                                "latest_transition_id": latest_transition.id if latest_transition else None,
                            },
                        )
                    )
                else:
                    outcome = GuardianPolicyOutcome.OBSERVE
                    reasons.append(
                        GuardianPolicyReason(
                            code="policy_warning_observe",
                            summary="Warning is observable but not yet escalated.",
                            severity=GuardianSeverity.WARN,
                            source=GuardianSignalSource.EXTERNAL,
                            evidence={
                                "changed": changed,
                                "transition_relevant": transition_relevant,
                                "sustained_count": sustained_count,
                            },
                        )
                    )
        else:
            candidate_alert = True
            candidate_action = True
            deferred = True
            if changed or previous_status != GuardianSeverity.CRITICAL:
                outcome = GuardianPolicyOutcome.ACTION_CANDIDATE
                reasons.append(
                    GuardianPolicyReason(
                        code="policy_new_critical",
                        summary="New critical condition is actionable.",
                        severity=GuardianSeverity.CRITICAL,
                        source=GuardianSignalSource.EXTERNAL,
                        evidence={
                            "previous_status": previous_status.value if previous_status else None,
                            "current_status": current_status.value,
                            "transition_id": receipt.transition_id,
                        },
                    )
                )
            elif sustained_count >= 2:
                outcome = GuardianPolicyOutcome.ACTION_CANDIDATE
                reasons.append(
                    GuardianPolicyReason(
                        code="policy_sustained_critical",
                        summary="Critical condition persisted across multiple snapshots.",
                        severity=GuardianSeverity.CRITICAL,
                        source=GuardianSignalSource.EXTERNAL,
                        evidence={
                            "sustained_count": sustained_count,
                            "latest_transition_id": latest_transition.id if latest_transition else None,
                        },
                    )
                )
            else:
                outcome = GuardianPolicyOutcome.ACTION_CANDIDATE
                reasons.append(
                    GuardianPolicyReason(
                        code="policy_critical_observe",
                        summary="Critical condition remains action-worthy.",
                        severity=GuardianSeverity.CRITICAL,
                        source=GuardianSignalSource.EXTERNAL,
                        evidence={"sustained_count": sustained_count},
                    )
                )

        if auth_limited:
            reasons.append(
                GuardianPolicyReason(
                    code="policy_auth_limited",
                    summary="Policy context is limited by auth-gated router reads.",
                    severity=GuardianSeverity.INFO,
                    source=GuardianSignalSource.ROUTER,
                    evidence={"auth_required": response.router.auth_required},
                )
            )
        if privilege_limited:
            reasons.append(
                GuardianPolicyReason(
                    code="policy_privilege_limited",
                    summary="Policy context is limited because Guardian is not running as root.",
                    severity=GuardianSeverity.INFO,
                    source=GuardianSignalSource.SYSTEM,
                    evidence={"running_as_root": response.system.running_as_root},
                )
            )
        if data_limited:
            reasons.append(
                GuardianPolicyReason(
                    code="policy_data_limited",
                    summary="Policy context has reduced confidence because some signal is incomplete.",
                    severity=GuardianSeverity.WARN,
                    source=GuardianSignalSource.EXTERNAL,
                    evidence={
                        "router_reasons": [reason.code for reason in response.router_evaluation.reasons],
                        "system_reasons": [reason.code for reason in response.system_evaluation.reasons],
                    },
                )
            )

        if outcome in {GuardianPolicyOutcome.ALERT_CANDIDATE, GuardianPolicyOutcome.ACTION_CANDIDATE}:
            reasons.append(
                GuardianPolicyReason(
                    code="policy_deferred_until_followup_capabilities",
                    summary="The state is candidate-worthy but execution capabilities are not built yet.",
                    severity=GuardianSeverity.WARN if outcome == GuardianPolicyOutcome.ALERT_CANDIDATE else GuardianSeverity.CRITICAL,
                    source=GuardianSignalSource.EXTERNAL,
                    evidence={
                        "alert_candidate": candidate_alert,
                        "action_candidate": candidate_action,
                    },
                )
            )

        summary = self._summary_for(outcome, current_status, previous_status, changed, sustained_count)

        return GuardianPolicyDecision(
            outcome=outcome,
            relevance=current_status,
            summary=summary,
            reasons=reasons,
            visibility=visibility,
            changed=changed,
            transition_relevant=transition_relevant,
            candidate_alert=candidate_alert,
            candidate_action=candidate_action,
            deferred=deferred,
            confidence=confidence,
            current_status=current_status,
            previous_status=previous_status,
            snapshot_id=receipt.snapshot_id,
            transition_id=receipt.transition_id,
            persistence_ok=True,
            context=self._build_context(
                response,
                receipt,
                snapshots,
                transitions,
                sustained_count,
                previous_status,
            ),
        )

    def _build_visibility(self, response: GuardianStatusResponse) -> GuardianPolicyVisibility:
        auth_limited = any(reason.code == "router_extended_read_auth_required" for reason in response.router_evaluation.reasons)
        privilege_limited = not response.system.running_as_root
        data_limited = any(
            reason.code in {
                "router_readout_incomplete",
                "system_core_metrics_missing",
                "system_collection_errors",
            }
            for reason in [*response.router_evaluation.reasons, *response.system_evaluation.reasons]
        )
        notes: list[str] = []
        if auth_limited:
            notes.append("router reads are partially auth-gated")
        if privilege_limited:
            notes.append("guardian is not running as root")
        if data_limited:
            notes.append("collector data is incomplete")
        reduced_confidence = auth_limited or privilege_limited or data_limited
        return GuardianPolicyVisibility(
            auth_limited=auth_limited,
            privilege_limited=privilege_limited,
            data_limited=data_limited,
            reduced_confidence=reduced_confidence,
            notes=notes,
        )

    def _confidence_for(
        self,
        visibility: GuardianPolicyVisibility,
        receipt: GuardianPersistenceReceipt,
        sustained_count: int,
    ) -> float:
        confidence = 1.0
        if not receipt.ok:
            return 0.2
        if visibility.auth_limited:
            confidence -= 0.1
        if visibility.privilege_limited:
            confidence -= 0.15
        if visibility.data_limited:
            confidence -= 0.1
        if sustained_count >= 2:
            confidence += 0.05
        return max(0.2, min(confidence, 1.0))

    def _count_sustained_status(self, snapshots: GuardianSnapshotHistory, current_status: GuardianSeverity) -> int:
        count = 0
        for snapshot in snapshots.items:
            if snapshot.guardian_status == current_status:
                count += 1
            else:
                break
        return count

    def _summary_for(
        self,
        outcome: GuardianPolicyOutcome,
        current_status: GuardianSeverity,
        previous_status: GuardianSeverity | None,
        changed: bool,
        sustained_count: int,
    ) -> str:
        if outcome == GuardianPolicyOutcome.LOG_ONLY:
            return "Stable OK state recorded."
        if outcome == GuardianPolicyOutcome.OBSERVE and current_status == GuardianSeverity.OK:
            return "Recovered or limited OK state should be observed."
        if outcome == GuardianPolicyOutcome.OBSERVE and current_status == GuardianSeverity.WARN:
            return "Warning observed and tracked."
        if outcome == GuardianPolicyOutcome.ALERT_CANDIDATE:
            return "Warning is sustained and alert-worthy when alerting is available."
        if outcome == GuardianPolicyOutcome.ACTION_CANDIDATE:
            return "Critical condition is actionable when recovery is available."
        return "Policy decision deferred."

    def _is_hard_warning(self, response: GuardianStatusResponse) -> bool:
        hard_router = any(
            reason.code in {
                "router_degraded",
                "router_readout_incomplete",
                "router_health_not_ok",
            }
            for reason in response.router_evaluation.reasons
        )
        hard_system = any(
            reason.code
            in {
                "system_cpu_warn",
                "system_memory_warn",
                "system_disk_warn",
                "system_temperature_warn",
                "system_collection_errors",
                "system_core_metrics_missing",
            }
            for reason in response.system_evaluation.reasons
        )
        return hard_router or hard_system

    def _warn_is_auth_only(self, response: GuardianStatusResponse) -> bool:
        router_codes = {reason.code for reason in response.router_evaluation.reasons}
        system_codes = {reason.code for reason in response.system_evaluation.reasons}
        return router_codes.issubset({"router_extended_read_auth_required", "router_readout_incomplete"}) and not (
            system_codes - {"system_not_running_as_root"}
        )

    def _build_context(
        self,
        response: GuardianStatusResponse,
        receipt: GuardianPersistenceReceipt,
        snapshots: GuardianSnapshotHistory,
        transitions: list[GuardianStateTransitionRecord],
        sustained_count: int,
        previous_status: GuardianSeverity | None,
    ) -> dict[str, object]:
        return {
            "current_status": response.status.value,
            "previous_status": previous_status.value if previous_status else None,
            "changed": receipt.changed,
            "transition_relevant": bool(receipt.transition_id is not None or receipt.changed),
            "snapshot_id": receipt.snapshot_id,
            "transition_id": receipt.transition_id,
            "recent_statuses": [snapshot.guardian_status.value for snapshot in snapshots.items],
            "recent_transition_ids": [transition.id for transition in transitions],
            "sustained_count": sustained_count,
        }
