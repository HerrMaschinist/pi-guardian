import subprocess
from pathlib import Path
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field

from app.config import settings

ENV_FILE = Path(".env")
SUDO_BIN = "/usr/bin/sudo"
SYSTEMCTL_BIN = "/usr/bin/systemctl"


class RouterSettingsUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    router_host: str | None = None
    router_port: int | None = Field(default=None, ge=1, le=65535)
    ollama_host: str | None = None
    ollama_port: int | None = Field(default=None, ge=1, le=65535)
    timeout: int | None = Field(default=None, ge=1, le=3600)
    default_model: str | None = None
    large_model: str | None = None
    logging_level: str | None = None
    stream_default: bool | None = None
    require_api_key: bool | None = None
    escalation_threshold: str | None = None
    restart_service: bool = False


def _normalize_log_level(value: str) -> str:
    normalized = value.upper()
    allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
    if normalized not in allowed:
        raise ValueError(f"Unsupported logging level: {value}")
    return normalized


def _normalize_escalation_threshold(value: str) -> str:
    normalized = value.strip().lower()
    allowed = {"low", "medium", "high"}
    if normalized not in allowed:
        raise ValueError(f"Unsupported escalation threshold: {value}")
    return normalized


def _require_non_empty(name: str, value: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{name} must not be empty")
    return normalized


def _require_safe_single_line(name: str, value: str) -> str:
    normalized = _require_non_empty(name, value)
    if any(ch in normalized for ch in ("\r", "\n", "\x00")):
        raise ValueError(f"{name} must be a single line value")
    return normalized


def _apply_optional_str(value: str | None, *, name: str) -> str | None:
    if value is None:
        return None
    return _require_safe_single_line(name, value)


def _compose_ollama_base_url(host: str, port: int) -> str:
    return f"http://{host}:{port}"


def _env_lines_from_settings() -> list[str]:
    parsed = urlparse(settings.OLLAMA_BASE_URL)
    ollama_host = parsed.hostname or "127.0.0.1"
    ollama_port = parsed.port or 11434
    return [
        f"OLLAMA_BASE_URL={_compose_ollama_base_url(ollama_host, ollama_port)}",
        f"ROUTER_HOST={settings.ROUTER_HOST}",
        f"ROUTER_PORT={settings.ROUTER_PORT}",
        f"LOG_LEVEL={settings.LOG_LEVEL}",
        f"DEFAULT_MODEL={settings.DEFAULT_MODEL}",
        f"LARGE_MODEL={settings.LARGE_MODEL}",
        f"REQUEST_TIMEOUT={settings.REQUEST_TIMEOUT}",
        f"STREAM_DEFAULT={'true' if settings.STREAM_DEFAULT else 'false'}",
        f"REQUIRE_API_KEY={'true' if settings.REQUIRE_API_KEY else 'false'}",
        f"ESCALATION_THRESHOLD={settings.ESCALATION_THRESHOLD}",
    ]


def persist_runtime_settings() -> None:
    ENV_FILE.write_text("\n".join(_env_lines_from_settings()) + "\n", encoding="utf-8")


def update_runtime_settings(update: RouterSettingsUpdate) -> None:
    changes = update.model_dump(exclude_unset=True)

    if "router_host" in changes:
        router_host = _apply_optional_str(changes["router_host"], name="router_host")
        if router_host is not None:
            settings.ROUTER_HOST = router_host
    if "router_port" in changes:
        router_port = changes["router_port"]
        if router_port is not None:
            settings.ROUTER_PORT = router_port
    if "logging_level" in changes:
        logging_level = changes["logging_level"]
        if logging_level is not None:
            settings.LOG_LEVEL = _normalize_log_level(logging_level)
    if "default_model" in changes:
        default_model = _apply_optional_str(
            changes["default_model"], name="default_model"
        )
        if default_model is not None:
            settings.DEFAULT_MODEL = default_model
    if "large_model" in changes:
        large_model = _apply_optional_str(changes["large_model"], name="large_model")
        if large_model is not None:
            settings.LARGE_MODEL = large_model
    if "timeout" in changes:
        timeout = changes["timeout"]
        if timeout is not None:
            settings.REQUEST_TIMEOUT = timeout
    if "stream_default" in changes:
        stream_default = changes["stream_default"]
        if stream_default is not None:
            settings.STREAM_DEFAULT = stream_default
    if "require_api_key" in changes:
        require_api_key = changes["require_api_key"]
        if require_api_key is not None:
            settings.REQUIRE_API_KEY = require_api_key
    if "escalation_threshold" in changes:
        escalation_threshold = changes["escalation_threshold"]
        if escalation_threshold is not None:
            settings.ESCALATION_THRESHOLD = _normalize_escalation_threshold(
                escalation_threshold
            )

    parsed = urlparse(settings.OLLAMA_BASE_URL)
    ollama_host = changes.get("ollama_host", parsed.hostname or "127.0.0.1")
    ollama_host = _apply_optional_str(ollama_host, name="ollama_host")
    if ollama_host is None:
        ollama_host = parsed.hostname or "127.0.0.1"
    ollama_port = changes.get("ollama_port", parsed.port or 11434)
    if ollama_port is None:
        ollama_port = parsed.port or 11434
    settings.OLLAMA_BASE_URL = _compose_ollama_base_url(ollama_host, ollama_port)

    persist_runtime_settings()


def set_default_model(model: str) -> None:
    settings.DEFAULT_MODEL = _require_safe_single_line("default_model", model)
    persist_runtime_settings()


def set_escalation_threshold(value: str) -> None:
    settings.ESCALATION_THRESHOLD = _normalize_escalation_threshold(value)
    persist_runtime_settings()


def restart_router_service() -> tuple[bool, str]:
    try:
        result = subprocess.run(
            [SUDO_BIN, "-n", SYSTEMCTL_BIN, "restart", "pi-guardian-router"],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except FileNotFoundError:
        return False, "sudo ist auf diesem System nicht verfügbar."
    except subprocess.TimeoutExpired:
        return False, "Dienstneustart hat das Timeout überschritten."
    except Exception as exc:
        return False, f"Dienstneustart fehlgeschlagen: {exc}"

    if result.returncode == 0:
        return True, "Router-Dienst erfolgreich neu gestartet."

    stderr = (result.stderr or "").strip()
    if stderr:
        return (
            False,
            "Dienstneustart nicht möglich. Prüfe sudo-/systemd-Rechte. "
            f"Details: {stderr}",
        )
    return False, "Dienstneustart nicht möglich. Prüfe sudo-/systemd-Rechte."
