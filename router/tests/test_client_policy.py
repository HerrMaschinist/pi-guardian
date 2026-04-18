import asyncio
from types import SimpleNamespace

from app.router.auth import AuthorizedClientContext
from app.router.decision.models import RequestClassification, RequestDecision
from app.router.policy import ClientPolicyContext, apply_client_policy
from app.router.service import route_prompt
from app.schemas.request_models import RouteRequest


def test_apply_client_policy_blocks_tool_use_when_client_is_not_allowed():
    decision = RequestDecision(
        classification=RequestClassification.TOOL_REQUIRED,
        selected_model="qwen2.5-coder:1.5b",
        reasons=["Toolbedarf erkannt"],
        tool_hints=["docker_status"],
    )

    result = apply_client_policy(
        decision,
        ClientPolicyContext(can_use_llm=True, can_use_tools=False, can_use_internet=False),
    )

    assert result.classification is RequestClassification.BLOCKED
    assert result.blocked is True
    assert "Client-Policy erlaubt keine Tool-Nutzung" in result.reasons
    assert result.tool_hints == ["docker_status"]


def test_route_prompt_blocks_tool_request_for_limited_client(monkeypatch):
    session = SimpleNamespace()
    history_calls: list[dict] = []
    client_context = AuthorizedClientContext(
        client_id=1,
        name="limited-client",
        policy=ClientPolicyContext(
            can_use_llm=True,
            can_use_tools=False,
            can_use_internet=False,
        ),
    )

    def fake_create_route_history_entry(session, **kwargs):
        history_calls.append(kwargs)

    monkeypatch.setattr("app.router.service.create_route_history_entry", fake_create_route_history_entry)

    try:
        asyncio.run(
            route_prompt(
                RouteRequest(prompt="Bitte prüfe Docker und Service-Status"),
                session=session,
                client_context=client_context,
            )
        )
    except Exception as exc:
        assert exc.code == "request_blocked"
        assert exc.status_code == 403
    else:
        raise AssertionError("Tool-Request ohne Policy-Recht muss blockiert werden")

    assert len(history_calls) == 1
    assert history_calls[0]["client_name"] == "limited-client"
    assert history_calls[0]["decision_classification"] == "blocked"
