from __future__ import annotations

from ipaddress import ip_address, ip_network

from fastapi import APIRouter, Depends, Request, Response, status
from sqlmodel import Session

from app.config import settings
from app.database import get_session
from app.router.admin_client import ensure_admin_client
from app.router.auth import extract_client_ip

router = APIRouter(prefix="/auth", tags=["auth"])


def _ip_allowed(client_ip: str, allowed_ip: str) -> bool:
    try:
        if "/" in allowed_ip:
            return ip_address(client_ip) in ip_network(allowed_ip, strict=False)
        return client_ip == allowed_ip
    except ValueError:
        return False


@router.post("/bootstrap", status_code=status.HTTP_204_NO_CONTENT)
async def bootstrap_admin_session(
    request: Request,
    session: Session = Depends(get_session),
) -> Response:
    client = ensure_admin_client(session)
    client_ip = extract_client_ip(request)
    if client_ip != "unknown" and not _ip_allowed(client_ip, client.allowed_ip):
        return Response(status_code=status.HTTP_403_FORBIDDEN)

    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    response.set_cookie(
        key=settings.ADMIN_SESSION_COOKIE_NAME,
        value=client.api_key,
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=settings.ADMIN_SESSION_COOKIE_MAX_AGE,
        path="/",
    )
    return response
