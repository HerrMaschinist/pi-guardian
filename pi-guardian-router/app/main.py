from fastapi import FastAPI

from app.router.service import route_prompt
from app.schemas.request_models import RouteRequest
from app.schemas.response_models import RouteResponse


app = FastAPI(
    title="PI Guardian Model Router",
    version="0.1.0",
    description="Lokaler FastAPI-Router für Ollama-Modelle auf dem Raspberry Pi",
)


@app.get("/health")
async def healthcheck() -> dict:
    return {"status": "ok"}


@app.post("/route", response_model=RouteResponse)
async def route(request: RouteRequest) -> RouteResponse:
    return await route_prompt(request)
