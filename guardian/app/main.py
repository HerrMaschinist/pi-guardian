from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request

from guardian.app.alerting import GuardianAlertingConfig, GuardianAlertingService, GuardianTelegramClient, GuardianTelegramConfig
from guardian.app.collectors import RouterCollector
from guardian.app.evaluators import GuardianStatusResponse, GuardianOverviewEvaluator, RouterEvaluator
from guardian.app.core.domain import GuardianHealth
from guardian.app.integrations.router_client import RouterReadClient, RouterReadConfig
from guardian.app.policy import GuardianPolicyEvaluator
from guardian.app.services import GuardianHealthService
from guardian.app.storage import GuardianHistoryResponse, GuardianSQLiteStore, GuardianStorageConfig
from guardian.app.system import SystemCollector, SystemEvaluator


@asynccontextmanager
async def lifespan(app: FastAPI):
    router_client = RouterReadClient(RouterReadConfig.from_env())
    guardian_store = GuardianSQLiteStore(GuardianStorageConfig.from_env())
    telegram_client = GuardianTelegramClient(GuardianTelegramConfig.from_env())
    alerting_service = GuardianAlertingService(
        telegram_client=telegram_client,
        config=GuardianAlertingConfig.from_env(),
        store=guardian_store,
    )
    app.state.router_client = router_client
    app.state.router_collector = RouterCollector(router_client)
    app.state.router_evaluator = RouterEvaluator()
    app.state.system_collector = SystemCollector()
    app.state.system_evaluator = SystemEvaluator()
    app.state.overview_evaluator = GuardianOverviewEvaluator()
    app.state.policy_evaluator = GuardianPolicyEvaluator()
    app.state.telegram_client = telegram_client
    app.state.alerting_service = alerting_service
    app.state.guardian_store = guardian_store
    app.state.health_service = GuardianHealthService(
        router_collector=app.state.router_collector,
        router_evaluator=app.state.router_evaluator,
        system_collector=app.state.system_collector,
        system_evaluator=app.state.system_evaluator,
        overview_evaluator=app.state.overview_evaluator,
        policy_evaluator=app.state.policy_evaluator,
        alerting_service=alerting_service,
        store=guardian_store,
    )
    try:
        yield
    finally:
        await router_client.aclose()
        await telegram_client.aclose()


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


@app.get("/history", response_model=GuardianHistoryResponse)
async def history(request: Request, limit: int = 10) -> GuardianHistoryResponse:
    """Read-only Guardian history endpoint for snapshots, transitions, and alerts."""

    store = _get_guardian_store(request)
    safe_limit = max(int(limit), 1)
    snapshots, transitions, alerts = await asyncio.gather(
        store.list_snapshots(limit=safe_limit),
        store.list_transitions(limit=safe_limit),
        store.list_alerts(limit=safe_limit),
    )
    return GuardianHistoryResponse(
        limit=safe_limit,
        snapshots=snapshots.items,
        transitions=transitions,
        alerts=alerts.items,
    )


@app.get("/health", response_model=GuardianStatusResponse)
async def health(request: Request) -> GuardianStatusResponse:
    """Minimal Guardian health endpoint."""

    service = getattr(request.app.state, "health_service", None)
    if service is None:
        service = GuardianHealthService(
            router_collector=_get_router_collector(request),
            router_evaluator=_get_router_evaluator(request),
            system_collector=_get_system_collector(request),
            system_evaluator=_get_system_evaluator(request),
            overview_evaluator=_get_overview_evaluator(request),
            policy_evaluator=_get_policy_evaluator(request),
            store=_get_guardian_store(request),
        )
        request.app.state.health_service = service
    return await service.run(_STARTED.component, _STARTED.version)
