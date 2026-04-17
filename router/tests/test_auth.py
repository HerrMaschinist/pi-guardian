from types import SimpleNamespace
from unittest.mock import patch

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from app.router.auth import authorize_protected_request


def make_request(headers: dict[str, str] | None = None, host: str = "192.168.50.10") -> Request:
    encoded_headers = []
    for key, value in (headers or {}).items():
        encoded_headers.append((key.lower().encode("latin-1"), value.encode("latin-1")))
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/settings",
        "headers": encoded_headers,
        "client": (host, 12345),
    }
    return Request(scope)


class DummySession:
    def __init__(self, client):
        self._client = client

    def exec(self, _query):
        return SimpleNamespace(first=lambda: self._client)


def test_protected_request_allows_matching_route():
    client = SimpleNamespace(
        active=True,
        api_key="secret",
        name="admin",
        allowed_ip="192.168.50.0/24",
        allowed_routes_list=lambda: ["/settings", "/clients"],
    )
    request = make_request(headers={"x-api-key": "secret"})

    with patch("app.router.auth.settings.REQUIRE_API_KEY", True):
        result = authorize_protected_request(request, DummySession(client), "/settings")

    assert result == "admin"


def test_protected_request_ignores_spoofed_forwarded_for_from_untrusted_peer():
    client = SimpleNamespace(
        active=True,
        api_key="secret",
        name="admin",
        allowed_ip="192.168.50.0/24",
        allowed_routes_list=lambda: ["/settings", "/clients"],
    )
    request = make_request(
        headers={
            "x-api-key": "secret",
            "x-forwarded-for": "192.168.50.77",
        },
        host="203.0.113.10",
    )

    with patch("app.router.auth.settings.REQUIRE_API_KEY", True):
        with pytest.raises(HTTPException) as exc_info:
            authorize_protected_request(request, DummySession(client), "/settings")

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Client-IP ist nicht erlaubt"


def test_protected_request_rejects_missing_route_permission():
    client = SimpleNamespace(
        active=True,
        api_key="secret",
        name="limited",
        allowed_ip="192.168.50.0/24",
        allowed_routes_list=lambda: ["/route"],
    )
    request = make_request(headers={"x-api-key": "secret"})

    with patch("app.router.auth.settings.REQUIRE_API_KEY", True):
        with pytest.raises(HTTPException) as exc_info:
            authorize_protected_request(request, DummySession(client), "/settings")

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Client darf /settings nicht nutzen"
