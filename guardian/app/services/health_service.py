from __future__ import annotations

import asyncio

from guardian.app.alerting import GuardianAlertingService
from guardian.app.collectors import RouterCollector
from guardian.app.evaluators import GuardianOverviewEvaluator, GuardianStatusResponse, RouterEvaluator
from guardian.app.policy import GuardianPolicyEvaluator
from guardian.app.storage import GuardianSQLiteStore, GuardianSnapshotInput
from guardian.app.system import SystemCollector, SystemEvaluator


class GuardianHealthService:
    """Coordinates one Guardian read-evaluate-persist-policy cycle."""

    def __init__(
        self,
        *,
        router_collector: RouterCollector,
        router_evaluator: RouterEvaluator,
        system_collector: SystemCollector,
        system_evaluator: SystemEvaluator,
        overview_evaluator: GuardianOverviewEvaluator,
        policy_evaluator: GuardianPolicyEvaluator,
        alerting_service: GuardianAlertingService | None = None,
        store: GuardianSQLiteStore,
    ) -> None:
        self._router_collector = router_collector
        self._router_evaluator = router_evaluator
        self._system_collector = system_collector
        self._system_evaluator = system_evaluator
        self._overview_evaluator = overview_evaluator
        self._policy_evaluator = policy_evaluator
        self._alerting_service = alerting_service
        self._store = store

    async def run(self, started_component: str, started_version: str) -> GuardianStatusResponse:
        router_state, system_state = await asyncio.gather(
            self._router_collector.collect(),
            self._system_collector.collect(),
        )
        router_evaluation = self._router_evaluator.evaluate(router_state)
        system_evaluation = self._system_evaluator.evaluate(system_state)
        overview = self._overview_evaluator.evaluate(router_evaluation, system_evaluation)
        response = GuardianStatusResponse(
            status=overview.status,
            component=started_component,
            version=started_version,
            router=router_state,
            router_evaluation=router_evaluation,
            system=system_state,
            system_evaluation=system_evaluation,
            evaluation=overview,
        )
        persistence = await self._store.record_cycle(self._build_snapshot_input(response))
        policy = await self._policy_evaluator.evaluate(response, persistence, self._store)
        alerting = None
        if self._alerting_service is not None:
            alerting = await self._alerting_service.evaluate_and_dispatch(response, policy, persistence)
        return response.model_copy(update={"persistence": persistence, "policy": policy, "alerting": alerting})

    def _build_snapshot_input(self, response: GuardianStatusResponse) -> GuardianSnapshotInput:
        router_state = response.router
        system_state = response.system
        return GuardianSnapshotInput(
            checked_at=response.checked_at,
            guardian_status=response.status,
            router_status=response.router_evaluation.status,
            system_status=response.system_evaluation.status,
            overview_summary=response.evaluation.summary,
            router_summary=response.router_evaluation.summary,
            system_summary=response.system_evaluation.summary,
            overview_reason_codes=[reason.code for reason in response.evaluation.reasons],
            router_reason_codes=[reason.code for reason in response.router_evaluation.reasons],
            system_reason_codes=[reason.code for reason in response.system_evaluation.reasons],
            router_access_state=router_state.access_state.value,
            router_readiness_state=router_state.readiness_state.value,
            router_reachable=router_state.reachable,
            router_auth_required=router_state.auth_required,
            system_running_as_root=system_state.running_as_root,
            system_cpu_usage_percent=system_state.cpu_usage_percent,
            system_memory_usage_percent=system_state.memory_usage_percent,
            system_disk_usage_percent=system_state.disk_usage_percent,
            system_temperature_c=system_state.temperature_c,
            evidence={
                "router": {
                    "base_url": router_state.base_url,
                    "health_path": router_state.health_path,
                    "status_path": router_state.status_path,
                    "health_status": router_state.health.status if router_state.health else None,
                    "service_active": (
                        router_state.service_status.active if router_state.service_status is not None else None
                    ),
                },
                "system": {
                    "hostname": system_state.hostname,
                    "cpu_count": system_state.cpu_count,
                    "load_avg_1m": system_state.load_avg_1m,
                    "memory_available_bytes": system_state.memory_available_bytes,
                    "disk_mountpoint": system_state.disk_mountpoint,
                    "temperature_source": system_state.temperature_source,
                },
            },
        )
