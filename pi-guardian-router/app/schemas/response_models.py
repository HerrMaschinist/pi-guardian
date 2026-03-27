from pydantic import BaseModel


class RouteResponse(BaseModel):
    model: str
    response: str
    done: bool
    done_reason: str | None = None
