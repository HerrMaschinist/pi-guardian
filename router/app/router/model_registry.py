from __future__ import annotations

import logging
from datetime import datetime

from fastapi import HTTPException
from sqlmodel import Session, select

from app.config import settings
from app.models.model_registry import ModelCreate, ModelRecord, ModelRead, ModelUpdate

logger = logging.getLogger(__name__)

DEFAULT_MODEL_ROLE = "default"
LARGE_MODEL_ROLE = "large"
REGISTERED_MODEL_ROLE = "registered"
READ_ONLY_ROLES = {DEFAULT_MODEL_ROLE, LARGE_MODEL_ROLE}


def _normalize_name(value: str) -> str:
    name = value.strip()
    if not name:
        raise HTTPException(status_code=422, detail="Modelname darf nicht leer sein")
    if any(ch in name for ch in ("\r", "\n", "\x00")):
        raise HTTPException(status_code=422, detail="Modelname muss einzeilig sein")
    return name


def _normalize_description(value: str) -> str:
    description = value.strip()
    if any(ch in description for ch in ("\r", "\x00")):
        raise HTTPException(status_code=422, detail="Beschreibung muss gültigen Text enthalten")
    return description


def _normalize_role(value: str | None) -> str:
    role = (value or REGISTERED_MODEL_ROLE).strip().lower()
    if role not in {DEFAULT_MODEL_ROLE, LARGE_MODEL_ROLE, REGISTERED_MODEL_ROLE}:
        raise HTTPException(status_code=422, detail=f"Unbekannte Modellrolle: {value}")
    return role


def _to_read(record: ModelRecord) -> ModelRead:
    return ModelRead(
        id=record.id or 0,
        name=record.name,
        description=record.description,
        role=record.role,
        enabled=record.enabled,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


def _ensure_model_record(
    session: Session,
    *,
    name: str,
    description: str,
) -> ModelRecord:
    record = session.exec(select(ModelRecord).where(ModelRecord.name == name)).first()
    if record is not None:
        return record

    record = ModelRecord(
        name=name,
        description=description,
        role=REGISTERED_MODEL_ROLE,  # type: ignore[arg-type]
        enabled=True,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    session.add(record)
    session.flush()
    return record


def sync_model_registry(session: Session) -> None:
    """Sorgt dafür, dass die gerouteten Kernmodelle persistent sichtbar bleiben."""
    default_name = _normalize_name(settings.DEFAULT_MODEL)
    large_name = _normalize_name(settings.LARGE_MODEL)
    if default_name == large_name:
        raise HTTPException(
            status_code=422,
            detail="default_model und large_model müssen verschieden sein.",
        )

    descriptions = {
        default_name: "Aktives Fast Model des Routers",
        large_name: "Aktives Deep Model für Fairness- und Eskalationsprüfungen",
    }
    desired_roles = {
        default_name: DEFAULT_MODEL_ROLE,
        large_name: LARGE_MODEL_ROLE,
    }

    _ensure_model_record(
        session,
        name=default_name,
        description=descriptions[default_name],
    )
    _ensure_model_record(
        session,
        name=large_name,
        description=descriptions[large_name],
    )

    records = session.exec(select(ModelRecord)).all()
    now = datetime.now()
    for record in records:
        next_role = desired_roles.get(record.name, REGISTERED_MODEL_ROLE)
        if record.role != next_role:
            record.role = next_role  # type: ignore[assignment]
        if next_role in READ_ONLY_ROLES:
            record.enabled = True
            record.description = descriptions[record.name]
        record.updated_at = now
        session.add(record)

    session.commit()


def list_model_registry(session: Session) -> list[ModelRead]:
    records = session.exec(
        select(ModelRecord).order_by(ModelRecord.role, ModelRecord.name)
    ).all()
    return [_to_read(record) for record in records]


def create_registered_model(session: Session, payload: ModelCreate) -> ModelRead:
    name = _normalize_name(payload.name)
    description = _normalize_description(payload.description)
    existing = session.exec(select(ModelRecord).where(ModelRecord.name == name)).first()
    if existing is not None:
        raise HTTPException(status_code=409, detail="Modell bereits registriert")

    record = ModelRecord(
        name=name,
        description=description,
        role=REGISTERED_MODEL_ROLE,  # type: ignore[arg-type]
        enabled=payload.enabled,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    session.add(record)
    session.commit()
    session.refresh(record)
    return _to_read(record)


def update_registered_model(
    session: Session,
    model_id: int,
    payload: ModelUpdate,
) -> ModelRead:
    record = session.get(ModelRecord, model_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Modell nicht gefunden")
    if record.role in READ_ONLY_ROLES:
        if payload.name is not None and _normalize_name(payload.name) != record.name:
            raise HTTPException(
                status_code=422,
                detail="Kernmodelle werden über /settings verwaltet, nicht über die Registry",
            )
        if payload.enabled is not None and payload.enabled != record.enabled:
            raise HTTPException(
                status_code=422,
                detail="Kernmodelle werden über /settings verwaltet, nicht über die Registry",
            )

    if payload.name is not None:
        next_name = _normalize_name(payload.name)
        existing = session.exec(select(ModelRecord).where(ModelRecord.name == next_name)).first()
        if existing is not None and existing.id != record.id:
            raise HTTPException(status_code=409, detail="Modellname bereits vergeben")
        record.name = next_name
    if payload.description is not None:
        record.description = _normalize_description(payload.description)
    if payload.enabled is not None and record.role == REGISTERED_MODEL_ROLE:
        record.enabled = payload.enabled
    record.updated_at = datetime.now()
    session.add(record)
    session.commit()
    session.refresh(record)
    return _to_read(record)


def delete_registered_model(session: Session, model_id: int) -> None:
    record = session.get(ModelRecord, model_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Modell nicht gefunden")
    if record.role in READ_ONLY_ROLES:
        raise HTTPException(
            status_code=422,
            detail="Kernmodelle werden über /settings verwaltet, nicht über die Registry",
        )
    session.delete(record)
    session.commit()
