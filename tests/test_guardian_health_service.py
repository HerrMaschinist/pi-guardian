from __future__ import annotations

import asyncio

from guardian.app.collectors.router_collector import (
    GuardianRouterAccessState,
    GuardianRouterCollectorState,
    GuardianRouterReadinessState,
)
from guardian.app.core.domain import GuardianAction, GuardianSeverity
from guardian.app.evaluators import GuardianOverviewEvaluator, RouterEvaluator
from guardian.app.integrations.router_client import GuardianRouterProbe, RouterServiceStatusPayload
from guardian.app.policy import GuardianPolicyEvaluator
from guardian.app.services import GuardianHealthService
from guardian.app.storage import GuardianSQLiteStore, GuardianStorageConfig
from guardian.app.system import GuardianSystemCollectorState, SystemCollector, SystemEvaluator


class StaticCollector:
    def __init__(self, value):
        self._value = value

    async def collect(self):
        return self._value


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
        readiness_state=GuardianRouterReadinessState.HEALTHY,
        severity=GuardianSeverity.OK,
        healthy=True,
        degraded=False,
        incomplete=False,
        auth_required=False,
        reachable=True,
        health=None,
        service_status=RouterServiceStatusPayload(service="pi-guardian-router", active=True, uptime="1h"),
        findings=[],
        notes=["Router probe completed successfully."],
        probe=probe,
    )


def build_system_state() -> GuardianSystemCollectorState:
    return GuardianSystemCollectorState(
        hostname="guardian-test",
        running_as_root=True,
        process_pid=1234,
        process_name="guardian",
        process_uptime_seconds=12.0,
        cpu_count=4,
        cpu_usage_percent=10.0,
        load_avg_1m=0.2,
        load_avg_5m=0.1,
        load_avg_15m=0.1,
        cpu_load_ratio_1m=0.05,
        memory_total_bytes=4 * 1024 * 1024 * 1024,
        memory_available_bytes=3 * 1024 * 1024 * 1024,
        memory_used_bytes=1 * 1024 * 1024 * 1024,
        memory_usage_percent=25.0,
        disk_mountpoint="/",
        disk_total_bytes=64 * 1024 * 1024 * 1024,
        disk_free_bytes=48 * 1024 * 1024 * 1024,
        disk_used_bytes=16 * 1024 * 1024 * 1024,
        disk_usage_percent=25.0,
        temperature_c=50.0,
        temperature_source="/sys/class/thermal/thermal_zone0/temp",
        notes=[],
        errors=[],
    )


def test_guardian_health_service_persists_and_policies_ok(tmp_path) -> None:
    store = GuardianSQLiteStore(GuardianStorageConfig(path=str(tmp_path / "guardian-health.sqlite3")))
    service = GuardianHealthService(
        router_collector=StaticCollector(build_router_state()),
        router_evaluator=RouterEvaluator(),
        system_collector=StaticCollector(build_system_state()),
        system_evaluator=SystemEvaluator(),
        overview_evaluator=GuardianOverviewEvaluator(),
        policy_evaluator=GuardianPolicyEvaluator(),
        store=store,
    )

    response = asyncio.run(service.run("guardian", "0.1.0"))

    assert response.persistence is not None
    assert response.persistence.ok is True
    assert response.policy is not None
    assert response.policy.outcome.value == "log_only"
    assert response.policy.persistence_ok is True
