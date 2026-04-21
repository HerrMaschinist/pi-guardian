from __future__ import annotations

from sqlmodel import Session, SQLModel, create_engine, select

from app.models.client import Client
from app.router.admin_client import ensure_admin_client


def test_ensure_admin_client_creates_persistent_admin_client(monkeypatch):
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)

    monkeypatch.setattr("app.router.admin_client.settings.ADMIN_CLIENT_NAME", "Router_Admin_UI_Persistent")
    monkeypatch.setattr("app.router.admin_client.settings.ADMIN_CLIENT_DESCRIPTION", "Dedizierter persistenter Admin-Client fuer die Router-UI")
    monkeypatch.setattr("app.router.admin_client.settings.ADMIN_ALLOWED_IP", "192.168.50.0/24")
    monkeypatch.setattr("app.router.admin_client.settings.ADMIN_ALLOWED_ROUTES", "/settings,/clients,/agents")
    monkeypatch.setattr("app.router.admin_client.settings.ADMIN_CLIENT_API_KEY", "")
    monkeypatch.setattr("app.router.admin_client.generate_api_key", lambda: "generated-admin-key")

    with Session(engine) as session:
        client = ensure_admin_client(session)

    with Session(engine) as session:
        stored = session.exec(select(Client).where(Client.name == "Router_Admin_UI_Persistent")).first()

    assert client.api_key == "generated-admin-key"
    assert stored is not None
    assert stored.allowed_ip == "192.168.50.0/24"
    assert stored.allowed_routes_list() == ["/settings", "/clients", "/agents"]
    assert stored.active is True


def test_ensure_admin_client_uses_configured_admin_api_key(monkeypatch):
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)

    monkeypatch.setattr("app.router.admin_client.settings.ADMIN_CLIENT_NAME", "Router_Admin_UI_Persistent")
    monkeypatch.setattr("app.router.admin_client.settings.ADMIN_CLIENT_DESCRIPTION", "Dedizierter persistenter Admin-Client fuer die Router-UI")
    monkeypatch.setattr("app.router.admin_client.settings.ADMIN_ALLOWED_IP", "192.168.50.0/24")
    monkeypatch.setattr("app.router.admin_client.settings.ADMIN_ALLOWED_ROUTES", "/settings,/clients,/agents")
    monkeypatch.setattr("app.router.admin_client.settings.ADMIN_CLIENT_API_KEY", "Alex-ist-der-Ultra-Admin-2026")
    monkeypatch.setattr("app.router.admin_client.generate_api_key", lambda: "generated-admin-key")

    with Session(engine) as session:
        client = ensure_admin_client(session)

    with Session(engine) as session:
        stored = session.exec(select(Client).where(Client.name == "Router_Admin_UI_Persistent")).first()

    assert client.api_key == "Alex-ist-der-Ultra-Admin-2026"
    assert stored is not None
    assert stored.api_key == "Alex-ist-der-Ultra-Admin-2026"
