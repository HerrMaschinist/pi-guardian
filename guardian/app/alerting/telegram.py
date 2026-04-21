from __future__ import annotations

import contextlib
import os
from dataclasses import dataclass
from typing import Any

import httpx

from guardian.app.alerting.models import GuardianAlertSendResult


@dataclass(frozen=True, slots=True)
class GuardianTelegramConfig:
    bot_token: str | None
    chat_id: str | None
    api_base_url: str = "https://api.telegram.org"
    timeout_seconds: float = 10.0

    @classmethod
    def from_env(cls) -> "GuardianTelegramConfig":
        bot_token = os.getenv("GUARDIAN_TELEGRAM_BOT_TOKEN", "").strip() or None
        chat_id = os.getenv("GUARDIAN_TELEGRAM_CHAT_ID", "").strip() or None
        api_base_url = os.getenv("GUARDIAN_TELEGRAM_API_BASE_URL", "https://api.telegram.org").strip()
        timeout_raw = os.getenv("GUARDIAN_TELEGRAM_TIMEOUT_SECONDS", "10.0").strip()
        try:
            timeout_seconds = float(timeout_raw)
        except ValueError:
            timeout_seconds = 10.0
        return cls(
            bot_token=bot_token,
            chat_id=chat_id,
            api_base_url=api_base_url.rstrip("/"),
            timeout_seconds=max(timeout_seconds, 1.0),
        )


class GuardianTelegramClient:
    """Minimal read-write Telegram sender for Guardian alerts."""

    def __init__(
        self,
        config: GuardianTelegramConfig,
        *,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._config = config
        self._client = client or httpx.AsyncClient(
            base_url=config.api_base_url,
            timeout=httpx.Timeout(config.timeout_seconds),
            follow_redirects=False,
        )
        self._owns_client = client is None

    @property
    def config(self) -> GuardianTelegramConfig:
        return self._config

    def is_ready(self) -> tuple[bool, str]:
        if not self._config.bot_token and not self._config.chat_id:
            return False, "telegram bot token and chat id are not configured"
        if not self._config.bot_token:
            return False, "telegram bot token is not configured"
        if not self._config.chat_id:
            return False, "telegram chat id is not configured"
        if not self._config.api_base_url:
            return False, "telegram api base url is not configured"
        return True, "telegram is configured"

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def send_message(self, text: str) -> GuardianAlertSendResult:
        ready, reason = self.is_ready()
        if not ready:
            return GuardianAlertSendResult(ok=False, error=reason)

        assert self._config.bot_token is not None
        assert self._config.chat_id is not None

        path = f"/bot{self._config.bot_token}/sendMessage"
        payload: dict[str, Any] = {
            "chat_id": self._config.chat_id,
            "text": text,
            "disable_web_page_preview": True,
        }

        try:
            response = await self._client.post(path, json=payload)
        except httpx.TimeoutException as exc:
            return GuardianAlertSendResult(ok=False, chat_id=self._config.chat_id, error=f"telegram timeout: {exc}")
        except httpx.RequestError as exc:
            return GuardianAlertSendResult(ok=False, chat_id=self._config.chat_id, error=f"telegram request error: {exc}")

        if response.status_code >= 400:
            return GuardianAlertSendResult(
                ok=False,
                chat_id=self._config.chat_id,
                status_code=response.status_code,
                error=f"telegram http {response.status_code}",
            )

        try:
            payload_json = response.json()
        except ValueError:
            return GuardianAlertSendResult(
                ok=False,
                chat_id=self._config.chat_id,
                status_code=response.status_code,
                error="telegram returned invalid json",
            )

        if not isinstance(payload_json, dict):
            return GuardianAlertSendResult(
                ok=False,
                chat_id=self._config.chat_id,
                status_code=response.status_code,
                error="telegram returned unexpected payload shape",
            )

        if not payload_json.get("ok"):
            description = str(payload_json.get("description") or "telegram api reported failure")
            return GuardianAlertSendResult(
                ok=False,
                chat_id=self._config.chat_id,
                status_code=response.status_code,
                error=description,
            )

        result = payload_json.get("result")
        message_id = None
        if isinstance(result, dict):
            with contextlib.suppress(Exception):
                message_id = int(result.get("message_id"))

        return GuardianAlertSendResult(
            ok=True,
            chat_id=self._config.chat_id,
            message_id=message_id,
            status_code=response.status_code,
        )
