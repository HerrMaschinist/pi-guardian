from __future__ import annotations

import os
from contextlib import suppress
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

import httpx
from pydantic import BaseModel, Field

from guardian.app.core.domain import (
    GuardianAction,
    GuardianSeverity,
    GuardianSignalSource,
)


class RouterReadError(RuntimeError):
    """Raised when the Guardian cannot read a router endpoint reliably."""


class RouterEndpointErrorKind(StrEnum):
    TIMEOUT = "timeout"
    CONNECTION_ERROR = "connection_error"
    HTTP_ERROR = "http_error"
    AUTH_REQUIRED = "auth_required"
    INVALID_JSON = "invalid_json"
    INVALID_SHAPE = "invalid_shape"
    INVALID_PAYLOAD = "invalid_payload"


class RouterHealthPayload(BaseModel):
    status: str | None = None
    service: str | None = None
    version: str | None = None
    router_busy: bool | None = None
    ollama_reachable: bool | None = None
    configured_models: dict[str, Any] | None = None


class RouterServiceStatusPayload(BaseModel):
    service: str | None = None
    active: bool | None = None
    uptime: str | None = None
    pid: int | None = None
    memory_usage: str | None = None
    cpu_percent: float | None = None


class RouterEndpointReadResult(BaseModel):
    endpoint: str
    ok: bool
    status_code: int | None = None
    error_kind: RouterEndpointErrorKind | None = None
    error_message: str | None = None
    payload: dict[str, Any] | None = None

    @property
    def auth_required(self) -> bool:
        return self.error_kind == RouterEndpointErrorKind.AUTH_REQUIRED

    @property
    def unavailable(self) -> bool:
        return not self.ok and self.error_kind in {
            RouterEndpointErrorKind.TIMEOUT,
            RouterEndpointErrorKind.CONNECTION_ERROR,
            RouterEndpointErrorKind.HTTP_ERROR,
        }


class GuardianFindingModel(BaseModel):
    code: str
    summary: str
    severity: GuardianSeverity
    source: GuardianSignalSource
    detail: str | None = None
    evidence: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class GuardianRouterProbe(BaseModel):
    checked_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    status: GuardianSeverity = GuardianSeverity.OK
    action: GuardianAction = GuardianAction.NONE
    reachable: bool = False
    service_active: bool | None = None
    health_result: RouterEndpointReadResult | None = None
    service_status_result: RouterEndpointReadResult | None = None
    health: RouterHealthPayload | None = None
    service_status: RouterServiceStatusPayload | None = None
    findings: list[GuardianFindingModel] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    router_base_url: str
    health_path: str = "/health"
    status_path: str = "/status/service"


@dataclass(frozen=True, slots=True)
class RouterReadConfig:
    base_url: str
    timeout_seconds: float = 2.5
    health_path: str = "/health"
    status_path: str = "/status/service"
    api_key: str | None = None

    @classmethod
    def from_env(cls) -> "RouterReadConfig":
        base_url = os.getenv("GUARDIAN_ROUTER_BASE_URL", "http://127.0.0.1:8071").strip()
        timeout_raw = os.getenv("GUARDIAN_ROUTER_TIMEOUT_SECONDS", "2.5").strip()
        health_path = os.getenv("GUARDIAN_ROUTER_HEALTH_PATH", "/health").strip() or "/health"
        status_path = os.getenv("GUARDIAN_ROUTER_STATUS_PATH", "/status/service").strip() or "/status/service"
        api_key = os.getenv("GUARDIAN_ROUTER_API_KEY", "").strip() or None
        try:
            timeout_seconds = float(timeout_raw)
        except ValueError:
            timeout_seconds = 2.5
        if not base_url:
            base_url = "http://127.0.0.1:8071"
        return cls(
            base_url=base_url.rstrip("/"),
            timeout_seconds=max(timeout_seconds, 0.5),
            health_path=health_path if health_path.startswith("/") else f"/{health_path}",
            status_path=status_path if status_path.startswith("/") else f"/{status_path}",
            api_key=api_key,
        )


class RouterReadClient:
    """Read-only HTTP client for the existing router."""

    def __init__(self, config: RouterReadConfig) -> None:
        self._config = config
        headers: dict[str, str] = {}
        if config.api_key:
            headers["X-API-Key"] = config.api_key
        self._client = httpx.AsyncClient(
            base_url=config.base_url,
            timeout=httpx.Timeout(config.timeout_seconds),
            follow_redirects=False,
            headers=headers,
        )

    @property
    def base_url(self) -> str:
        return self._config.base_url

    async def aclose(self) -> None:
        await self._client.aclose()

    async def _get_json(self, path: str) -> RouterEndpointReadResult:
        try:
            response = await self._client.get(path)
        except httpx.TimeoutException as exc:
            return RouterEndpointReadResult(
                endpoint=path,
                ok=False,
                error_kind=RouterEndpointErrorKind.TIMEOUT,
                error_message=f"timeout while requesting {path}: {exc}",
            )
        except httpx.RequestError as exc:
            return RouterEndpointReadResult(
                endpoint=path,
                ok=False,
                error_kind=RouterEndpointErrorKind.CONNECTION_ERROR,
                error_message=f"connection error while requesting {path}: {exc}",
            )

        if response.status_code >= 400:
            error_kind = RouterEndpointErrorKind.HTTP_ERROR
            if response.status_code in {401, 403}:
                error_kind = RouterEndpointErrorKind.AUTH_REQUIRED
            return RouterEndpointReadResult(
                endpoint=path,
                ok=False,
                status_code=response.status_code,
                error_kind=error_kind,
                error_message=f"http {response.status_code} for {path}",
            )

        try:
            payload = response.json()
        except ValueError:
            return RouterEndpointReadResult(
                endpoint=path,
                ok=False,
                status_code=response.status_code,
                error_kind=RouterEndpointErrorKind.INVALID_JSON,
                error_message=f"invalid json from {path}",
            )

        if not isinstance(payload, dict):
            return RouterEndpointReadResult(
                endpoint=path,
                ok=False,
                status_code=response.status_code,
                error_kind=RouterEndpointErrorKind.INVALID_SHAPE,
                error_message=f"unexpected json shape from {path}",
            )

        return RouterEndpointReadResult(
            endpoint=path,
            ok=True,
            status_code=response.status_code,
            payload=payload,
        )

    async def read_health(self) -> tuple[RouterEndpointReadResult, RouterHealthPayload | None]:
        result = await self._get_json(self._config.health_path)
        if not result.ok:
            return result, None

        with suppress(Exception):
            return result, RouterHealthPayload.model_validate(result.payload or {})

        return (
            RouterEndpointReadResult(
                endpoint=self._config.health_path,
                ok=False,
                status_code=result.status_code,
                error_kind=RouterEndpointErrorKind.INVALID_PAYLOAD,
                error_message=f"invalid health payload from {self._config.health_path}",
            ),
            None,
        )

    async def read_service_status(self) -> tuple[RouterEndpointReadResult, RouterServiceStatusPayload | None]:
        result = await self._get_json(self._config.status_path)
        if not result.ok:
            return result, None

        with suppress(Exception):
            return result, RouterServiceStatusPayload.model_validate(result.payload or {})

        return (
            RouterEndpointReadResult(
                endpoint=self._config.status_path,
                ok=False,
                status_code=result.status_code,
                error_kind=RouterEndpointErrorKind.INVALID_PAYLOAD,
                error_message=f"invalid service status payload from {self._config.status_path}",
            ),
            None,
        )

    async def probe(self) -> GuardianRouterProbe:
        health_result, health = await self.read_health()
        service_result, service_status = await self.read_service_status()

        findings: list[GuardianFindingModel] = []
        errors: list[str] = []

        reachable = health_result.ok
        service_active = service_status.active if service_status is not None else None

        if health is None:
            if health_result.error_message:
                errors.append(health_result.error_message)
            findings.append(
                GuardianFindingModel(
                    code="router_health_unreachable",
                    summary="Router health endpoint is not reachable.",
                    severity=GuardianSeverity.CRITICAL,
                    source=GuardianSignalSource.ROUTER,
                    detail=health_result.error_message,
                    evidence={"endpoint": self._config.health_path, "base_url": self._config.base_url},
                )
            )
        else:
            health_status = (health.status or "").strip().lower()
            if health_status and health_status != "ok":
                severity = GuardianSeverity.WARN if health_status == "degraded" else GuardianSeverity.CRITICAL
                findings.append(
                    GuardianFindingModel(
                        code="router_health_degraded",
                        summary=f"Router health status reported {health_status!r}.",
                        severity=severity,
                        source=GuardianSignalSource.ROUTER,
                        evidence=health.model_dump(mode="json"),
                    )
                )

        if service_status is None:
            if service_result.auth_required:
                findings.append(
                    GuardianFindingModel(
                        code="router_service_status_auth_required",
                        summary="Router service status endpoint requires router authentication.",
                        severity=GuardianSeverity.INFO,
                        source=GuardianSignalSource.ROUTER,
                        detail=service_result.error_message,
                        evidence={"endpoint": self._config.status_path, "base_url": self._config.base_url},
                    )
                )
            else:
                if service_result.error_message:
                    errors.append(service_result.error_message)
                findings.append(
                    GuardianFindingModel(
                        code="router_service_status_unreachable",
                        summary="Router service status endpoint is not reachable.",
                        severity=GuardianSeverity.WARN,
                        source=GuardianSignalSource.ROUTER,
                        detail=service_result.error_message,
                        evidence={"endpoint": self._config.status_path, "base_url": self._config.base_url},
                    )
                )
        elif service_active is False:
            findings.append(
                GuardianFindingModel(
                    code="router_service_inactive",
                    summary="Router service status reports an inactive service.",
                    severity=GuardianSeverity.CRITICAL,
                    source=GuardianSignalSource.ROUTER,
                    evidence=service_status.model_dump(mode="json"),
                )
            )

        if not health_result.ok and health_result.error_message and health_result.error_kind != RouterEndpointErrorKind.AUTH_REQUIRED:
            errors.append(health_result.error_message)
        if not service_result.ok and service_result.error_message and service_result.error_kind != RouterEndpointErrorKind.AUTH_REQUIRED:
            errors.append(service_result.error_message)

        status = GuardianSeverity.OK
        if any(item.severity == GuardianSeverity.CRITICAL for item in findings):
            status = GuardianSeverity.CRITICAL
        elif any(item.severity == GuardianSeverity.WARN for item in findings):
            status = GuardianSeverity.WARN

        action = GuardianAction.NONE
        if status == GuardianSeverity.CRITICAL and health is None:
            action = GuardianAction.ALERT

        return GuardianRouterProbe(
            status=status,
            action=action,
            reachable=reachable,
            service_active=service_active,
            health_result=health_result,
            service_status_result=service_result,
            health=health,
            service_status=service_status,
            findings=findings,
            errors=errors,
            router_base_url=self._config.base_url,
            health_path=self._config.health_path,
            status_path=self._config.status_path,
        )
