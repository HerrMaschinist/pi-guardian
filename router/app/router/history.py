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
    decision_classification: str = "llm_only",
    decision_reasons: list[str] | None = None,
    decision_tool_hints: list[str] | None = None,
    decision_internet_hints: list[str] | None = None,
    policy_trace: dict | None = None,
    execution_mode: str = "llm",
    execution_status: str = "not_executed",
    executed_tools: list[str] | None = None,
    tool_execution_records: list[dict] | None = None,
    execution_error: str | None = None,
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
            decision_classification=decision_classification,
            decision_reasons=json.dumps(decision_reasons or [], ensure_ascii=False),
            decision_tool_hints=json.dumps(decision_tool_hints or [], ensure_ascii=False),
            decision_internet_hints=json.dumps(
                decision_internet_hints or [], ensure_ascii=False
            ),
            policy_trace=json.dumps(policy_trace or {}, ensure_ascii=False, default=str),
            execution_mode=execution_mode,
            execution_status=execution_status,
            executed_tools=json.dumps(executed_tools or [], ensure_ascii=False),
            tool_execution_records=json.dumps(
                tool_execution_records or [], ensure_ascii=False, default=str
            ),
            execution_error=execution_error,
        )
    )
    session.commit()
