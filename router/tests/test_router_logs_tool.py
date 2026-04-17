from app.tools.router_logs_tool import RouterLogsTool, RouterLogsInput


def test_router_logs_tool_filters_by_level_and_text(monkeypatch):
    tool = RouterLogsTool()

    monkeypatch.setattr(
        "app.tools.router_logs_tool.read_logs",
        lambda limit: [
            {
                "timestamp": "2026-04-17T10:00:00",
                "level": "info",
                "source": "app.main",
                "message": "startup complete",
            },
            {
                "timestamp": "2026-04-17T10:01:00",
                "level": "error",
                "source": "app.agents.runtime",
                "message": "tool_call_failed",
            },
            {
                "timestamp": "2026-04-17T10:02:00",
                "level": "error",
                "source": "app.api.routes_agents",
                "message": "agent_run failed",
            },
        ],
    )

    result = tool.execute(
        RouterLogsInput.model_validate(
            {
                "limit": 2,
                "level": "error",
                "source_contains": "routes",
            }
        )
    )

    assert result.success is True
    assert result.tool_name == "router_logs"
    assert result.output["source"] == "router.log"
    assert result.output["returned_count"] == 1
    assert len(result.output["entries"]) == 1
    assert result.output["entries"][0]["source"] == "app.api.routes_agents"


def test_router_logs_tool_rejects_invalid_limit():
    tool = RouterLogsTool()

    try:
        RouterLogsInput.model_validate({"limit": 0})
    except Exception as exc:
        assert "greater than or equal to 1" in str(exc)
    else:
        raise AssertionError("invalid limit should fail")
