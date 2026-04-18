import time
import uuid

from sqlmodel import Session

from app.config import settings
from app.router.execution.service import (
    build_route_tool_plan,
    create_policy_trace,
    render_route_tool_response,
    route_execution_service,
)
from app.router.auth import AuthorizedClientContext
from app.router.decision.models import RequestClassification
from app.router.decision.service import decide_route_request
from app.router.errors import RouterApiError
from app.router.fairness import assess_fairness
from app.router.history import create_route_history_entry
from app.router.policy import apply_client_policy
from app.router.ollama_client import generate_with_ollama
from app.schemas.request_models import RouteRequest
from app.schemas.response_models import RouteResponse


def _prompt_preview(prompt: str, limit: int = 160) -> str:
    return " ".join(prompt.split())[:limit]


def _default_policy_trace(classification: str) -> dict:
    return create_policy_trace(
        can_use_llm=True,
        can_use_tools=False,
        can_use_internet=False,
        decision_classification=classification,
    ).model_dump(mode="json")


async def route_prompt(
    request: RouteRequest,
    session: Session,
    client_context: AuthorizedClientContext | None = None,
    client_name: str | None = None,
) -> RouteResponse:
    request_id = str(uuid.uuid4())
    started_at = time.perf_counter()
    preview = _prompt_preview(request.prompt)
    resolved_client_name = client_context.name if client_context is not None else client_name
    decision = decide_route_request(request)
    policy_trace = (
        create_policy_trace(
            can_use_llm=bool(client_context.policy.can_use_llm),
            can_use_tools=bool(client_context.policy.can_use_tools),
            can_use_internet=bool(client_context.policy.can_use_internet),
            decision_classification=decision.classification.value,
        ).model_dump(mode="json")
        if client_context is not None
        else _default_policy_trace(decision.classification.value)
    )
    decision = apply_client_policy(
        decision,
        client_context.policy if client_context is not None else None,
    )
    selected_model = decision.selected_model or settings.DEFAULT_MODEL

    if decision.classification is RequestClassification.BLOCKED:
        duration_ms = int((time.perf_counter() - started_at) * 1000)
        create_route_history_entry(
            session,
            request_id=request_id,
            prompt_preview=preview,
            model=None,
            success=False,
            error_code="request_blocked",
            client_name=resolved_client_name,
            duration_ms=duration_ms,
            decision_classification=decision.classification.value,
            decision_reasons=decision.reasons,
            decision_tool_hints=decision.tool_hints,
            decision_internet_hints=decision.internet_hints,
            policy_trace=policy_trace,
            execution_mode="llm",
            execution_status="failed",
            execution_error="request_blocked",
        )
        raise RouterApiError(
            message="Anfrage wurde durch die vorgelagerte Entscheidungslogik blockiert",
            status_code=403,
            code="request_blocked",
            request_id=request_id,
            retryable=False,
        )

    if decision.classification is RequestClassification.INTERNET_REQUIRED:
        duration_ms = int((time.perf_counter() - started_at) * 1000)
        create_route_history_entry(
            session,
            request_id=request_id,
            prompt_preview=preview,
            model=None,
            success=False,
            error_code="internet_execution_unavailable",
            client_name=resolved_client_name,
            duration_ms=duration_ms,
            decision_classification=decision.classification.value,
            decision_reasons=decision.reasons,
            decision_tool_hints=decision.tool_hints,
            decision_internet_hints=decision.internet_hints,
            policy_trace=policy_trace,
            execution_mode="internet_pending",
            execution_status="failed",
            execution_error=(
                "Internet-Zugriff ist architektonisch klassifiziert, aber im "
                "normalen `/route`-Pfad noch nicht kontrolliert aktiviert."
            ),
        )
        raise RouterApiError(
            message=(
                "Internet-Anfragen werden erkannt, aber im normalen `/route`-Pfad "
                "noch nicht kontrolliert ausgeführt."
            ),
            status_code=501,
            code="internet_execution_unavailable",
            request_id=request_id,
            retryable=False,
        )

    if decision.classification is RequestClassification.TOOL_REQUIRED:
        plans = build_route_tool_plan(request.prompt, decision.tool_hints)
        if not plans:
            duration_ms = int((time.perf_counter() - started_at) * 1000)
            create_route_history_entry(
                session,
                request_id=request_id,
                prompt_preview=preview,
                model=None,
                success=False,
                error_code="tool_execution_not_supported",
                client_name=resolved_client_name,
                duration_ms=duration_ms,
                decision_classification=decision.classification.value,
                decision_reasons=decision.reasons,
                decision_tool_hints=decision.tool_hints,
                decision_internet_hints=decision.internet_hints,
                policy_trace=policy_trace,
                execution_mode="tool",
                execution_status="failed",
                executed_tools=[],
                execution_error=(
                    "Für diese Tool-Hinweise ist im normalen `/route`-Pfad noch "
                    "kein kontrolliert ausführbares Tool verdrahtet."
                ),
            )
            raise RouterApiError(
                message=(
                    "Tool-Bedarf wurde erkannt, aber für diese Anfrage ist im "
                    "normalen `/route`-Pfad noch kein kontrolliert ausführbares Tool "
                    "verdrahtet."
                ),
                status_code=422,
                code="tool_execution_not_supported",
                request_id=request_id,
                retryable=False,
            )

        tool_executions = await route_execution_service.execute_tools(
            plans=plans,
            request_id=request_id,
            policy_trace=create_policy_trace(
                can_use_llm=policy_trace["can_use_llm"],
                can_use_tools=policy_trace["can_use_tools"],
                can_use_internet=policy_trace["can_use_internet"],
                decision_classification=policy_trace["decision_classification"],
            ),
        )
        execution_error = None
        success = any(execution.success for execution in tool_executions)
        if not success:
            execution_error = "Alle geplanten Tools sind fehlgeschlagen."

        duration_ms = int((time.perf_counter() - started_at) * 1000)
        create_route_history_entry(
            session,
            request_id=request_id,
            prompt_preview=preview,
            model=None,
            success=success,
            error_code=None if success else "tool_execution_failed",
            client_name=resolved_client_name,
            duration_ms=duration_ms,
            decision_classification=decision.classification.value,
            decision_reasons=decision.reasons,
            decision_tool_hints=decision.tool_hints,
            decision_internet_hints=decision.internet_hints,
            policy_trace=policy_trace,
            execution_mode="tool",
            execution_status="succeeded" if success else "failed",
            executed_tools=[execution.tool_name for execution in tool_executions],
            tool_execution_records=[
                execution.model_dump(mode="json") for execution in tool_executions
            ],
            execution_error=execution_error,
        )
        if not success:
            raise RouterApiError(
                message="Geplante Tool-Ausführung ist fehlgeschlagen.",
                status_code=502,
                code="tool_execution_failed",
                request_id=request_id,
                retryable=False,
            )

        return RouteResponse(
            request_id=request_id,
            model="tool_executor",
            response=render_route_tool_response(tool_executions),
            done=True,
            done_reason="tool_execution_completed",
            duration_ms=duration_ms,
            decision_classification=decision.classification.value,
            decision_reasons=decision.reasons,
            decision_tool_hints=decision.tool_hints,
            decision_internet_hints=decision.internet_hints,
            execution_mode="tool",
            policy_trace=policy_trace,
            tool_executions=[
                execution.model_dump(mode="json") for execution in tool_executions
            ],
            execution_error=execution_error,
        )

    fairness = await assess_fairness(
        prompt=request.prompt,
        selected_model=selected_model,
        request_id=request_id,
    )

    if fairness.override_to_large and selected_model != settings.LARGE_MODEL:
        selected_model = settings.LARGE_MODEL

    try:
        result = await generate_with_ollama(
            model=selected_model,
            prompt=request.prompt,
            request_id=request_id,
            stream=request.stream,
        )
        duration_ms = int((time.perf_counter() - started_at) * 1000)
        resolved_model = result.get("model", selected_model)
        create_route_history_entry(
            session,
            request_id=request_id,
            prompt_preview=preview,
            model=resolved_model,
            success=True,
            error_code=None,
            client_name=resolved_client_name,
            duration_ms=duration_ms,
            decision_classification=decision.classification.value,
            decision_reasons=decision.reasons,
            decision_tool_hints=decision.tool_hints,
            decision_internet_hints=decision.internet_hints,
            policy_trace=policy_trace,
            execution_mode="llm",
            execution_status="not_executed",
            fairness_review_attempted=fairness.attempted,
            fairness_review_used=fairness.used,
            fairness_risk=fairness.risk,
            fairness_review_override=fairness.override_to_large,
            escalation_threshold=fairness.threshold,
            fairness_reasons=fairness.reasons,
            fairness_notes=fairness.notes,
        )
        return RouteResponse(
            request_id=request_id,
            model=resolved_model,
            response=result.get("response", ""),
            done=result.get("done", False),
            done_reason=result.get("done_reason"),
            duration_ms=duration_ms,
            decision_classification=decision.classification.value,
            decision_reasons=decision.reasons,
            decision_tool_hints=decision.tool_hints,
            decision_internet_hints=decision.internet_hints,
            fairness_review_attempted=fairness.attempted,
            fairness_review_used=fairness.used,
            fairness_risk=fairness.risk,
            fairness_review_override=fairness.override_to_large,
            fairness_reasons=fairness.reasons,
            fairness_notes=fairness.notes,
            execution_mode="llm",
            policy_trace=policy_trace,
        )
    except RouterApiError as exc:
        create_route_history_entry(
            session,
            request_id=request_id,
            prompt_preview=preview,
            model=selected_model,
            success=False,
            error_code=exc.code,
            client_name=resolved_client_name,
            duration_ms=int((time.perf_counter() - started_at) * 1000),
            decision_classification=decision.classification.value,
            decision_reasons=decision.reasons,
            decision_tool_hints=decision.tool_hints,
            decision_internet_hints=decision.internet_hints,
            policy_trace=policy_trace,
            execution_mode="llm",
            execution_status="failed",
            execution_error=exc.code,
            fairness_review_attempted=fairness.attempted,
            fairness_review_used=fairness.used,
            fairness_risk=fairness.risk,
            fairness_review_override=fairness.override_to_large,
            escalation_threshold=fairness.threshold,
            fairness_reasons=fairness.reasons,
            fairness_notes=fairness.notes,
        )
        raise
