from __future__ import annotations

import time

from app.models.agent_models import AgentPolicySettings
from app.models.tool_models import ToolExecutionContext
from app.router.execution.models import RoutePolicyTrace, RouteToolExecution, RouteToolPlan
from app.tools.executor import ToolExecutor


_ROUTE_SAFE_TOOLS = {"system_status", "service_status"}


def _extract_service_name(prompt: str) -> str | None:
    prompt_lower = prompt.lower()
    if "ollama" in prompt_lower:
        return "ollama"
    if "pi-guardian-router" in prompt_lower or "router" in prompt_lower:
        return "pi-guardian-router"
    if "docker" in prompt_lower and (
        "service" in prompt_lower
        or "dienst" in prompt_lower
        or "systemd" in prompt_lower
    ):
        return "docker"
    return None


def build_route_tool_plan(prompt: str, tool_hints: list[str]) -> list[RouteToolPlan]:
    prompt_lower = prompt.lower()
    plans: list[RouteToolPlan] = []

    if "system_status" in tool_hints:
        plans.append(
            RouteToolPlan(
                tool_name="system_status",
                arguments={},
                reason="Systemmetriken wurden als lokaler Read-Only-Status erkannt",
            )
        )

    if "service_status" in tool_hints:
        service_name = _extract_service_name(prompt_lower)
        if service_name is not None:
            plans.append(
                RouteToolPlan(
                    tool_name="service_status",
                    arguments={"service_name": service_name},
                    reason=f"Dienststatus für {service_name} wurde aus dem Prompt abgeleitet",
                )
            )

    # Keine implizite Freigabe weiterer Tools im normalen `/route`-Pfad.
    deduplicated: list[RouteToolPlan] = []
    seen: set[tuple[str, tuple[tuple[str, str], ...]]] = set()
    for plan in plans:
        key = (
            plan.tool_name,
            tuple(sorted((name, str(value)) for name, value in plan.arguments.items())),
        )
        if key in seen:
            continue
        seen.add(key)
        deduplicated.append(plan)
    return deduplicated[:2]


def create_policy_trace(
    *,
    can_use_llm: bool,
    can_use_tools: bool,
    can_use_internet: bool,
    decision_classification: str,
) -> RoutePolicyTrace:
    return RoutePolicyTrace(
        can_use_llm=can_use_llm,
        can_use_tools=can_use_tools,
        can_use_internet=can_use_internet,
        decision_classification=decision_classification,
        tool_execution_allowed=can_use_tools and decision_classification == "tool_required",
        internet_execution_allowed=(
            can_use_internet and decision_classification == "internet_required"
        ),
    )


def _tool_policy_for_route(plans: list[RouteToolPlan]) -> AgentPolicySettings:
    allowed_tools = [plan.tool_name for plan in plans if plan.tool_name in _ROUTE_SAFE_TOOLS]
    return AgentPolicySettings(
        allowed_tools=allowed_tools,
        read_only=True,
        can_use_logs=False,
        can_use_services="service_status" in allowed_tools,
        can_use_docker=False,
        max_steps=1,
        max_tool_calls=len(allowed_tools) or None,
    )


def render_route_tool_response(executions: list[RouteToolExecution]) -> str:
    lines: list[str] = []
    for execution in executions:
        if execution.tool_name == "system_status" and execution.success:
            memory = execution.output.get("memory", {}) if isinstance(execution.output, dict) else {}
            disk = execution.output.get("disk", {}) if isinstance(execution.output, dict) else {}
            lines.append(
                "Systemstatus gelesen:"
                f" Uptime={execution.output.get('uptime_seconds', 'n/a')}s,"
                f" RAM={memory.get('used_percent', 'n/a')}%,"
                f" Disk={disk.get('used_percent', 'n/a')}%"
            )
            continue

        if execution.tool_name == "service_status" and execution.success:
            lines.append(
                "Dienststatus gelesen:"
                f" {execution.output.get('service_name', 'unbekannt')}="
                f"{execution.output.get('active_state', 'unknown')}/"
                f"{execution.output.get('sub_state', 'unknown')}"
            )
            continue

        if execution.success:
            lines.append(f"{execution.tool_name} erfolgreich ausgeführt.")
        else:
            lines.append(
                f"{execution.tool_name} fehlgeschlagen: {execution.error or 'unbekannter Fehler'}"
            )
    return "\n".join(lines)


class RouteExecutionService:
    def __init__(self, tool_executor: ToolExecutor | None = None) -> None:
        self.tool_executor = tool_executor or ToolExecutor(timeout_seconds=8.0)

    async def execute_tools(
        self,
        *,
        plans: list[RouteToolPlan],
        request_id: str,
        policy_trace: RoutePolicyTrace,
    ) -> list[RouteToolExecution]:
        policy = _tool_policy_for_route(plans)
        executions: list[RouteToolExecution] = []

        for index, plan in enumerate(plans, start=1):
            started_at = time.perf_counter()
            result = await self.tool_executor.execute(
                plan.tool_name,
                plan.arguments,
                allowed_tools=policy.allowed_tools,
                context=ToolExecutionContext(
                    agent_name="route_executor",
                    tool_name=plan.tool_name,
                    step_number=index,
                    request_id=request_id,
                    allowed_tools=policy.allowed_tools,
                    tool_call_number=index,
                    policy=policy,
                ),
            )
            executions.append(
                RouteToolExecution(
                    tool_name=plan.tool_name,
                    arguments=plan.arguments,
                    reason=plan.reason,
                    success=result.success,
                    duration_ms=int((time.perf_counter() - started_at) * 1000),
                    output=result.output,
                    error=result.error,
                )
            )

        return executions


route_execution_service = RouteExecutionService()
