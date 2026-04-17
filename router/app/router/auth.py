from ipaddress import ip_address, ip_network

from fastapi import HTTPException, Request
from sqlmodel import Session, select

from app.config import settings
from app.models.client import Client


def _extract_client_ip(request: Request) -> str:
    peer_host = request.client.host if request.client and request.client.host else ""
    if not peer_host:
        return "unknown"

    try:
        peer_ip = ip_address(peer_host)
    except ValueError:
        return peer_host

    if peer_ip.is_loopback:
        forwarded = request.headers.get("x-forwarded-for", "").strip()
        if forwarded:
            candidate = forwarded.split(",")[0].strip()
            try:
                ip_address(candidate)
            except ValueError:
                return peer_host
            return candidate

        real_ip = request.headers.get("x-real-ip", "").strip()
        if real_ip:
            try:
                ip_address(real_ip)
            except ValueError:
                return peer_host
            return real_ip

    return peer_host


def extract_client_ip(request: Request) -> str:
    return _extract_client_ip(request)


def _ip_allowed(client: Client, ip: str) -> bool:
    try:
        if "/" in client.allowed_ip:
            return ip_address(ip) in ip_network(client.allowed_ip, strict=False)
        return ip == client.allowed_ip
    except ValueError:
        return False


def _authorize_request(
    request: Request,
    session: Session,
    allowed_route: str,
) -> str | None:
    if not settings.REQUIRE_API_KEY:
        return None

    api_key = request.headers.get("x-api-key", "").strip()
    if not api_key:
        api_key = request.cookies.get(settings.ADMIN_SESSION_COOKIE_NAME, "").strip()
    if not api_key:
        raise HTTPException(status_code=401, detail="X-API-Key fehlt")

    client = session.exec(select(Client).where(Client.api_key == api_key)).first()
    if not client or not client.active:
        raise HTTPException(status_code=403, detail="API-Key ungültig oder Client inaktiv")

    if allowed_route not in client.allowed_routes_list():
        raise HTTPException(
            status_code=403,
            detail=f"Client darf {allowed_route} nicht nutzen",
        )

    client_ip = _extract_client_ip(request)
    if client_ip != "unknown" and not _ip_allowed(client, client_ip):
        raise HTTPException(status_code=403, detail="Client-IP ist nicht erlaubt")

    return client.name


def authorize_route_request(request: Request, session: Session) -> str | None:
    return _authorize_request(request, session, "/route")


def authorize_protected_request(
    request: Request,
    session: Session,
    allowed_route: str,
) -> str | None:
    return _authorize_request(request, session, allowed_route)
