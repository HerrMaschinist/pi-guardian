from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlmodel import Session, select

from app.database import get_session
from app.memory.models import FeedbackEntryRecord, KnowledgeEntryRecord
from app.memory.schemas import (
    MemoryFeedbackCreate,
    MemoryFeedbackEntryRead,
    MemoryIncidentCreate,
    MemoryIncidentFindingCreate,
    MemoryIncidentRead,
    MemoryKnowledgeCreate,
    MemoryKnowledgeEntryRead,
    MemoryRunDetail,
    MemoryRunSummary,
)
from app.memory.service import (
    add_incident_finding,
    create_feedback_entry,
    create_incident,
    create_knowledge_entry,
    get_feedback_entries,
    get_incident,
    get_incidents,
    get_knowledge_entries,
    get_run,
    get_runs,
)
from app.router.auth import authorize_protected_request

router = APIRouter(prefix="/memory", tags=["memory"])


def require_memory_access(
    request: Request,
    session: Session = Depends(get_session),
) -> None:
    authorize_protected_request(request, session, "/memory")


def _incident_from_id(session: Session, incident_id: int) -> MemoryIncidentRead | None:
    return get_incident(session, incident_id)


def _knowledge_from_id(session: Session, entry_id: int) -> MemoryKnowledgeEntryRead | None:
    record = session.exec(
        select(KnowledgeEntryRecord).where(KnowledgeEntryRecord.id == entry_id)
    ).first()
    if record is None:
        return None
    return MemoryKnowledgeEntryRead(
        id=record.id or 0,
        title=record.title,
        pattern=record.pattern,
        probable_cause=record.probable_cause,
        recommended_checks=record.recommended_checks,
        recommended_actions=record.recommended_actions,
        confidence=record.confidence,
        confirmed=record.confirmed,
        source=record.source,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


def _feedback_from_id(session: Session, entry_id: int) -> MemoryFeedbackEntryRead | None:
    record = session.exec(
        select(FeedbackEntryRecord).where(FeedbackEntryRecord.id == entry_id)
    ).first()
    if record is None:
        return None
    return MemoryFeedbackEntryRead(
        id=record.id or 0,
        related_run_id=record.related_run_id,
        related_incident_id=record.related_incident_id,
        verdict=record.verdict,
        comment=record.comment,
        created_by=record.created_by,
        created_at=record.created_at,
    )


@router.get("", response_model=list[MemoryRunSummary], dependencies=[Depends(require_memory_access)])
@router.get("/runs", response_model=list[MemoryRunSummary], dependencies=[Depends(require_memory_access)])
async def memory_runs(session: Session = Depends(get_session)) -> list[MemoryRunSummary]:
    return get_runs(session)


@router.get(
    "/runs/{run_id}",
    response_model=MemoryRunDetail,
    dependencies=[Depends(require_memory_access)],
)
async def memory_run_detail(run_id: str, session: Session = Depends(get_session)) -> MemoryRunDetail:
    run = get_run(session, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run nicht gefunden")
    return run


@router.get(
    "/incidents",
    response_model=list[MemoryIncidentRead],
    dependencies=[Depends(require_memory_access)],
)
async def memory_incidents(session: Session = Depends(get_session)) -> list[MemoryIncidentRead]:
    return get_incidents(session)


@router.get(
    "/incidents/{incident_id}",
    response_model=MemoryIncidentRead,
    dependencies=[Depends(require_memory_access)],
)
async def memory_incident_detail(incident_id: int, session: Session = Depends(get_session)) -> MemoryIncidentRead:
    incident = _incident_from_id(session, incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident nicht gefunden")
    return incident


@router.get(
    "/knowledge",
    response_model=list[MemoryKnowledgeEntryRead],
    dependencies=[Depends(require_memory_access)],
)
async def memory_knowledge(session: Session = Depends(get_session)) -> list[MemoryKnowledgeEntryRead]:
    return get_knowledge_entries(session)


@router.get(
    "/feedback",
    response_model=list[MemoryFeedbackEntryRead],
    dependencies=[Depends(require_memory_access)],
)
async def memory_feedback(session: Session = Depends(get_session)) -> list[MemoryFeedbackEntryRead]:
    return get_feedback_entries(session)


@router.post(
    "/incidents",
    response_model=MemoryIncidentRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_memory_access)],
)
async def memory_create_incident(
    payload: MemoryIncidentCreate,
    session: Session = Depends(get_session),
) -> MemoryIncidentRead:
    incident_id = create_incident(
        title=payload.title,
        summary=payload.summary,
        severity=payload.severity,
        status=payload.status,
        related_run_id=payload.related_run_id,
    )
    if incident_id is None:
        raise HTTPException(status_code=503, detail="Incident konnte nicht gespeichert werden")
    incident = _incident_from_id(session, incident_id)
    if incident is None:
        raise HTTPException(status_code=503, detail="Incident konnte nicht geladen werden")
    return incident


@router.post(
    "/incidents/{incident_id}/findings",
    response_model=MemoryIncidentRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_memory_access)],
)
async def memory_add_incident_finding(
    incident_id: int,
    payload: MemoryIncidentFindingCreate,
    session: Session = Depends(get_session),
) -> MemoryIncidentRead:
    add_incident_finding(
        incident_id=incident_id,
        source_type=payload.source_type,
        source_ref=payload.source_ref,
        finding_type=payload.finding_type,
        content=payload.content,
        confidence=payload.confidence,
    )
    incident = _incident_from_id(session, incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident nicht gefunden")
    return incident


@router.post(
    "/knowledge",
    response_model=MemoryKnowledgeEntryRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_memory_access)],
)
async def memory_create_knowledge(
    payload: MemoryKnowledgeCreate,
    session: Session = Depends(get_session),
) -> MemoryKnowledgeEntryRead:
    entry_id = create_knowledge_entry(
        title=payload.title,
        pattern=payload.pattern,
        probable_cause=payload.probable_cause,
        recommended_checks=payload.recommended_checks,
        recommended_actions=payload.recommended_actions,
        confidence=payload.confidence,
        confirmed=payload.confirmed,
        source=payload.source,
    )
    if entry_id is None:
        raise HTTPException(status_code=503, detail="Knowledge-Eintrag konnte nicht gespeichert werden")
    entry = _knowledge_from_id(session, entry_id)
    if entry is None:
        raise HTTPException(status_code=503, detail="Knowledge-Eintrag konnte nicht geladen werden")
    return entry


@router.post(
    "/feedback",
    response_model=MemoryFeedbackEntryRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_memory_access)],
)
async def memory_create_feedback(
    payload: MemoryFeedbackCreate,
    session: Session = Depends(get_session),
) -> MemoryFeedbackEntryRead:
    entry_id = create_feedback_entry(
        related_run_id=payload.related_run_id,
        related_incident_id=payload.related_incident_id,
        verdict=payload.verdict,
        comment=payload.comment,
        created_by=payload.created_by,
    )
    if entry_id is None:
        raise HTTPException(status_code=503, detail="Feedback konnte nicht gespeichert werden")
    entry = _feedback_from_id(session, entry_id)
    if entry is None:
        raise HTTPException(status_code=503, detail="Feedback konnte nicht geladen werden")
    return entry
