from __future__ import annotations

import asyncio
from types import SimpleNamespace

from fastapi import Response

from app.api.routes_auth import bootstrap_admin_session


def test_bootstrap_admin_session_sets_cookie(monkeypatch):
    monkeypatch.setattr(
        "app.api.routes_auth.ensure_admin_client",
        lambda session: SimpleNamespace(api_key="secret", allowed_ip="192.168.50.0/24"),
    )
    monkeypatch.setattr("app.api.routes_auth.extract_client_ip", lambda request: "192.168.50.10")

    request = SimpleNamespace(
        client=SimpleNamespace(host="192.168.50.10"),
        headers={},
    )
    response = asyncio.run(
        bootstrap_admin_session(
            request=request,  # type: ignore[arg-type]
            session=object(),  # type: ignore[arg-type]
        )
    )

    assert isinstance(response, Response)
    assert response.status_code == 204
    assert "pi_guardian_admin_api_key" in response.headers.get("set-cookie", "")


def test_bootstrap_admin_session_rejects_wrong_ip(monkeypatch):
    monkeypatch.setattr(
        "app.api.routes_auth.ensure_admin_client",
        lambda session: SimpleNamespace(api_key="secret", allowed_ip="192.168.50.0/24"),
    )
    monkeypatch.setattr("app.api.routes_auth.extract_client_ip", lambda request: "203.0.113.10")

    request = SimpleNamespace(
        client=SimpleNamespace(host="203.0.113.10"),
        headers={},
    )
    response = asyncio.run(
        bootstrap_admin_session(
            request=request,  # type: ignore[arg-type]
            session=object(),  # type: ignore[arg-type]
        )
    )

    assert response.status_code == 403
