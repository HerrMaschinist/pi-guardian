from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, Field

from guardian.app.collectors.router_collector import (
    GuardianRouterAccessState,
    GuardianRouterCollectorState,
    GuardianRouterReadinessState,
)
from guardian.app.evaluators.common import GuardianEvaluationReason
from guardian.app.core.domain import GuardianSeverity, GuardianSignalSource


class GuardianRouterEvaluation(BaseModel):
    status: GuardianSeverity
    summary: str
    checked_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    reasons: list[GuardianEvaluationReason] = Field(default_factory=list)
    router: GuardianRouterCollectorState


class GuardianEvaluationResponse(BaseModel):
    status: GuardianSeverity
    component: str = "guardian"
    version: str = "0.1.0"
    checked_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    router: GuardianRouterCollectorState
    evaluation: GuardianRouterEvaluation


class RouterEvaluator:
    """Deterministically evaluates the normalized router state."""

    def evaluate(self, router_state: GuardianRouterCollectorState) -> GuardianRouterEvaluation:
        reasons: list[GuardianEvaluationReason] = []

        status = GuardianSeverity.OK
        summary = "Router state is healthy."

        if router_state.readiness_state == GuardianRouterReadinessState.INVALID:
            status = GuardianSeverity.CRITICAL
            summary = "Router state is invalid."
            reasons.append(
                GuardianEvaluationReason(
                    code="router_state_invalid",
                    summary="Collector reported an invalid router state.",
                    severity=GuardianSeverity.CRITICAL,
                    source=GuardianSignalSource.ROUTER,
                    detail="Collector marked the router response as invalid.",
                    evidence={
                        "readiness_state": router_state.readiness_state,
                        "access_state": router_state.access_state,
                        "health_path": router_state.health_path,
                        "status_path": router_state.status_path,
                    },
                )
            )
        elif (
            router_state.access_state == GuardianRouterAccessState.UNREACHABLE
            or router_state.readiness_state == GuardianRouterReadinessState.UNAVAILABLE
            or not router_state.reachable
        ):
            status = GuardianSeverity.CRITICAL
            summary = "Router is not reachable."
            reasons.append(
                GuardianEvaluationReason(
                    code="router_unreachable",
                    summary="Router health endpoint is not reachable.",
                    severity=GuardianSeverity.CRITICAL,
                    source=GuardianSignalSource.ROUTER,
                    detail="The collector could not establish a reliable router readout.",
                    evidence={
                        "reachable": router_state.reachable,
                        "access_state": router_state.access_state,
                        "readiness_state": router_state.readiness_state,
                        "base_url": router_state.base_url,
                    },
                )
            )
        elif router_state.service_status is not None and router_state.service_status.active is False:
            status = GuardianSeverity.CRITICAL
            summary = "Router service is inactive."
            reasons.append(
                GuardianEvaluationReason(
                    code="router_service_inactive",
                    summary="Router service status reports an inactive service.",
                    severity=GuardianSeverity.CRITICAL,
                    source=GuardianSignalSource.ROUTER,
                    detail="The router reported its service as inactive.",
                    evidence=router_state.service_status.model_dump(mode="json"),
                )
            )
        else:
            self._append_non_critical_reasons(router_state, reasons)
            if any(item.severity == GuardianSeverity.WARN for item in reasons):
                status = GuardianSeverity.WARN
                summary = "Router state is degraded or incomplete."

        if not reasons:
            reasons.append(
                GuardianEvaluationReason(
                    code="router_state_healthy",
                    summary="Router health and readout are consistent.",
                    severity=GuardianSeverity.OK,
                    source=GuardianSignalSource.ROUTER,
                    detail="The collector reported a healthy and reachable router state.",
                    evidence={
                        "readiness_state": router_state.readiness_state,
                        "access_state": router_state.access_state,
                        "healthy": router_state.healthy,
                        "degraded": router_state.degraded,
                        "incomplete": router_state.incomplete,
                        "auth_required": router_state.auth_required,
                    },
                )
            )

        return GuardianRouterEvaluation(
            status=status,
            summary=summary,
            reasons=reasons,
            router=router_state,
        )

    def _append_non_critical_reasons(
        self,
        router_state: GuardianRouterCollectorState,
        reasons: list[GuardianEvaluationReason],
    ) -> None:
        if router_state.auth_required:
            reasons.append(
                GuardianEvaluationReason(
                    code="router_extended_read_auth_required",
                    summary="Extended router read endpoint requires authentication.",
                    severity=GuardianSeverity.WARN,
                    source=GuardianSignalSource.ROUTER,
                    detail="Base health is readable, but one or more extended read endpoints require auth.",
                    evidence={
                        "access_state": router_state.access_state,
                        "readiness_state": router_state.readiness_state,
                        "health_path": router_state.health_path,
                        "status_path": router_state.status_path,
                    },
                )
            )

        if router_state.readiness_state == GuardianRouterReadinessState.DEGRADED or router_state.degraded:
            reasons.append(
                GuardianEvaluationReason(
                    code="router_degraded",
                    summary="Router reported a degraded state.",
                    severity=GuardianSeverity.WARN,
                    source=GuardianSignalSource.ROUTER,
                    detail="The collector normalized the router into a degraded state.",
                    evidence={
                        "health": router_state.health.model_dump(mode="json") if router_state.health else None,
                        "service_status": (
                            router_state.service_status.model_dump(mode="json")
                            if router_state.service_status
                            else None
                        ),
                    },
                )
            )

        if router_state.readiness_state in {
            GuardianRouterReadinessState.INCOMPLETE,
            GuardianRouterReadinessState.AUTH_REQUIRED,
        } or router_state.incomplete:
            reasons.append(
                GuardianEvaluationReason(
                    code="router_readout_incomplete",
                    summary="Router readout is incomplete.",
                    severity=GuardianSeverity.WARN,
                    source=GuardianSignalSource.ROUTER,
                    detail="The collector could not fully observe all requested router endpoints.",
                    evidence={
                        "incomplete": router_state.incomplete,
                        "auth_required": router_state.auth_required,
                        "findings": [finding.code for finding in router_state.findings],
                    },
                )
            )

        if router_state.health is not None:
            health_status = (router_state.health.status or "").strip().lower()
            if health_status == "ok" and router_state.access_state == GuardianRouterAccessState.REACHABLE:
                reasons.append(
                    GuardianEvaluationReason(
                        code="router_health_ok",
                        summary="Router base health endpoint reports ok.",
                        severity=GuardianSeverity.OK,
                        source=GuardianSignalSource.ROUTER,
                        evidence=router_state.health.model_dump(mode="json"),
                    )
                )
            elif health_status and health_status != "ok":
                severity = GuardianSeverity.WARN if health_status == "degraded" else GuardianSeverity.CRITICAL
                reasons.append(
                    GuardianEvaluationReason(
                        code="router_health_not_ok",
                        summary=f"Router health endpoint reported {health_status!r}.",
                        severity=severity,
                        source=GuardianSignalSource.ROUTER,
                        detail="The router health payload did not report a clean ok state.",
                        evidence=router_state.health.model_dump(mode="json"),
                    )
                )
