from __future__ import annotations

import asyncio
import json
import logging
import re
from datetime import datetime

import httpx
from fastapi import HTTPException
from sqlmodel import Session, select

from app.config import settings
from app.models.model_pull import ModelPullCreate, ModelPullJob, ModelPullRead
from app.models.model_registry import ModelRecord
from app.router.model_registry import sync_model_registry

logger = logging.getLogger(__name__)

ACTIVE_PULL_TASKS: set[asyncio.Task[None]] = set()
MODEL_NAME_PATTERN = re.compile(r"^[A-Za-z0-9._:/-]+$")


def _normalize_model_name(value: str) -> str:
    model_name = value.strip()
    if not model_name:
        raise HTTPException(status_code=422, detail="Modelname darf nicht leer sein")
    if any(ch in model_name for ch in ("\r", "\n", "\x00")):
        raise HTTPException(status_code=422, detail="Modelname muss einzeilig sein")
    if not MODEL_NAME_PATTERN.fullmatch(model_name):
        raise HTTPException(status_code=422, detail="Modelname enthält ungültige Zeichen")
    return model_name


def _to_read(job: ModelPullJob) -> ModelPullRead:
    return ModelPullRead(
        id=job.id or 0,
        model_name=job.model_name,
        status=job.status,
        progress_message=job.progress_message,
        progress_percent=job.progress_percent,
        requested_by=job.requested_by,
        result_summary=job.result_summary,
        error_message=job.error_message,
        created_at=job.created_at,
        updated_at=job.updated_at,
        started_at=job.started_at,
        finished_at=job.finished_at,
    )


def _update_job(job_id: int, **changes) -> None:
    from app.database import engine

    with Session(engine) as session:
        job = session.get(ModelPullJob, job_id)
        if job is None:
            return
        for key, value in changes.items():
            setattr(job, key, value)
        job.updated_at = datetime.now()
        session.add(job)
        session.commit()


def _mark_job_failed(job_id: int, message: str) -> None:
    _update_job(
        job_id,
        status="failed",
        progress_message=message,
        error_message=message,
        finished_at=datetime.now(),
    )


def _mark_job_succeeded(job_id: int, message: str) -> None:
    _update_job(
        job_id,
        status="succeeded",
        progress_message=message,
        result_summary=message,
        error_message=None,
        progress_percent=100,
        finished_at=datetime.now(),
    )


def _extract_progress(payload: dict) -> tuple[str, int | None]:
    message = (
        payload.get("status")
        or payload.get("message")
        or payload.get("error")
        or "Modell wird geladen"
    )
    percent = None
    completed = payload.get("completed")
    total = payload.get("total")
    if isinstance(completed, (int, float)) and isinstance(total, (int, float)) and total > 0:
        percent = max(0, min(100, int((completed / total) * 100)))
    return str(message), percent


async def _run_model_pull(job_id: int) -> None:
    from app.database import engine

    with Session(engine) as session:
        job = session.get(ModelPullJob, job_id)
        if job is None:
            return
        job.status = "running"
        job.started_at = datetime.now()
        job.progress_message = "Modell-Download gestartet"
        job.updated_at = datetime.now()
        session.add(job)
        session.commit()
        model_name = job.model_name

    url = f"{settings.OLLAMA_BASE_URL}/api/pull"
    payload = {"name": model_name, "stream": True}

    try:
        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream("POST", url, json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line.strip():
                        continue
                    try:
                        parsed = json.loads(line)
                    except json.JSONDecodeError:
                        parsed = {"status": line.strip()}
                    if not isinstance(parsed, dict):
                        continue
                    message, percent = _extract_progress(parsed)
                    _update_job(
                        job_id,
                        progress_message=message,
                        progress_percent=percent,
                    )
                    if parsed.get("error"):
                        raise RuntimeError(str(parsed["error"]))
                _mark_job_succeeded(job_id, f"Modell {model_name} erfolgreich geladen")

        with Session(engine) as session:
            existing = session.exec(
                select(ModelRecord).where(ModelRecord.name == model_name)
            ).first()
            if existing is None:
                session.add(
                    ModelRecord(
                        name=model_name,
                        description="Per Modell-Download hinzugefügt",
                        role="registered",
                        enabled=True,
                        created_at=datetime.now(),
                        updated_at=datetime.now(),
                    )
                )
                session.commit()
            sync_model_registry(session)
    except Exception as exc:
        logger.warning("Model pull failed: model=%s job_id=%s error=%s", model_name, job_id, exc)
        _mark_job_failed(job_id, f"Modell-Download fehlgeschlagen: {exc}")


def _track_task(task: asyncio.Task[None]) -> None:
    ACTIVE_PULL_TASKS.add(task)

    def _cleanup(done: asyncio.Task[None]) -> None:
        ACTIVE_PULL_TASKS.discard(done)
        try:
            done.result()
        except Exception as exc:
            logger.warning("Model pull task error: %s", exc)

    task.add_done_callback(_cleanup)


def create_model_pull_job(
    session: Session,
    payload: ModelPullCreate,
    requested_by: str | None = None,
) -> ModelPullRead:
    model_name = _normalize_model_name(payload.model_name)
    job = ModelPullJob(
        model_name=model_name,
        status="queued",
        progress_message="Wartet auf Start",
        requested_by=requested_by,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    session.add(job)
    session.commit()
    session.refresh(job)

    task = asyncio.create_task(_run_model_pull(job.id or 0))
    _track_task(task)
    return _to_read(job)


def list_model_pull_jobs(session: Session, limit: int = 10) -> list[ModelPullRead]:
    jobs = session.exec(
        select(ModelPullJob).order_by(ModelPullJob.created_at.desc()).limit(limit)
    ).all()
    return [_to_read(job) for job in jobs]


def get_model_pull_job(session: Session, job_id: int) -> ModelPullRead:
    job = session.get(ModelPullJob, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Pull-Job nicht gefunden")
    return _to_read(job)


def reset_stale_pull_jobs() -> None:
    from app.database import engine

    with Session(engine) as session:
        stale_jobs = session.exec(
            select(ModelPullJob).where(ModelPullJob.status.in_(["queued", "running"]))
        ).all()
        if not stale_jobs:
            return
        for job in stale_jobs:
            job.status = "failed"
            job.progress_message = "Router neu gestartet, Pull-Job abgebrochen"
            job.error_message = "Router neu gestartet, Pull-Job abgebrochen"
            job.finished_at = datetime.now()
            job.updated_at = datetime.now()
            session.add(job)
        session.commit()
