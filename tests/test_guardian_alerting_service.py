from __future__ import annotations

import asyncio
import json

import httpx

from guardian.app.alerting import GuardianAlertingConfig, GuardianAlertingService, GuardianTelegramClient, GuardianTelegramConfig
from guardian.app.collectors.router_collector import (
    GuardianRouterAccessState,
    GuardianRouterCollectorState,
    GuardianRouterReadinessState,
)
from guardian.app.core.domain import GuardianAction, GuardianSeverity, GuardianSignalSource
from guardian.app.evaluators import GuardianOverviewEvaluator, GuardianRouterEvaluation, GuardianStatusResponse
from guardian.app.evaluators.common import GuardianEvaluationReason
from guardian.app.integrations.router_client import GuardianRouterProbe, RouterServiceStatusPayload
from guardian.app.policy.models import GuardianPolicyDecision, GuardianPolicyOutcome, GuardianPolicyReason, GuardianPolicyVisibility
from guardian.app.storage import GuardianPersistenceReceipt, GuardianSQLiteStore, GuardianStorageConfig
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


def build_critical_response() -> GuardianStatusResponse:
    router_state = build_router_state()
    system_state = build_system_state()
    router_evaluation = GuardianRouterEvaluation(
        status=GuardianSeverity.OK,
        summary="Router is healthy.",
        reasons=[],
        router=router_state,
    )
    system_evaluation = GuardianSystemEvaluation(
        status=GuardianSeverity.CRITICAL,
        summary="System is critical.",
        reasons=[
            GuardianEvaluationReason(
                code="system_disk_critical",
                summary="Disk usage is critical.",
                severity=GuardianSeverity.CRITICAL,
                source=GuardianSignalSource.SYSTEM,
            )
        ],
        system=system_state,
    )
    overview = GuardianOverviewEvaluator().evaluate(router_evaluation, system_evaluation)
    return GuardianStatusResponse(
        status=overview.status,
        router=router_state,
        router_evaluation=router_evaluation,
        system=system_state,
        system_evaluation=system_evaluation,
        evaluation=overview,
    )


def build_critical_policy() -> GuardianPolicyDecision:
    return GuardianPolicyDecision(
        outcome=GuardianPolicyOutcome.ACTION_CANDIDATE,
        relevance=GuardianSeverity.CRITICAL,
        summary="Critical condition is actionable.",
        reasons=[
            GuardianPolicyReason(
                code="policy_new_critical",
                summary="New critical condition is actionable.",
                severity=GuardianSeverity.CRITICAL,
                source=GuardianSignalSource.EXTERNAL,
            )
        ],
        visibility=GuardianPolicyVisibility(),
        changed=True,
        transition_relevant=True,
        candidate_alert=True,
        candidate_action=True,
        deferred=True,
        confidence=0.95,
        current_status=GuardianSeverity.CRITICAL,
        previous_status=GuardianSeverity.WARN,
        snapshot_id=1,
        transition_id=1,
        persistence_ok=True,
        context={"snapshot_id": 1},
    )


def test_guardian_alerting_sends_once_and_suppresses_on_cooldown(tmp_path) -> None:
    requests: list[dict[str, object]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(
            {
                "path": request.url.path,
                "body": json.loads(request.content.decode("utf-8")),
            }
        )
        return httpx.Response(200, json={"ok": True, "result": {"message_id": len(requests)}})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="https://api.telegram.org")
    telegram = GuardianTelegramClient(
        GuardianTelegramConfig(
            bot_token="TOKEN",
            chat_id="CHAT",
            api_base_url="https://api.telegram.org",
            timeout_seconds=5.0,
        ),
        client=client,
    )
    store = GuardianSQLiteStore(GuardianStorageConfig(path=str(tmp_path / "guardian-alerts.sqlite3")))
    service = GuardianAlertingService(
        telegram_client=telegram,
        config=GuardianAlertingConfig(enabled=True, cooldown_seconds=3600),
        store=store,
    )

    response = build_critical_response()
    policy = build_critical_policy()
    receipt = GuardianPersistenceReceipt(
        ok=True,
        database_path=str(tmp_path / "guardian-alerts.sqlite3"),
        snapshot_id=1,
        transition_id=1,
        changed=True,
        previous_status=GuardianSeverity.WARN,
        current_status=GuardianSeverity.CRITICAL,
    )

    first = asyncio.run(service.evaluate_and_dispatch(response, policy, receipt))
    second = asyncio.run(service.evaluate_and_dispatch(response, policy, receipt))
    asyncio.run(telegram.aclose())

    assert first.outcome.value == "send"
    assert first.sent is True
    assert second.outcome.value == "suppress"
    assert second.should_send is False
    assert len(requests) == 1
    assert "CRITICAL" in requests[0]["body"]["text"]
