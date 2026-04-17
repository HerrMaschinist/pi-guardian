from __future__ import annotations

import logging

from sqlmodel import Session
from sqlmodel import select

from app.config import settings
from app.models.client import Client
from app.router.api_key import generate_api_key

logger = logging.getLogger(__name__)


def _allowed_routes() -> str:
    routes = [route.strip() for route in settings.ADMIN_ALLOWED_ROUTES.split(",") if route.strip()]
    return ",".join(routes)


def ensure_admin_client(session: Session) -> Client:
    client = session.exec(
        select(Client).where(Client.name == settings.ADMIN_CLIENT_NAME)
    ).first()
    if client is None:
        client = Client(
            name=settings.ADMIN_CLIENT_NAME,
            description=settings.ADMIN_CLIENT_DESCRIPTION,
            active=True,
            allowed_ip=settings.ADMIN_ALLOWED_IP,
            allowed_routes=_allowed_routes(),
            api_key=generate_api_key(),
        )
        session.add(client)
        session.commit()
        session.refresh(client)
        logger.info("Admin-Client angelegt: %s", client.name)
        return client

    changed = False
    if client.description != settings.ADMIN_CLIENT_DESCRIPTION:
        client.description = settings.ADMIN_CLIENT_DESCRIPTION
        changed = True
    if client.allowed_ip != settings.ADMIN_ALLOWED_IP:
        client.allowed_ip = settings.ADMIN_ALLOWED_IP
        changed = True
    desired_routes = _allowed_routes()
    if client.allowed_routes != desired_routes:
        client.allowed_routes = desired_routes
        changed = True
    if not client.active:
        client.active = True
        changed = True
    if changed:
        session.add(client)
        session.commit()
        session.refresh(client)
        logger.info("Admin-Client aktualisiert: %s", client.name)

    return client
