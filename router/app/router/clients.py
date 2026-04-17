import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlmodel import Session, select

from app.database import get_session
from app.models.client import Client, ClientCreate, ClientRead, ClientUpdate
from app.router.api_key import generate_api_key
from app.router.auth import authorize_protected_request

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/clients", tags=["clients"])


def _normalize_client_name(value: str) -> str:
    name = value.strip()
    if not name:
        raise HTTPException(status_code=422, detail="Name darf nicht leer sein")
    return name


def require_clients_access(
    request: Request,
    session: Session = Depends(get_session),
) -> None:
    authorize_protected_request(request, session, "/clients")


def _to_read(client: Client, include_key: bool = False) -> ClientRead:
    """Konvertiert DB-Objekt → API-Schema. API-Key nur bei Erstellung sichtbar."""
    return ClientRead(
        id=client.id,
        name=client.name,
        description=client.description,
        active=client.active,
        allowed_ip=client.allowed_ip,
        allowed_routes=client.allowed_routes_list(),
        api_key=client.api_key if include_key else "",
        created_at=client.created_at,
    )


@router.get("", response_model=list[ClientRead], dependencies=[Depends(require_clients_access)])
async def list_clients(session: Session = Depends(get_session)) -> list[ClientRead]:
    try:
        clients = session.exec(
            select(Client).order_by(Client.created_at.desc())
        ).all()
        return [_to_read(c) for c in clients]
    except Exception as exc:
        logger.error("list_clients: %s", exc)
        raise HTTPException(status_code=503, detail="Datenbank nicht erreichbar")


@router.post("", response_model=ClientRead, status_code=201, dependencies=[Depends(require_clients_access)])
async def create_client(
    data: ClientCreate, session: Session = Depends(get_session)
) -> ClientRead:
    try:
        client = Client(
            name=_normalize_client_name(data.name),
            description=data.description,
            active=data.active,
            allowed_ip=data.allowed_ip,
            allowed_routes=",".join(r.strip() for r in data.allowed_routes if r.strip()),
            api_key=generate_api_key(),
        )
        session.add(client)
        session.commit()
        session.refresh(client)
        logger.info("Client erstellt: id=%s name=%s", client.id, client.name)
        return _to_read(client, include_key=True)
    except HTTPException:
        raise
    except Exception as exc:
        session.rollback()
        logger.error("create_client: %s", exc)
        raise HTTPException(status_code=503, detail="Datenbank nicht erreichbar")


@router.get("/{client_id}", response_model=ClientRead, dependencies=[Depends(require_clients_access)])
async def get_client(
    client_id: int, session: Session = Depends(get_session)
) -> ClientRead:
    try:
        client = session.get(Client, client_id)
    except Exception as exc:
        logger.error("get_client: %s", exc)
        raise HTTPException(status_code=503, detail="Datenbank nicht erreichbar")
    if not client:
        raise HTTPException(status_code=404, detail="Client nicht gefunden")
    return _to_read(client)


@router.put("/{client_id}", response_model=ClientRead, dependencies=[Depends(require_clients_access)])
async def update_client(
    client_id: int,
    data: ClientUpdate,
    session: Session = Depends(get_session),
) -> ClientRead:
    try:
        client = session.get(Client, client_id)
    except Exception as exc:
        logger.error("update_client: %s", exc)
        raise HTTPException(status_code=503, detail="Datenbank nicht erreichbar")
    if not client:
        raise HTTPException(status_code=404, detail="Client nicht gefunden")
    try:
        update_fields = data.model_dump(exclude_unset=True)
        if "name" in update_fields:
            update_fields["name"] = _normalize_client_name(update_fields["name"])
        if "allowed_routes" in update_fields:
            update_fields["allowed_routes"] = ",".join(
                r.strip() for r in update_fields["allowed_routes"] if r.strip()
            )
        for field, value in update_fields.items():
            setattr(client, field, value)
        session.add(client)
        session.commit()
        session.refresh(client)
        return _to_read(client)
    except HTTPException:
        raise
    except Exception as exc:
        session.rollback()
        logger.error("update_client commit: %s", exc)
        raise HTTPException(status_code=503, detail="Datenbank nicht erreichbar")


@router.delete("/{client_id}", status_code=204, dependencies=[Depends(require_clients_access)])
async def delete_client(
    client_id: int, session: Session = Depends(get_session)
) -> None:
    try:
        client = session.get(Client, client_id)
    except Exception as exc:
        logger.error("delete_client: %s", exc)
        raise HTTPException(status_code=503, detail="Datenbank nicht erreichbar")
    if not client:
        raise HTTPException(status_code=404, detail="Client nicht gefunden")
    try:
        session.delete(client)
        session.commit()
        logger.info("Client gelöscht: id=%s", client_id)
    except Exception as exc:
        session.rollback()
        logger.error("delete_client commit: %s", exc)
        raise HTTPException(status_code=503, detail="Datenbank nicht erreichbar")
