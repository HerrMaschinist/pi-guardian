import asyncio
from types import SimpleNamespace

from app.router.auth import AuthorizedClientContext
from app.router.errors import RouterApiError
from app.router.execution.models import RouteToolExecution
from app.router.policy import ClientPolicyContext
from app.router.service import route_prompt
from app.schemas.request_models import RouteRequest


def test_route_prompt_executes_supported_tools(monkeypatch):
    session = SimpleNamespace()
    history_calls: list[dict] = []
    client_context = AuthorizedClientContext(
        client_id=7,
        name="ops-admin",
        policy=ClientPolicyContext(
            can_use_llm=True,
            can_use_tools=True,
            can_use_internet=False,
        ),
    )

    async def fake_execute_tools(*, plans, request_id, policy_trace):
        assert len(plans) == 2
        assert [plan.tool_name for plan in plans] == ["system_status", "service_status"]
        assert request_id
        assert policy_trace.tool_execution_allowed is True
        return [
            RouteToolExecution(
                tool_name="system_status",
                arguments={},
                reason="Systemmetriken wurden als lokaler Read-Only-Status erkannt",
                success=True,
                duration_ms=4,
                output={
                    "uptime_seconds": 321.0,
                    "memory": {"used_percent": 38.5},
                    "disk": {"used_percent": 44.2},
                },
                error=None,
            ),
            RouteToolExecution(
                tool_name="service_status",
                arguments={"service_name": "ollama"},
                reason="Dienststatus für ollama wurde aus dem Prompt abgeleitet",
                success=True,
                duration_ms=3,
                output={
                    "service_name": "ollama",
                    "active_state": "active",
                    "sub_state": "running",
                },
                error=None,
            ),
        ]

    def fake_create_route_history_entry(_session, **kwargs):
        history_calls.append(kwargs)

    monkeypatch.setattr("app.router.service.route_execution_service.execute_tools", fake_execute_tools)
    monkeypatch.setattr("app.router.service.create_route_history_entry", fake_create_route_history_entry)

    response = asyncio.run(
        route_prompt(
            RouteRequest(prompt="Bitte prüfe Systemstatus und den ollama service"),
            session=session,
            client_context=client_context,
        )
    )

    assert response.decision_classification == "tool_required"
    assert response.execution_mode == "tool"
    assert response.model == "tool_executor"
    assert len(response.tool_executions) == 2
    assert response.policy_trace is not None
    assert response.policy_trace.tool_execution_allowed is True
    assert "Systemstatus gelesen" in response.response
    assert len(history_calls) == 1
    assert history_calls[0]["execution_mode"] == "tool"
    assert history_calls[0]["execution_status"] == "succeeded"
    assert history_calls[0]["executed_tools"] == ["system_status", "service_status"]


def test_route_prompt_marks_internet_requests_as_pending(monkeypatch):
    session = SimpleNamespace()
    history_calls: list[dict] = []
    client_context = AuthorizedClientContext(
        client_id=8,
        name="research-client",
        policy=ClientPolicyContext(
            can_use_llm=True,
            can_use_tools=False,
            can_use_internet=True,
        ),
    )

    def fake_create_route_history_entry(_session, **kwargs):
        history_calls.append(kwargs)

    monkeypatch.setattr("app.router.service.create_route_history_entry", fake_create_route_history_entry)

    try:
        asyncio.run(
            route_prompt(
                RouteRequest(prompt="Recherchiere online die aktuelle API-Dokumentation"),
                session=session,
                client_context=client_context,
            )
        )
    except RouterApiError as exc:
        assert exc.code == "internet_execution_unavailable"
        assert exc.status_code == 501
    else:
        raise AssertionError("Internet-Requests ohne Web-Layer müssen kontrolliert abbrechen")

    assert len(history_calls) == 1
    assert history_calls[0]["execution_mode"] == "internet_pending"
    assert history_calls[0]["execution_status"] == "failed"
    assert history_calls[0]["error_code"] == "internet_execution_unavailable"
