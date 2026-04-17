from app.agents.tool_parser import parse_tool_call


def test_parse_tool_call_accepts_registered_tool():
    result = parse_tool_call(
        '{"tool_name":"system_status","arguments":{},"reason":"System prüfen"}',
        allowed_tools=["system_status", "docker_status"],
    )

    assert result.error is None
    assert result.tool_call is not None
    assert result.tool_call.tool_name == "system_status"
    assert result.tool_call.arguments == {}


def test_parse_tool_call_rejects_tool_not_allowed():
    result = parse_tool_call(
        '{"tool_name":"service_status","arguments":{"service_name":"ollama"},"reason":"Prüfen"}',
        allowed_tools=["system_status"],
    )

    assert result.tool_call is None
    assert result.error is not None
    assert "nicht für diesen Agenten erlaubt" in result.error


def test_parse_tool_call_ignores_plain_text_final_answer():
    result = parse_tool_call(
        "Alles stabil, keine weiteren Schritte nötig.",
        allowed_tools=["system_status"],
    )

    assert result.tool_call is None
    assert result.error is None


def test_parse_tool_call_ignores_json_without_tool_marker():
    result = parse_tool_call(
        '{"summary":"ok","confidence":0.9}',
        allowed_tools=["system_status"],
    )

    assert result.tool_call is None
    assert result.error is None

