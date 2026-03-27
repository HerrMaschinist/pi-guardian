import logging
import os
from contextlib import asynccontextmanager
from logging.handlers import RotatingFileHandler

from app.config import settings

os.makedirs("logs", exist_ok=True)

formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s \u2013 %(message)s")

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
    logging.getLogger(name).propagate = True

from fastapi import FastAPI, Query

from app.database import init_db
from app.router.clients import router as clients_router
from app.router.log_reader import read_logs
from app.router.ollama_models import fetch_models
from app.router.service import route_prompt
from app.router.settings_reader import get_settings
from app.router.system_status import get_service_status
from app.schemas.request_models import RouteRequest
from app.schemas.response_models import (
    LogEntry,
    OllamaModel,
    RouteResponse,
    RouterSettings,
    ServiceStatus,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="PI Guardian Model Router",
    version="0.1.0",
    description="Lokaler FastAPI-Router für Ollama-Modelle auf dem Raspberry Pi",
    lifespan=lifespan,
)

app.include_router(clients_router)


@app.get("/health")
async def healthcheck() -> dict:
    return {"status": "ok"}


@app.get("/status/service", response_model=ServiceStatus)
async def service_status() -> ServiceStatus:
    return ServiceStatus(**get_service_status())


@app.get("/logs", response_model=list[LogEntry])
async def logs(limit: int = Query(default=50, ge=1, le=200)) -> list[LogEntry]:
    return [LogEntry(**e) for e in read_logs(limit)]


@app.get("/models", response_model=list[OllamaModel])
async def models() -> list[OllamaModel]:
    return [OllamaModel(**m) for m in await fetch_models()]


@app.get("/settings", response_model=RouterSettings)
async def router_settings() -> RouterSettings:
    return RouterSettings(**get_settings())


@app.post("/route", response_model=RouteResponse)
async def route(request: RouteRequest) -> RouteResponse:
    return await route_prompt(request)
