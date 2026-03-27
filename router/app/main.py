import logging
import os
from logging.handlers import RotatingFileHandler

from app.config import settings

os.makedirs("logs", exist_ok=True)

formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s – %(message)s")

file_handler = RotatingFileHandler(
    "logs/router.log", maxBytes=5 * 1024 * 1024, backupCount=3
)
file_handler.setFormatter(formatter)

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)

level = logging.getLevelName(settings.LOG_LEVEL)

root_logger = logging.getLogger()
root_logger.setLevel(level)
root_logger.addHandler(file_handler)
root_logger.addHandler(stream_handler)

for name in ("uvicorn", "uvicorn.access", "uvicorn.error"):
    log = logging.getLogger(name)
    log.propagate = True

from fastapi import FastAPI

from app.router.service import route_prompt
from app.router.system_status import get_service_status
from app.schemas.request_models import RouteRequest
from app.schemas.response_models import RouteResponse, ServiceStatus


app = FastAPI(
    title="PI Guardian Model Router",
    version="0.1.0",
    description="Lokaler FastAPI-Router für Ollama-Modelle auf dem Raspberry Pi",
)


@app.get("/health")
async def healthcheck() -> dict:
    return {"status": "ok"}


@app.get("/status/service", response_model=ServiceStatus)
async def service_status() -> ServiceStatus:
    return ServiceStatus(**get_service_status())


@app.post("/route", response_model=RouteResponse)
async def route(request: RouteRequest) -> RouteResponse:
    return await route_prompt(request)
