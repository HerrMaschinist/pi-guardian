from __future__ import annotations

from contextlib import asynccontextmanager
import asyncio

from fastapi import FastAPI, Request

from guardian.app.collectors import RouterCollector
from guardian.app.evaluators import GuardianStatusResponse, GuardianOverviewEvaluator, RouterEvaluator
from guardian.app.core.domain import GuardianHealth
from guardian.app.integrations.router_client import RouterReadClient, RouterReadConfig
from guardian.app.policy import GuardianPolicyEvaluator
from guardian.app.storage import GuardianSQLiteStore, GuardianSnapshotInput, GuardianStorageConfig
from guardian.app.system import SystemCollector, SystemEvaluator


@asynccontextmanager
async def lifespan(app: FastAPI):
    router_client = RouterReadClient(RouterReadConfig.from_env())
    guardian_store = GuardianSQLiteStore(GuardianStorageConfig.from_env())
    app.state.router_client = router_client
    app.state.router_collector = RouterCollector(router_client)
    app.state.router_evaluator = RouterEvaluator()
    app.state.system_collector = SystemCollector()
    app.state.system_evaluator = SystemEvaluator()
    app.state.overview_evaluator = GuardianOverviewEvaluator()
    app.state.policy_evaluator = GuardianPolicyEvaluator()
    app.state.guardian_store = guardian_store
    try:
        yield
    finally:
        await router_client.aclose()


app = FastAPI(
    title="PI Guardian",
    version="0.1.0",
    description="Independent control and recovery layer for the local PI router.",
    lifespan=lifespan,
)

_STARTED = GuardianHealth()


def _get_router_client(request: Request) -> RouterReadClient:
    client = getattr(request.app.state, "router_client", None)
    if client is None:
        client = RouterReadClient(RouterReadConfig.from_env())
        request.app.state.router_client = client
    return client


def _get_router_collector(request: Request) -> RouterCollector:
    collector = getattr(request.app.state, "router_collector", None)
    if collector is None:
        collector = RouterCollector(_get_router_client(request))
        request.app.state.router_collector = collector
    return collector


def _get_router_evaluator(request: Request) -> RouterEvaluator:
    evaluator = getattr(request.app.state, "router_evaluator", None)
    if evaluator is None:
        evaluator = RouterEvaluator()
        request.app.state.router_evaluator = evaluator
    return evaluator


def _get_system_collector(request: Request) -> SystemCollector:
    collector = getattr(request.app.state, "system_collector", None)
    if collector is None:
        collector = SystemCollector()
        request.app.state.system_collector = collector
    return collector


def _get_system_evaluator(request: Request) -> SystemEvaluator:
    evaluator = getattr(request.app.state, "system_evaluator", None)
    if evaluator is None:
        evaluator = SystemEvaluator()
        request.app.state.system_evaluator = evaluator
    return evaluator


def _get_overview_evaluator(request: Request) -> GuardianOverviewEvaluator:
    evaluator = getattr(request.app.state, "overview_evaluator", None)
    if evaluator is None:
        evaluator = GuardianOverviewEvaluator()
        request.app.state.overview_evaluator = evaluator
    return evaluator


def _get_policy_evaluator(request: Request) -> GuardianPolicyEvaluator:
    evaluator = getattr(request.app.state, "policy_evaluator", None)
    if evaluator is None:
        evaluator = GuardianPolicyEvaluator()
        request.app.state.policy_evaluator = evaluator
    return evaluator


def _get_guardian_store(request: Request) -> GuardianSQLiteStore:
    store = getattr(request.app.state, "guardian_store", None)
    if store is None:
        store = GuardianSQLiteStore(GuardianStorageConfig.from_env())
        request.app.state.guardian_store = store
    return store


def _build_snapshot_input(response: GuardianStatusResponse) -> GuardianSnapshotInput:
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


@app.get("/health", response_model=GuardianStatusResponse)
async def health(request: Request) -> GuardianStatusResponse:
    """Minimal Guardian health endpoint."""

    router_state, system_state = await asyncio.gather(
        _get_router_collector(request).collect(),
        _get_system_collector(request).collect(),
    )
    router_evaluation = _get_router_evaluator(request).evaluate(router_state)
    system_evaluation = _get_system_evaluator(request).evaluate(system_state)
    evaluation = _get_overview_evaluator(request).evaluate(router_evaluation, system_evaluation)
    guardian_status = evaluation.status
    response = GuardianStatusResponse(
        status=guardian_status,
        component=_STARTED.component,
        version=_STARTED.version,
        router=router_state,
        router_evaluation=router_evaluation,
        system=system_state,
        system_evaluation=system_evaluation,
        evaluation=evaluation,
    )
    store = _get_guardian_store(request)
    persistence = await store.record_cycle(_build_snapshot_input(response))
    policy = await _get_policy_evaluator(request).evaluate(response, persistence, store)
    return response.model_copy(update={"persistence": persistence, "policy": policy})
