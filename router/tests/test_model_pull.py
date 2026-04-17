from datetime import datetime

import pytest
from fastapi import HTTPException
from sqlmodel import Session, SQLModel, create_engine, select

from app.models.model_pull import ModelPullCreate, ModelPullJob
from app.router.model_pull import create_model_pull_job, reset_stale_pull_jobs


class _FakeTask:
    def add_done_callback(self, callback):
        self.callback = callback


def _fake_create_task(coro):
    coro.close()
    return _FakeTask()


def _session():
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)
    return Session(engine)


def test_create_model_pull_job_creates_queued_job(monkeypatch):
    monkeypatch.setattr("app.router.model_pull.asyncio.create_task", _fake_create_task)

    with _session() as session:
        job = create_model_pull_job(session, ModelPullCreate(model_name="qwen2.5-coder:14b"))

        stored = session.exec(select(ModelPullJob)).first()

    assert job.model_name == "qwen2.5-coder:14b"
    assert job.status == "queued"
    assert stored is not None
    assert stored.progress_message == "Wartet auf Start"


def test_create_model_pull_job_rejects_invalid_name(monkeypatch):
    monkeypatch.setattr("app.router.model_pull.asyncio.create_task", _fake_create_task)

    with _session() as session:
        with pytest.raises(HTTPException):
            create_model_pull_job(session, ModelPullCreate(model_name="bad name with spaces"))


def test_reset_stale_pull_jobs_marks_running_as_failed(monkeypatch):
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)
    monkeypatch.setattr("app.database.engine", engine)

    with Session(engine) as session:
        session.add(
            ModelPullJob(
                model_name="qwen2.5-coder:14b",
                status="running",
                progress_message="läuft",
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
        )
        session.commit()

    reset_stale_pull_jobs()

    with Session(engine) as session:
        job = session.exec(select(ModelPullJob)).first()

    assert job is not None
    assert job.status == "failed"
    assert "Router neu gestartet" in job.error_message
