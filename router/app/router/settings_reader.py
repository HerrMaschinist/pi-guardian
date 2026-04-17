from urllib.parse import urlparse

from app.config import settings


def get_settings() -> dict:
    parsed = urlparse(settings.OLLAMA_BASE_URL)
    return {
        "router_host": settings.ROUTER_HOST,
        "router_port": settings.ROUTER_PORT,
        "ollama_host": parsed.hostname or "127.0.0.1",
        "ollama_port": parsed.port or 11434,
        "timeout": settings.REQUEST_TIMEOUT,
        "default_model": settings.DEFAULT_MODEL,
        "large_model": settings.LARGE_MODEL,
        "logging_level": settings.LOG_LEVEL,
        "stream_default": settings.STREAM_DEFAULT,
        "require_api_key": settings.REQUIRE_API_KEY,
        "escalation_threshold": settings.ESCALATION_THRESHOLD,
    }
