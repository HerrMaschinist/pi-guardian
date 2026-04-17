from types import SimpleNamespace
from unittest.mock import patch

import pytest

from app.router.settings_manager import restart_router_service
from app.config import settings
from app.router.settings_manager import RouterSettingsUpdate, update_runtime_settings


def test_restart_router_service_includes_permission_hint_and_details():
    result = SimpleNamespace(
        returncode=1,
        stderr="sudo: a password is required",
    )

    with patch("app.router.settings_manager.subprocess.run", return_value=result):
        success, message = restart_router_service()

    assert success is False
    assert "Dienstneustart nicht möglich. Prüfe sudo-/systemd-Rechte." in message
    assert "sudo: a password is required" in message


def test_update_runtime_settings_ignores_null_values(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)

    original = {
        "ROUTER_HOST": settings.ROUTER_HOST,
        "ROUTER_PORT": settings.ROUTER_PORT,
        "OLLAMA_BASE_URL": settings.OLLAMA_BASE_URL,
        "LOG_LEVEL": settings.LOG_LEVEL,
        "DEFAULT_MODEL": settings.DEFAULT_MODEL,
        "REQUEST_TIMEOUT": settings.REQUEST_TIMEOUT,
        "STREAM_DEFAULT": settings.STREAM_DEFAULT,
        "REQUIRE_API_KEY": settings.REQUIRE_API_KEY,
        "ESCALATION_THRESHOLD": settings.ESCALATION_THRESHOLD,
    }
    try:
        update_runtime_settings(
            RouterSettingsUpdate(
                router_host=None,
                router_port=None,
                ollama_host=None,
                ollama_port=None,
                timeout=None,
                default_model=None,
                logging_level=None,
                stream_default=None,
                require_api_key=None,
                escalation_threshold=None,
            )
        )
    finally:
        for key, value in original.items():
            setattr(settings, key, value)

    assert settings.ROUTER_HOST == original["ROUTER_HOST"]
    assert settings.ROUTER_PORT == original["ROUTER_PORT"]
    assert settings.OLLAMA_BASE_URL == original["OLLAMA_BASE_URL"]
    assert settings.LOG_LEVEL == original["LOG_LEVEL"]
    assert settings.DEFAULT_MODEL == original["DEFAULT_MODEL"]
    assert settings.REQUEST_TIMEOUT == original["REQUEST_TIMEOUT"]
    assert settings.STREAM_DEFAULT == original["STREAM_DEFAULT"]
    assert settings.REQUIRE_API_KEY == original["REQUIRE_API_KEY"]
    assert settings.ESCALATION_THRESHOLD == original["ESCALATION_THRESHOLD"]


def test_update_runtime_settings_rejects_control_char_in_host(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)

    with pytest.raises(ValueError):
        update_runtime_settings(
            RouterSettingsUpdate(router_host="127.0.0.1\nmalicious")
        )


def test_update_runtime_settings_rejects_invalid_fairness_threshold(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)

    with pytest.raises(ValueError):
        update_runtime_settings(
            RouterSettingsUpdate(escalation_threshold="urgent")
        )
