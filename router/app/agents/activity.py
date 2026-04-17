from __future__ import annotations

from datetime import datetime

from sqlmodel import Session, select

from app.memory.models import AgentRunRecord
from app.models.agent_models import AgentActivitySummary, AgentDefinition


def _preview(value: str | None, limit: int = 120) -> str | None:
    if value is None:
        return None
    normalized = " ".join(value.split())
    if not normalized:
        return None
    if len(normalized) <= limit:
        return normalized
    return f"{normalized[: limit - 1].rstrip()}…"


def _duration_ms(started_at: datetime | None, finished_at: datetime | None) -> int | None:
    if started_at is None or finished_at is None:
        return None
    return max(0, int((finished_at - started_at).total_seconds() * 1000))


def get_agent_activity_map(session: Session) -> dict[str, AgentActivitySummary]:
    runs = session.exec(
        select(AgentRunRecord).order_by(AgentRunRecord.started_at.desc())
    ).all()

    activity: dict[str, AgentActivitySummary] = {}
    for run in runs:
        if run.agent_name in activity:
            continue
        activity[run.agent_name] = AgentActivitySummary(
            last_run_id=run.run_id,
            last_run_at=run.finished_at or run.started_at,
            last_status="success" if run.success else "failed",
            last_model=run.used_model,
            last_activity=_preview(run.input),
            last_result_preview=_preview(run.final_answer),
            last_duration_ms=_duration_ms(run.started_at, run.finished_at),
        )
    return activity


def attach_agent_activity(
    definitions: list[AgentDefinition],
    session: Session,
) -> list[AgentDefinition]:
    activity_map = get_agent_activity_map(session)
    return [
        definition.model_copy(update={"activity": activity_map.get(definition.name)})
        for definition in definitions
    ]

