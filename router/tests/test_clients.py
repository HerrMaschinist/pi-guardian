import asyncio

import pytest
from fastapi import HTTPException

from app.models.client import Client, ClientCreate, ClientUpdate
from app.router.clients import create_client, update_client


class DummySession:
    def __init__(self, client=None):
        self.client = client
        self.added = None
        self.deleted = None

    def get(self, _model, _client_id):
        return self.client

    def add(self, obj):
        self.added = obj

    def commit(self):
        return None

    def refresh(self, _obj):
        return None

    def delete(self, obj):
        self.deleted = obj

    def rollback(self):
        return None


def test_create_client_requires_non_empty_name():
    session = DummySession()

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(
            create_client(
                ClientCreate(
                    name="   ",
                    description="desc",
                    active=True,
                    allowed_ip="192.168.50.0/24",
                    allowed_routes=["/route"],
                ),
                session,
            )
        )

    assert exc_info.value.status_code == 422


def test_update_client_rejects_blank_name():
    client = Client(
        id=1,
        name="client-a",
        description="desc",
        active=True,
        allowed_ip="192.168.50.0/24",
        allowed_routes="/route",
        api_key="secret",
    )
    session = DummySession(client=client)

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(update_client(1, ClientUpdate(name="   "), session))

    assert exc_info.value.status_code == 422


def test_update_client_applies_trimmed_name_and_routes():
    client = Client(
        id=1,
        name="client-a",
        description="desc",
        active=True,
        allowed_ip="192.168.50.0/24",
        allowed_routes="",
        api_key="secret",
    )
    session = DummySession(client=client)

    result = asyncio.run(
        update_client(
            1,
            ClientUpdate(
                name="  client-b  ",
                description="new desc",
                active=False,
                allowed_ip="10.0.0.0/24",
                allowed_routes=["/route", " /history ", ""],
            ),
            session,
        )
    )

    assert result.name == "client-b"
    assert result.description == "new desc"
    assert result.active is False
    assert result.allowed_ip == "10.0.0.0/24"
    assert result.allowed_routes == ["/route", "/history"]
