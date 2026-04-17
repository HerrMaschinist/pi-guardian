import json

from sqlmodel import Session, select

from app.models.route_history import RouteHistory


def list_route_history(session: Session, limit: int = 50) -> list[RouteHistory]:
    return session.exec(
        select(RouteHistory).order_by(RouteHistory.created_at.desc()).limit(limit)
    ).all()


def create_route_history_entry(
    session: Session,
    *,
    request_id: str,
    prompt_preview: str,
    model: str | None,
    success: bool,
    error_code: str | None,
    client_name: str | None,
    duration_ms: int | None,
    fairness_review_attempted: bool = False,
    fairness_review_used: bool = False,
    fairness_risk: str = "unknown",
    fairness_review_override: bool = False,
    escalation_threshold: str | None = None,
    fairness_reasons: list[str] | None = None,
    fairness_notes: list[str] | None = None,
) -> None:
    session.add(
        RouteHistory(
            request_id=request_id,
            prompt_preview=prompt_preview,
            model=model,
            success=success,
            error_code=error_code,
            client_name=client_name,
            duration_ms=duration_ms,
            fairness_review_attempted=fairness_review_attempted,
            fairness_review_used=fairness_review_used,
            fairness_risk=fairness_risk,
            fairness_review_override=fairness_review_override,
            fairness_threshold=escalation_threshold,
            fairness_reasons=json.dumps(fairness_reasons or [], ensure_ascii=False),
            fairness_notes=json.dumps(fairness_notes or [], ensure_ascii=False),
        )
    )
    session.commit()
