from __future__ import annotations

from fastapi.testclient import TestClient

from guardian.app.alerting import GuardianAlertingService
from guardian.app.collectors.router_collector import (
    GuardianRouterAccessState,
    GuardianRouterCollectorState,
    GuardianRouterReadinessState,
)
from guardian.app.core.domain import GuardianAction, GuardianSeverity
from guardian.app.evaluators import GuardianOverviewEvaluator, RouterEvaluator
from guardian.app.integrations.router_client import GuardianRouterProbe, RouterServiceStatusPayload
from guardian.app.main import app
from guardian.app.policy import GuardianPolicyEvaluator
from guardian.app.services import GuardianHealthService
from guardian.app.system import GuardianSystemCollectorState, SystemEvaluator


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
        checked_at="2026-04-21T00:00:00Z",
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
        checked_at="2026-04-21T00:00:00Z",
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


def test_history_endpoint_exposes_snapshot_transition_and_alerts(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("GUARDIAN_STORAGE_PATH", str(tmp_path / "guardian-ui.sqlite3"))
    monkeypatch.setenv("GUARDIAN_ALERTING_ENABLED", "false")

    with TestClient(app) as client:
        client.app.state.health_service = GuardianHealthService(
            router_collector=StaticCollector(build_router_state()),
            router_evaluator=RouterEvaluator(),
            system_collector=StaticCollector(build_system_state()),
            system_evaluator=SystemEvaluator(),
            overview_evaluator=GuardianOverviewEvaluator(),
            policy_evaluator=GuardianPolicyEvaluator(),
            alerting_service=client.app.state.alerting_service,
            store=client.app.state.guardian_store,
        )

        health_response = client.get("/health")
        history_response = client.get("/history?limit=3")

    assert health_response.status_code == 200
    assert health_response.json()["status"] == "ok"
    assert history_response.status_code == 200
    payload = history_response.json()
    assert payload["limit"] == 3
    assert len(payload["snapshots"]) == 1
    assert payload["snapshots"][0]["guardian_status"] == "ok"
    assert payload["alerts"]
