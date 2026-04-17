from __future__ import annotations

import asyncio

import pytest

from app.agents.registry import update_agent_settings
from app.agents.runtime import run_agent
from app.models.agent_models import (
    AgentBehaviorSettings,
    AgentDefinition,
    AgentPersonalitySettings,
    AgentPolicySettings,
    AgentRunRequest,
    AgentSettings,
    AgentSettingsUpdate,
)
from app.models.tool_models import ToolExecutionContext
from app.tools.executor import ToolExecutor


def _build_policy(allowed_tools: list[str], *, max_tool_calls: int | None = None) -> AgentPolicySettings:
    return AgentPolicySettings(
        allowed_tools=allowed_tools,
        read_only=True,
        can_use_logs=any(tool == "router_logs" or tool.endswith("_logs") for tool in allowed_tools),
        can_use_services="service_status" in allowed_tools,
        can_use_docker="docker_status" in allowed_tools,
        max_steps=5,
        max_tool_calls=max_tool_calls,
    )


def test_tool_executor_blocks_log_tools_when_policy_disallows():
    executor = ToolExecutor(timeout_seconds=1)
    context = ToolExecutionContext(
        agent_name="guardian_supervisor",
        tool_name="router_logs",
        step_number=1,
        request_id="req-1",
        allowed_tools=["router_logs"],
        tool_call_number=1,
        policy=_build_policy(["router_logs"], max_tool_calls=3).model_copy(update={"can_use_logs": False}),
    )

    result = asyncio.run(
        executor.execute(
            "router_logs",
            {"limit": 3},
            allowed_tools=["router_logs"],
            context=context,
        )
    )

    assert result.success is False
    assert "Logs sind für diesen Agenten nicht freigegeben" in (result.error or "")


def test_tool_executor_blocks_service_tools_when_policy_disallows():
    executor = ToolExecutor(timeout_seconds=1)
    context = ToolExecutionContext(
        agent_name="service_diagnose",
        tool_name="service_status",
        step_number=1,
        request_id="req-2",
        allowed_tools=["service_status"],
        tool_call_number=1,
        policy=_build_policy(["service_status"]).model_copy(update={"can_use_services": False}),
    )

    result = asyncio.run(
        executor.execute(
            "service_status",
            {"service_name": "ollama"},
            allowed_tools=["service_status"],
            context=context,
        )
    )

    assert result.success is False
    assert "Service-Tools sind für diesen Agenten nicht freigegeben" in (result.error or "")


def test_tool_executor_blocks_after_max_tool_calls():
    executor = ToolExecutor(timeout_seconds=1)
    context = ToolExecutionContext(
        agent_name="service_diagnose",
        tool_name="service_status",
        step_number=2,
        request_id="req-3",
        allowed_tools=["service_status"],
        tool_call_number=2,
        policy=_build_policy(["service_status"], max_tool_calls=1),
    )

    result = asyncio.run(
        executor.execute(
            "service_status",
            {"service_name": "ollama"},
            allowed_tools=["service_status"],
            context=context,
        )
    )

    assert result.success is False
    assert "Maximale Tool-Aufrufe überschritten" in (result.error or "")


def test_system_agent_policy_cannot_be_weakened():
    with pytest.raises(ValueError, match="System-Agenten dürfen max_steps nicht ändern"):
        update_agent_settings("guardian_supervisor", AgentSettingsUpdate(max_steps=10))

    with pytest.raises(ValueError, match="System-Agenten dürfen ihre Policy nicht ändern"):
        update_agent_settings(
            "guardian_supervisor",
            AgentSettingsUpdate(
                policy=_build_policy(["service_status"]).model_copy(update={"read_only": False})
            ),
        )


def test_agent_runtime_respects_max_tool_call_policy(monkeypatch):
    agent = AgentDefinition(
        name="policy_guard",
        description="Test agent",
        agent_type="custom",
        allowed_tools=["service_status"],
        settings=AgentSettings(
            active=True,
            preferred_model=None,
            max_steps=3,
            timeout_seconds=90,
            read_only=True,
            policy=_build_policy(["service_status"], max_tool_calls=1),
            behavior=AgentBehaviorSettings(),
            personality=AgentPersonalitySettings(),
            custom_instruction=None,
        ),
        system_prompt="pending",
    )

    responses = iter(
        [
            {
                "response": '{"tool_name":"service_status","arguments":{"service_name":"ollama"},"reason":"Dienst prüfen"}'
            },
            {
                "response": '{"tool_name":"service_status","arguments":{"service_name":"ollama"},"reason":"Nochmals prüfen"}'
            },
            {"response": "Dienststatus ist stabil."},
        ]
    )

    async def fake_generate_with_ollama(model, prompt, request_id, stream=False):
        return next(responses)

    monkeypatch.setattr("app.agents.runtime.generate_with_ollama", fake_generate_with_ollama)
    monkeypatch.setattr("app.agents.runtime.get_agent", lambda _name: agent)
    monkeypatch.setattr(
        "app.tools.service_status_tool._inspect_service",
        lambda service_name: {
            "service_name": service_name,
            "active_state": "active",
            "sub_state": "running",
            "main_pid": 123,
            "unit_file_state": "enabled",
            "fragment_path": "/etc/systemd/system/ollama.service",
            "description": "Ollama",
        },
    )

    result = asyncio.run(
        run_agent(
            AgentRunRequest.model_validate(
                {
                    "agent_name": "policy_guard",
                    "input": "Prüfe den Dienst mehrfach",
                    "max_steps": 3,
                }
            )
        )
    )

    assert result.success is True
    assert result.tool_calls[0].tool_name == "service_status"
    assert any("Maximale Tool-Aufrufe überschritten" in error for error in result.errors)
    assert result.final_answer == "Dienststatus ist stabil."
