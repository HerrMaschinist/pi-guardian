from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field

from guardian.app.core.domain import GuardianSeverity
from guardian.app.integrations.router_client import (
    GuardianFindingModel,
    GuardianRouterProbe,
    RouterEndpointErrorKind,
    RouterHealthPayload,
    RouterReadClient,
    RouterServiceStatusPayload,
)


class GuardianRouterAccessState(StrEnum):
    REACHABLE = "reachable"
    UNREACHABLE = "unreachable"
    AUTH_REQUIRED = "auth_required"
    PARTIAL = "partial"
    UNKNOWN = "unknown"


class GuardianRouterReadinessState(StrEnum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    INCOMPLETE = "incomplete"
    INVALID = "invalid"
    UNAVAILABLE = "unavailable"
    AUTH_REQUIRED = "auth_required"
    UNKNOWN = "unknown"


class GuardianRouterCollectorSummary(BaseModel):
    access_state: GuardianRouterAccessState
    readiness_state: GuardianRouterReadinessState
    severity: GuardianSeverity
    healthy: bool
    degraded: bool
    incomplete: bool
    auth_required: bool
    reachable: bool
    checked_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class GuardianRouterCollectorState(BaseModel):
    checked_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    base_url: str
    health_path: str
    status_path: str
    access_state: GuardianRouterAccessState
    readiness_state: GuardianRouterReadinessState
    severity: GuardianSeverity
    healthy: bool
    degraded: bool
    incomplete: bool
    auth_required: bool
    reachable: bool
    health: RouterHealthPayload | None = None
    service_status: RouterServiceStatusPayload | None = None
    findings: list[GuardianFindingModel] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
    probe: GuardianRouterProbe


class GuardianHealthResponse(BaseModel):
    status: GuardianSeverity
    component: str = "guardian"
    version: str = "0.1.0"
    checked_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    router: GuardianRouterCollectorState


class RouterCollector:
    """Normalizes router probe data into a Guardian-facing state."""

    def __init__(self, client: RouterReadClient) -> None:
        self._client = client

    async def collect(self) -> GuardianRouterCollectorState:
        probe = await self._client.probe()
        summary = self._summarize(probe)
        return GuardianRouterCollectorState(
            base_url=probe.router_base_url,
            health_path=probe.health_path,
            status_path=probe.status_path,
            access_state=summary.access_state,
            readiness_state=summary.readiness_state,
            severity=summary.severity,
            healthy=summary.healthy,
            degraded=summary.degraded,
            incomplete=summary.incomplete,
            auth_required=summary.auth_required,
            reachable=summary.reachable,
            health=probe.health,
            service_status=probe.service_status,
            findings=probe.findings,
            notes=self._notes_for_probe(probe),
            probe=probe,
        )

    def _summarize(self, probe: GuardianRouterProbe) -> GuardianRouterCollectorSummary:
        health_result = probe.health_result
        service_result = probe.service_status_result

        auth_required = bool(
            (health_result and health_result.auth_required)
            or (service_result and service_result.auth_required)
        )
        unreachable = bool(
            (health_result and health_result.unavailable)
            or (service_result and service_result.unavailable and not auth_required)
        )
        invalid = bool(
            (health_result and health_result.error_kind in {
                RouterEndpointErrorKind.INVALID_JSON,
                RouterEndpointErrorKind.INVALID_SHAPE,
                RouterEndpointErrorKind.INVALID_PAYLOAD,
            })
            or (service_result and service_result.error_kind in {
                RouterEndpointErrorKind.INVALID_JSON,
                RouterEndpointErrorKind.INVALID_SHAPE,
                RouterEndpointErrorKind.INVALID_PAYLOAD,
            })
        )

        healthy = (
            probe.health is not None
            and (probe.health.status or "").strip().lower() == "ok"
            and (probe.service_status is None or probe.service_status.active is not False)
            and not auth_required
            and not unreachable
            and not invalid
        )
        degraded = bool(
            probe.health is not None and (probe.health.status or "").strip().lower() == "degraded"
        ) or bool(probe.service_status is not None and probe.service_status.active is False)
        incomplete = bool(
            auth_required
            or (
                probe.health is not None
                and probe.service_status is None
                and not unreachable
                and not invalid
            )
        )

        if invalid:
            access_state = GuardianRouterAccessState.UNKNOWN
            readiness_state = GuardianRouterReadinessState.INVALID
            severity = GuardianSeverity.CRITICAL
        elif auth_required and unreachable:
            access_state = GuardianRouterAccessState.PARTIAL
            readiness_state = GuardianRouterReadinessState.INCOMPLETE
            severity = GuardianSeverity.WARN
        elif unreachable:
            access_state = GuardianRouterAccessState.UNREACHABLE
            readiness_state = GuardianRouterReadinessState.UNAVAILABLE
            severity = GuardianSeverity.CRITICAL
        elif auth_required:
            access_state = GuardianRouterAccessState.AUTH_REQUIRED
            readiness_state = GuardianRouterReadinessState.AUTH_REQUIRED
            severity = GuardianSeverity.INFO
        elif degraded:
            access_state = GuardianRouterAccessState.REACHABLE
            readiness_state = GuardianRouterReadinessState.DEGRADED
            severity = GuardianSeverity.WARN
        elif incomplete:
            access_state = GuardianRouterAccessState.PARTIAL
            readiness_state = GuardianRouterReadinessState.INCOMPLETE
            severity = GuardianSeverity.WARN
        elif healthy:
            access_state = GuardianRouterAccessState.REACHABLE
            readiness_state = GuardianRouterReadinessState.HEALTHY
            severity = GuardianSeverity.OK
        else:
            access_state = GuardianRouterAccessState.UNKNOWN
            readiness_state = GuardianRouterReadinessState.UNKNOWN
            severity = probe.status

        if probe.findings:
            if any(f.severity == GuardianSeverity.CRITICAL for f in probe.findings):
                severity = GuardianSeverity.CRITICAL
            elif severity == GuardianSeverity.OK and any(
                f.severity == GuardianSeverity.WARN for f in probe.findings
            ):
                severity = GuardianSeverity.WARN

        return GuardianRouterCollectorSummary(
            access_state=access_state,
            readiness_state=readiness_state,
            severity=severity,
            healthy=healthy,
            degraded=degraded,
            incomplete=incomplete,
            auth_required=auth_required,
            reachable=bool(probe.reachable or auth_required),
        )

    def _notes_for_probe(self, probe: GuardianRouterProbe) -> list[str]:
        notes: list[str] = []
        if probe.health_result and probe.health_result.auth_required:
            notes.append("Router health endpoint requires auth.")
        if probe.service_status_result and probe.service_status_result.auth_required:
            notes.append("Router service status endpoint requires auth.")
        if probe.health is not None and (probe.health.status or "").strip().lower() == "degraded":
            notes.append("Router health reports degraded.")
        if probe.service_status is not None and probe.service_status.active is False:
            notes.append("Router service status reports inactive service.")
        if not notes and probe.reachable:
            notes.append("Router probe completed successfully.")
        return notes
