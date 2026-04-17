from types import SimpleNamespace
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from app.tools.registry import get_tool


def test_system_status_tool_returns_read_only_snapshot(monkeypatch):
    tool = get_tool("system_status")
    assert tool is not None

    monkeypatch.setattr("app.tools.system_status_tool._read_uptime_seconds", lambda: 123.4)
    monkeypatch.setattr(
        "app.tools.system_status_tool._read_load_average",
        lambda: {"1m": 0.1, "5m": 0.2, "15m": 0.3},
    )
    monkeypatch.setattr(
        "app.tools.system_status_tool._read_meminfo",
        lambda: {"total_mb": 1000.0, "available_mb": 500.0, "used_mb": 500.0, "used_percent": 50.0},
    )
    monkeypatch.setattr("app.tools.system_status_tool._read_temperature_c", lambda: 42.0)
    monkeypatch.setattr(
        "app.tools.system_status_tool.shutil.disk_usage",
        lambda _path: SimpleNamespace(total=10 * 1024**3, used=4 * 1024**3, free=6 * 1024**3),
    )

    result = tool.execute(tool.validate_arguments({}))

    assert result.success is True
    assert result.output["temperature_c"] == 42.0
    assert result.output["disk"]["used_percent"] == 40.0


def test_system_status_tool_rejects_unexpected_arguments():
    tool = get_tool("system_status")
    assert tool is not None

    with pytest.raises(ValidationError):
        tool.validate_arguments({"unexpected": True})


def test_docker_status_tool_parses_container_list(monkeypatch):
    tool = get_tool("docker_status")
    assert tool is not None

    def fake_run(args):
        if args[0] == "inspect":
            return SimpleNamespace(stdout="healthy\n")
        return SimpleNamespace(
            stdout='{"ID":"abc123","Names":"demo","Status":"Up 1 hour","Image":"nginx:latest"}\n'
        )

    monkeypatch.setattr("app.tools.docker_status_tool._run_docker_command", fake_run)

    result = tool.execute(tool.validate_arguments({}))

    assert result.success is True
    assert result.output["container_count"] == 1
    assert result.output["containers"][0]["health"] == "healthy"


def test_docker_status_tool_reports_missing_binary(monkeypatch):
    tool = get_tool("docker_status")
    assert tool is not None

    def fake_run(_args):
        raise FileNotFoundError("docker")

    monkeypatch.setattr("app.tools.docker_status_tool._run_docker_command", fake_run)

    result = tool.execute(tool.validate_arguments({}))

    assert result.success is False
    assert "Docker-Binary nicht gefunden" in result.error


def test_service_status_tool_validates_safe_service_name():
    tool = get_tool("service_status")
    assert tool is not None

    with pytest.raises(ValidationError):
        tool.validate_arguments({"service_name": "ssh"})


def test_service_status_tool_reads_router_state(monkeypatch):
    tool = get_tool("service_status")
    assert tool is not None

    monkeypatch.setattr(
        "app.tools.service_status_tool.get_service_status",
        lambda: {
            "service": "pi-guardian-router",
            "active": True,
            "uptime": "1 day",
            "pid": 123,
            "memory_usage": "10 MB",
            "cpu_percent": 1.5,
        },
    )

    def fake_run(args, **kwargs):
        return SimpleNamespace(
            stdout=(
                "ActiveState=active\n"
                "SubState=running\n"
                "MainPID=123\n"
                "UnitFileState=enabled\n"
                "FragmentPath=/etc/systemd/system/pi-guardian-router.service\n"
                "Description=PI Guardian Router\n"
            )
        )

    monkeypatch.setattr("app.tools.service_status_tool.subprocess.run", fake_run)

    result = tool.execute(tool.validate_arguments({"service_name": "pi-guardian-router"}))

    assert result.success is True
    assert result.output["active_state"] == "active"
    assert result.output["service"] == "pi-guardian-router"

