from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

from pydantic import ValidationError

from app.models.agent_models import AgentPolicySettings, ToolResult
from app.models.tool_models import ToolExecutionContext, ToolExecutionRecord
from app.tools.registry import get_tool

logger = logging.getLogger(__name__)


class ToolExecutionError(RuntimeError):
    pass


def _policy_denies_tool(tool_category: str, policy: AgentPolicySettings) -> str | None:
    if not policy.read_only:
        return "read_only Agenten dürfen keine nicht-lesenden Rechte erhalten"
    if tool_category == "logs" and not policy.can_use_logs:
        return "Logs sind für diesen Agenten nicht freigegeben"
    if tool_category == "services" and not policy.can_use_services:
        return "Service-Tools sind für diesen Agenten nicht freigegeben"
    if tool_category == "docker" and not policy.can_use_docker:
        return "Docker-Tools sind für diesen Agenten nicht freigegeben"
    return None


class ToolExecutor:
    def __init__(self, timeout_seconds: float = 10.0) -> None:
        self.timeout_seconds = timeout_seconds

    async def execute(
        self,
        tool_name: str,
        arguments: dict[str, Any] | None,
        *,
        allowed_tools: list[str],
        context: ToolExecutionContext,
    ) -> ToolResult:
        start = time.perf_counter()
        policy = context.policy
        logger.info(
            "tool_call_start agent=%s step=%s tool=%s",
            context.agent_name,
            context.step_number,
            tool_name,
        )

        if tool_name not in allowed_tools:
            error = f"Tool nicht für Agent freigegeben: {tool_name}"
            logger.warning(
                "tool_call_denied agent=%s step=%s tool=%s",
                context.agent_name,
                context.step_number,
                tool_name,
            )
            return ToolResult(tool_name=tool_name, success=False, error=error)

        tool = get_tool(tool_name)
        if tool is None:
            error = f"Unbekanntes Tool: {tool_name}"
            logger.warning(
                "tool_call_unknown agent=%s step=%s tool=%s",
                context.agent_name,
                context.step_number,
                tool_name,
            )
            return ToolResult(tool_name=tool_name, success=False, error=error)

        if not tool.read_only:
            error = f"Nicht-lesendes Tool ist für Agenten gesperrt: {tool_name}"
            logger.warning(
                "tool_call_write_blocked agent=%s step=%s tool=%s",
                context.agent_name,
                context.step_number,
                tool_name,
            )
            return ToolResult(tool_name=tool_name, success=False, error=error)

        policy_error = _policy_denies_tool(tool.category, policy)
        if policy_error is not None:
            logger.warning(
                "tool_call_policy_denied agent=%s step=%s tool=%s category=%s",
                context.agent_name,
                context.step_number,
                tool_name,
                tool.category,
            )
            return ToolResult(tool_name=tool_name, success=False, error=policy_error)

        if policy.max_tool_calls is not None and context.tool_call_number > policy.max_tool_calls:
            error = (
                f"Maximale Tool-Aufrufe überschritten: {context.tool_call_number} > "
                f"{policy.max_tool_calls}"
            )
            logger.warning(
                "tool_call_limit_denied agent=%s step=%s tool=%s tool_call_number=%s max_tool_calls=%s",
                context.agent_name,
                context.step_number,
                tool_name,
                context.tool_call_number,
                policy.max_tool_calls,
            )
            return ToolResult(tool_name=tool_name, success=False, error=error)

        try:
            validated_input = tool.validate_arguments(arguments)
        except ValidationError as exc:
            error = f"Ungültige Tool-Argumente für {tool_name}: {exc.errors()}"
            logger.warning(
                "tool_call_validation_failed agent=%s step=%s tool=%s error=%s",
                context.agent_name,
                context.step_number,
                tool_name,
                error,
            )
            return ToolResult(tool_name=tool_name, success=False, error=error)
        except Exception as exc:
            error = f"Tool-Argumente konnten nicht validiert werden: {exc}"
            logger.warning(
                "tool_call_validation_error agent=%s step=%s tool=%s error=%s",
                context.agent_name,
                context.step_number,
                tool_name,
                exc,
            )
            return ToolResult(tool_name=tool_name, success=False, error=error)

        try:
            result = await asyncio.wait_for(
                asyncio.to_thread(tool.execute, validated_input),
                timeout=self.timeout_seconds,
            )
        except asyncio.TimeoutError:
            error = f"Tool-Timeout nach {self.timeout_seconds:.1f}s: {tool_name}"
            logger.warning(
                "tool_call_timeout agent=%s step=%s tool=%s",
                context.agent_name,
                context.step_number,
                tool_name,
            )
            return ToolResult(tool_name=tool_name, success=False, error=error)
        except Exception as exc:
            error = f"Tool-Ausführung fehlgeschlagen: {exc}"
            logger.exception(
                "tool_call_failed agent=%s step=%s tool=%s",
                context.agent_name,
                context.step_number,
                tool_name,
            )
            return ToolResult(tool_name=tool_name, success=False, error=error)

        duration_ms = int((time.perf_counter() - start) * 1000)
        record = ToolExecutionRecord(
            tool_name=tool_name,
            success=result.success,
            duration_ms=duration_ms,
            output=result.output,
            error=result.error,
        )
        logger.info(
            "tool_call_end agent=%s step=%s tool=%s success=%s duration_ms=%s",
            context.agent_name,
            context.step_number,
            tool_name,
            record.success,
            record.duration_ms,
        )
        return result
