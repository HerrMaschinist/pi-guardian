from __future__ import annotations

import asyncio
import json

import httpx

from guardian.app.alerting import GuardianTelegramClient, GuardianTelegramConfig


def test_guardian_telegram_client_sends_message() -> None:
    seen: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["path"] = request.url.path
        seen["body"] = json.loads(request.content.decode("utf-8"))
        return httpx.Response(
            200,
            json={
                "ok": True,
                "result": {
                    "message_id": 123,
                },
            },
        )

    transport = httpx.MockTransport(handler)
    client = httpx.AsyncClient(transport=transport, base_url="https://api.telegram.org")
    telegram = GuardianTelegramClient(
        GuardianTelegramConfig(
            bot_token="TOKEN",
            chat_id="CHAT",
            api_base_url="https://api.telegram.org",
            timeout_seconds=5.0,
        ),
        client=client,
    )

    result = asyncio.run(telegram.send_message("hello world"))
    asyncio.run(telegram.aclose())

    assert result.ok is True
    assert result.message_id == 123
    assert seen["path"] == "/botTOKEN/sendMessage"
    assert seen["body"]["chat_id"] == "CHAT"
    assert seen["body"]["text"] == "hello world"
