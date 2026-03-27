from urllib.parse import urlparse

from app.config import settings


def get_settings() -> dict:
    parsed = urlparse(settings.OLLAMA_BASE_URL)
    return {
        "router_host": settings.ROUTER_HOST,
        "router_port": settings.ROUTER_PORT,
        "ollama_host": parsed.hostname or "127.0.0.1",
        "ollama_port": parsed.port or 11434,
        "timeout": 120,
        "default_model": "qwen2.5-coder:1.5b",
        "logging_level": settings.LOG_LEVEL,
        "stream_default": False,
    }
