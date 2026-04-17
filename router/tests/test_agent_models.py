import pytest

from pydantic import ValidationError

from app.models.agent_models import (
    AgentBehaviorSettings,
    AgentDefinition,
    AgentPersonalitySettings,
    AgentRunRequest,
    AgentSettings,
    ToolCall,
)


def test_agent_run_request_accepts_input_alias_and_trims():
    request = AgentRunRequest.model_validate(
        {
            "agent_name": "guardian_supervisor",
            "input": "  Bitte prüfe den Zustand  ",
            "preferred_model": "  qwen2.5-coder:1.5b  ",
            "max_steps": 3,
        }
    )

    assert request.agent_name == "guardian_supervisor"
    assert request.prompt == "Bitte prüfe den Zustand"
    assert request.preferred_model == "qwen2.5-coder:1.5b"
    assert request.max_steps == 3


def test_agent_definition_keeps_read_only_and_tools():
    definition = AgentDefinition(
        name="guardian_supervisor",
        description="Read-only supervisor",
        system_prompt="Du bist guardian_supervisor",
        allowed_tools=["system_status", "docker_status", "service_status"],
        settings=AgentSettings(
            active=True,
            preferred_model="",
            max_steps=5,
            timeout_seconds=90,
            read_only=True,
            behavior=AgentBehaviorSettings(),
            personality=AgentPersonalitySettings(),
            custom_instruction=None,
        ),
    )

    assert definition.settings.read_only is True
    assert definition.settings.max_steps == 5
    assert definition.allowed_tools == [
        "system_status",
        "docker_status",
        "service_status",
    ]


def test_tool_call_rejects_invalid_name():
    with pytest.raises(ValidationError):
        ToolCall(tool_name="forbidden tool", arguments={}, reason="test")
