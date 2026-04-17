import time
import uuid

from sqlmodel import Session

from app.config import settings
from app.router.classifier import select_model
from app.router.errors import RouterApiError
from app.router.fairness import assess_fairness
from app.router.history import create_route_history_entry
from app.router.ollama_client import generate_with_ollama
from app.schemas.request_models import RouteRequest
from app.schemas.response_models import RouteResponse


def _prompt_preview(prompt: str, limit: int = 160) -> str:
    return " ".join(prompt.split())[:limit]


async def route_prompt(
    request: RouteRequest,
    session: Session,
    client_name: str | None = None,
) -> RouteResponse:
    request_id = str(uuid.uuid4())
    selected_model = select_model(request)
    started_at = time.perf_counter()
    preview = _prompt_preview(request.prompt)
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
            client_name=client_name,
            duration_ms=duration_ms,
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
            fairness_review_attempted=fairness.attempted,
            fairness_review_used=fairness.used,
            fairness_risk=fairness.risk,
            fairness_review_override=fairness.override_to_large,
            fairness_reasons=fairness.reasons,
            fairness_notes=fairness.notes,
        )
    except RouterApiError as exc:
        create_route_history_entry(
            session,
            request_id=request_id,
            prompt_preview=preview,
            model=selected_model,
            success=False,
            error_code=exc.code,
            client_name=client_name,
            duration_ms=int((time.perf_counter() - started_at) * 1000),
            fairness_review_attempted=fairness.attempted,
            fairness_review_used=fairness.used,
            fairness_risk=fairness.risk,
            fairness_review_override=fairness.override_to_large,
            escalation_threshold=fairness.threshold,
            fairness_reasons=fairness.reasons,
            fairness_notes=fairness.notes,
        )
        raise
