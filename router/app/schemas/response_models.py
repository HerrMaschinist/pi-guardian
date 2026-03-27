from typing import Literal

from pydantic import BaseModel


class RouteResponse(BaseModel):
    model: str
    response: str
    done: bool
    done_reason: str | None = None


class ServiceStatus(BaseModel):
    service: str
    active: bool
    uptime: str | None = None
    pid: int | None = None
    memory_usage: str | None = None
    cpu_percent: float | None = None


class LogEntry(BaseModel):
    timestamp: str
    level: Literal["info", "warn", "error"]
    source: str
    message: str


class OllamaModel(BaseModel):
    name: str
    size: str
    modified_at: str
    digest: str


class RouterSettings(BaseModel):
    router_host: str
    router_port: int
    ollama_host: str
    ollama_port: int
    timeout: int
    default_model: str
    logging_level: str
    stream_default: bool
