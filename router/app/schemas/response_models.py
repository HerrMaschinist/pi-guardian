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
