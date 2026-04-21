from __future__ import annotations

import asyncio

from guardian.app.collectors.router_collector import (
    GuardianRouterAccessState,
    GuardianRouterCollectorState,
    GuardianRouterReadinessState,
)
from guardian.app.core.domain import GuardianAction, GuardianSeverity, GuardianSignalSource
from guardian.app.evaluators import GuardianOverviewEvaluator, GuardianRouterEvaluation, GuardianStatusResponse
from guardian.app.evaluators.common import GuardianEvaluationReason
from guardian.app.integrations.router_client import GuardianRouterProbe, RouterServiceStatusPayload
from guardian.app.policy import GuardianPolicyEvaluator
from guardian.app.storage import GuardianSQLiteStore, GuardianSnapshotInput, GuardianStorageConfig
from guardian.app.system import GuardianSystemCollectorState, GuardianSystemEvaluation


def build_router_state() -> GuardianRouterCollectorState:
    probe = GuardianRouterProbe(
        status=GuardianSeverity.OK,
        action=GuardianAction.NONE,
        reachable=True,
        service_active=True,
        health=None,
        service_status=RouterServiceStatusPayload(service="pi-guardian-router", active=True, uptime="1h"),
        findings=[],
        errors=[],
        router_base_url="http://127.0.0.1:8071",
    )
    return GuardianRouterCollectorState(
        base_url="http://127.0.0.1:8071",
        health_path="/health",
        status_path="/status/service",
        access_state=GuardianRouterAccessState.REACHABLE,
        readiness_state=GuardianRouterReadinessState.AUTH_REQUIRED,
        severity=GuardianSeverity.INFO,
        healthy=False,
        degraded=False,
        incomplete=False,
        auth_required=True,
        reachable=True,
        health=None,
        service_status=RouterServiceStatusPayload(service="pi-guardian-router", active=True, uptime="1h"),
        findings=[],
        notes=[],
        probe=probe,
    )


def build_system_state() -> GuardianSystemCollectorState:
    return GuardianSystemCollectorState(
        hostname="guardian-test",
        running_as_root=True,
        process_pid=1234,
        process_name="guardian",
    )


def test_guardian_policy_auth_only_warning_is_observe(tmp_path) -> None:
    router_state = build_router_state()
    system_state = build_system_state()
    router_evaluation = GuardianRouterEvaluation(
        status=GuardianSeverity.WARN,
        summary="Router read is auth-gated.",
        reasons=[
            GuardianEvaluationReason(
                code="router_extended_read_auth_required",
                summary="Extended router read endpoint requires authentication.",
                severity=GuardianSeverity.WARN,
                source=GuardianSignalSource.ROUTER,
            )
        ],
        router=router_state,
    )
    system_evaluation = GuardianSystemEvaluation(
        status=GuardianSeverity.OK,
        summary="System is healthy.",
        reasons=[],
        system=system_state,
    )
    overview = GuardianOverviewEvaluator().evaluate(router_evaluation, system_evaluation)
    response = GuardianStatusResponse(
        status=overview.status,
        router=router_state,
        router_evaluation=router_evaluation,
        system=system_state,
        system_evaluation=system_evaluation,
        evaluation=overview,
    )

    store = GuardianSQLiteStore(GuardianStorageConfig(path=str(tmp_path / "guardian-policy.sqlite3")))
    persistence = asyncio.run(
        store.record_cycle(
            GuardianSnapshotInput(
                guardian_status=response.status,
                router_status=response.router_evaluation.status,
                system_status=response.system_evaluation.status,
                overview_summary=response.evaluation.summary,
                router_summary=response.router_evaluation.summary,
                system_summary=response.system_evaluation.summary,
                overview_reason_codes=[reason.code for reason in response.evaluation.reasons],
                router_reason_codes=[reason.code for reason in response.router_evaluation.reasons],
                system_reason_codes=[reason.code for reason in response.system_evaluation.reasons],
                router_access_state=response.router.access_state.value,
                router_readiness_state=response.router.readiness_state.value,
                router_reachable=response.router.reachable,
                router_auth_required=response.router.auth_required,
                system_running_as_root=response.system.running_as_root,
            )
        )
    )
    policy = asyncio.run(GuardianPolicyEvaluator().evaluate(response, persistence, store))

    assert policy.outcome.value == "observe"
    assert policy.visibility.auth_limited is True
    assert policy.candidate_alert is False
    assert policy.deferred is False
