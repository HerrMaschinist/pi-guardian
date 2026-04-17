import asyncio

from app.agents.runtime import run_agent
from app.models.agent_models import AgentRunRequest, ToolResult


def test_agent_runtime_completes_after_tool_call(monkeypatch):
    responses = iter(
        [
            {
                "response": '{"tool_name":"system_status","arguments":{},"reason":"Systemzustand erfassen"}'
            },
            {"response": "Systemzustand ist unauffällig."},
        ]
    )

    async def fake_generate_with_ollama(model, prompt, request_id, stream=False):
        return next(responses)

    async def fake_execute(tool_name, arguments, *, allowed_tools, context):
        return ToolResult(
            tool_name=tool_name,
            success=True,
            output={"uptime_seconds": 123},
            error=None,
        )

    monkeypatch.setattr("app.agents.runtime.generate_with_ollama", fake_generate_with_ollama)
    monkeypatch.setattr("app.agents.runtime.runtime.tool_executor.execute", fake_execute)

    result = asyncio.run(
        run_agent(
            AgentRunRequest.model_validate(
                {
                    "agent_name": "guardian_supervisor",
                    "input": "Analysiere den Systemzustand",
                    "max_steps": 3,
                }
            )
        )
    )

    assert result.success is True
    assert result.final_answer == "Systemzustand ist unauffällig."
    assert result.used_model is not None
    assert len(result.tool_calls) == 1
    assert result.steps[-1].action == "final_answer"


def test_agent_runtime_aborts_after_max_steps(monkeypatch):
    async def fake_generate_with_ollama(model, prompt, request_id, stream=False):
        return {
            "response": '{"tool_name":"forbidden_tool","arguments":{},"reason":"Nicht erlaubt"}'
        }

    monkeypatch.setattr("app.agents.runtime.generate_with_ollama", fake_generate_with_ollama)

    result = asyncio.run(
        run_agent(
            AgentRunRequest.model_validate(
                {
                    "agent_name": "guardian_supervisor",
                    "input": "Analysiere alles",
                    "max_steps": 2,
                }
            )
        )
    )

    assert result.success is False
    assert result.used_model is not None
    assert any("nicht für diesen Agenten erlaubt" in error for error in result.errors)
    assert "Maximale Schrittzahl" in result.final_answer


def test_service_diagnose_runtime_uses_safe_tools(monkeypatch):
    responses = iter(
        [
            {
                "response": '{"tool_name":"service_status","arguments":{"service_name":"ollama"},"reason":"Ollama-Dienst prüfen"}'
            },
            {"response": "Ollama läuft, keine akute Störung erkennbar."},
        ]
    )

    async def fake_generate_with_ollama(model, prompt, request_id, stream=False):
        return next(responses)

    async def fake_execute(tool_name, arguments, *, allowed_tools, context):
        return ToolResult(
            tool_name=tool_name,
            success=True,
            output={
                "service_name": arguments.get("service_name", "ollama"),
                "active_state": "active",
                "sub_state": "running",
            },
            error=None,
        )

    monkeypatch.setattr("app.agents.runtime.generate_with_ollama", fake_generate_with_ollama)
    monkeypatch.setattr("app.agents.runtime.runtime.tool_executor.execute", fake_execute)

    result = asyncio.run(
        run_agent(
            AgentRunRequest.model_validate(
                {
                    "agent_name": "service_diagnose",
                    "input": "Prüfe den ollama Dienst",
                    "max_steps": 3,
                }
            )
        )
    )

    assert result.success is True
    assert result.agent_name == "service_diagnose"
    assert result.used_model is not None
    assert len(result.tool_calls) == 1
    assert result.tool_calls[0].tool_name == "service_status"
    assert result.steps[-1].action == "final_answer"


def test_log_analyst_runtime_uses_router_logs(monkeypatch):
    responses = iter(
        [
            {
                "response": '{"tool_name":"router_logs","arguments":{"limit":3,"level":"error"},"reason":"Fehlerlog prüfen"}'
            },
            {"response": "Es gibt wiederkehrende Fehler im Router-Log, vermutlich durch Konfigurations- oder Verfügbarkeitsprobleme."},
        ]
    )

    async def fake_generate_with_ollama(model, prompt, request_id, stream=False):
        return next(responses)

    async def fake_execute(tool_name, arguments, *, allowed_tools, context):
        return ToolResult(
            tool_name=tool_name,
            success=True,
            output={
                "source": "router.log",
                "requested_limit": arguments.get("limit", 3),
                "returned_count": 2,
                "entries": [
                    {"level": "error", "source": "app.api.routes_agents", "message": "failed"},
                    {"level": "error", "source": "app.agents.runtime", "message": "timeout"},
                ],
            },
            error=None,
        )

    monkeypatch.setattr("app.agents.runtime.generate_with_ollama", fake_generate_with_ollama)
    monkeypatch.setattr("app.agents.runtime.runtime.tool_executor.execute", fake_execute)

    result = asyncio.run(
        run_agent(
            AgentRunRequest.model_validate(
                {
                    "agent_name": "log_analyst",
                    "input": "Analysiere aktuelle Router-Logs",
                    "max_steps": 3,
                }
            )
        )
    )

    assert result.success is True
    assert result.agent_name == "log_analyst"
    assert result.used_model is not None
    assert len(result.tool_calls) == 1
    assert result.tool_calls[0].tool_name == "router_logs"
    assert result.steps[-1].action == "final_answer"
