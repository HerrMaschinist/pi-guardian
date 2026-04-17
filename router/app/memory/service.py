from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime
from typing import Any

from sqlmodel import Session
from sqlmodel import select

from app.database import engine
from app.memory.models import (
    ActionExecutionRecord,
    ActionProposalRecord,
    AgentRunRecord,
    AgentStepRecord,
    ApprovalRecord,
    FeedbackEntryRecord,
    IncidentFindingRecord,
    IncidentRecord,
    KnowledgeEntryRecord,
    SkillRunRecord,
    ToolCallRecord,
    ToolResultRecord,
)
from app.memory.schemas import (
    MemoryActionExecutionRead,
    MemoryActionProposalRead,
    MemoryApprovalRead,
    MemoryFeedbackEntryRead,
    MemoryIncidentFindingRead,
    MemoryIncidentRead,
    MemoryKnowledgeEntryRead,
    MemoryRunDetail,
    MemoryRunSummary,
    MemorySkillRunRead,
    MemoryStepRead,
    MemoryToolCallRead,
    MemoryToolResultRead,
)
from app.models.action_models import ActionProposal, ActionResult
from app.models.agent_models import AgentRunRequest, AgentRunResponse, AgentStep, ToolCall, ToolResult
from app.models.skill_models import SkillResult

logger = logging.getLogger(__name__)


def _json_dumps(value: Any) -> str:
    if hasattr(value, "model_dump"):
        value = value.model_dump(mode="json")
    return json.dumps(value, ensure_ascii=False, default=str)


def _json_load(value: str) -> Any:
    try:
        return json.loads(value)
    except Exception:
        return value


def _safe_execute(callback):
    try:
        with Session(engine) as session:
            return callback(session)
    except Exception as exc:
        logger.warning("Memory-Operation fehlgeschlagen: %s", exc)
        return None


def record_reference_data_seed() -> None:
    from app.persistence.reference_data import bootstrap_reference_data

    _safe_execute(bootstrap_reference_data)


def _store_run(
    session: Session,
    *,
    request: AgentRunRequest,
    response: AgentRunResponse,
) -> str:
    run_id = str(uuid.uuid4())
    now = datetime.now()
    session.add(
        AgentRunRecord(
            run_id=response.run_id or run_id,
            agent_name=request.agent_name,
            input=request.prompt,
            used_model=response.used_model,
            success=response.success,
            final_answer=response.final_answer,
            started_at=now,
            finished_at=now,
        )
    )

    for item in response.steps:
        _store_step(session, run_id=response.run_id or run_id, agent_name=request.agent_name, step=item)

    session.commit()
    return response.run_id or run_id


def _store_step(session: Session, *, run_id: str, agent_name: str, step: AgentStep) -> None:
    session.add(
        AgentStepRecord(
            run_id=run_id,
            step_number=step.step_number,
            action_type=step.action,
            observation=step.observation,
            raw_payload=_json_dumps(step.tool_call_or_response),
        )
    )

    payload = step.tool_call_or_response
    if step.action == "tool_call" and isinstance(payload, ToolCall):
        session.add(
            ToolCallRecord(
                run_id=run_id,
                step_number=step.step_number,
                tool_name=payload.tool_name,
                arguments=_json_dumps(payload.arguments),
                reason=payload.reason,
            )
        )
    elif step.action == "tool_result" and isinstance(payload, ToolResult):
        session.add(
            ToolResultRecord(
                run_id=run_id,
                step_number=step.step_number,
                tool_name=payload.tool_name,
                success=payload.success,
                output=_json_dumps(payload.output),
                error=payload.error,
            )
        )
    elif step.action == "skill_call":
        skill_name = getattr(payload, "skill_name", "")
        arguments = getattr(payload, "arguments", {})
        reason = getattr(payload, "reason", "")
        session.add(
            SkillRunRecord(
                run_id=run_id,
                step_number=step.step_number,
                skill_name=skill_name,
                arguments=_json_dumps(arguments),
                reason=reason,
                success=False,
                output="{}",
                error=None,
            )
        )
    elif step.action == "skill_result" and isinstance(payload, SkillResult):
        existing = session.exec(
            select(SkillRunRecord)
            .where(SkillRunRecord.run_id == run_id)
            .where(SkillRunRecord.step_number == step.step_number)
            .where(SkillRunRecord.skill_name == payload.skill_name)
        ).first()
        if existing is None:
            session.add(
                SkillRunRecord(
                    run_id=run_id,
                    step_number=step.step_number,
                    skill_name=payload.skill_name,
                    arguments="{}",
                    reason=step.observation or "",
                    success=payload.success,
                    output=_json_dumps(payload.output),
                    error=payload.error,
                )
            )
        else:
            existing.success = payload.success
            existing.output = _json_dumps(payload.output)
            existing.error = payload.error
            session.add(existing)
    elif step.action == "action_proposal" and isinstance(payload, ActionProposal):
        proposal_id = str(uuid.uuid4())
        session.add(
            ActionProposalRecord(
                proposal_id=proposal_id,
                run_id=run_id,
                agent_name=agent_name,
                action_name=payload.action_name,
                arguments=_json_dumps(payload.arguments),
                reason=payload.reason,
                target=payload.target,
                requires_approval=payload.requires_approval,
            )
        )


def record_agent_run(request: AgentRunRequest, response: AgentRunResponse) -> str | None:
    def _callback(session: Session) -> str:
        return _store_run(session, request=request, response=response)

    return _safe_execute(_callback)


def record_skill_run(
    *,
    run_id: str,
    step_number: int,
    skill_name: str,
    arguments: dict[str, Any],
    reason: str,
    success: bool,
    output: Any,
    error: str | None = None,
) -> None:
    def _callback(session: Session) -> None:
        session.add(
            SkillRunRecord(
                run_id=run_id,
                step_number=step_number,
                skill_name=skill_name,
                arguments=_json_dumps(arguments),
                reason=reason,
                success=success,
                output=_json_dumps(output),
                error=error,
            )
        )
        session.commit()

    _safe_execute(_callback)


def record_action_proposal(
    *,
    proposal_id: str,
    run_id: str | None,
    agent_name: str,
    action_name: str,
    arguments: dict[str, Any],
    reason: str,
    target: str | None,
    requires_approval: bool,
) -> None:
    def _callback(session: Session) -> None:
        session.add(
            ActionProposalRecord(
                proposal_id=proposal_id,
                run_id=run_id,
                agent_name=agent_name,
                action_name=action_name,
                arguments=_json_dumps(arguments),
                reason=reason,
                target=target,
                requires_approval=requires_approval,
            )
        )
        session.commit()

    _safe_execute(_callback)


def record_action_execution(
    *,
    proposal_id: str,
    run_id: str | None,
    action_name: str,
    approved: bool,
    success: bool,
    output: Any,
    error: str | None = None,
) -> None:
    def _callback(session: Session) -> None:
        session.add(
            ActionExecutionRecord(
                proposal_id=proposal_id,
                run_id=run_id,
                action_name=action_name,
                approved=approved,
                success=success,
                output=_json_dumps(output),
                error=error,
            )
        )
        session.commit()

    _safe_execute(_callback)


def record_approval(
    *,
    proposal_id: str,
    approved_by: str | None,
    decision: str,
    comment: str | None = None,
) -> None:
    def _callback(session: Session) -> None:
        session.add(
            ApprovalRecord(
                proposal_id=proposal_id,
                approved_by=approved_by,
                decision=decision,
                comment=comment,
            )
        )
        session.commit()

    _safe_execute(_callback)


def create_incident(
    *,
    title: str,
    summary: str = "",
    severity: str = "medium",
    status: str = "open",
    related_run_id: str | None = None,
) -> int | None:
    def _callback(session: Session) -> int:
        incident = IncidentRecord(
            title=title,
            summary=summary,
            severity=severity,
            status=status,
            related_run_id=related_run_id,
        )
        session.add(incident)
        session.commit()
        session.refresh(incident)
        return incident.id or 0

    return _safe_execute(_callback)


def add_incident_finding(
    *,
    incident_id: int,
    source_type: str,
    source_ref: str,
    finding_type: str = "",
    content: str = "",
    confidence: float = 0.0,
) -> None:
    def _callback(session: Session) -> None:
        session.add(
            IncidentFindingRecord(
                incident_id=incident_id,
                source_type=source_type,
                source_ref=source_ref,
                finding_type=finding_type,
                content=content,
                confidence=confidence,
            )
        )
        session.commit()

    _safe_execute(_callback)


def create_knowledge_entry(
    *,
    title: str,
    pattern: str = "",
    probable_cause: str = "",
    recommended_checks: str = "",
    recommended_actions: str = "",
    confidence: float = 0.0,
    confirmed: bool = False,
    source: str = "",
) -> int | None:
    def _callback(session: Session) -> int:
        entry = KnowledgeEntryRecord(
            title=title,
            pattern=pattern,
            probable_cause=probable_cause,
            recommended_checks=recommended_checks,
            recommended_actions=recommended_actions,
            confidence=confidence,
            confirmed=confirmed,
            source=source,
        )
        session.add(entry)
        session.commit()
        session.refresh(entry)
        return entry.id or 0

    return _safe_execute(_callback)


def create_feedback_entry(
    *,
    related_run_id: str | None,
    related_incident_id: int | None,
    verdict: str,
    comment: str = "",
    created_by: str = "",
) -> int | None:
    def _callback(session: Session) -> int:
        entry = FeedbackEntryRecord(
            related_run_id=related_run_id,
            related_incident_id=related_incident_id,
            verdict=verdict,
            comment=comment,
            created_by=created_by,
        )
        session.add(entry)
        session.commit()
        session.refresh(entry)
        return entry.id or 0

    return _safe_execute(_callback)


def _load_json_field(value: str):
    try:
        return json.loads(value)
    except Exception:
        return value


def get_runs(session: Session) -> list[MemoryRunSummary]:
    runs = session.exec(
        select(AgentRunRecord).order_by(AgentRunRecord.started_at.desc())
    ).all()
    return [
        MemoryRunSummary(
            run_id=run.run_id,
            agent_name=run.agent_name,
            input=run.input,
            used_model=run.used_model,
            success=run.success,
            final_answer=run.final_answer,
            started_at=run.started_at,
            finished_at=run.finished_at,
        )
        for run in runs
    ]


def get_run(session: Session, run_id: str) -> MemoryRunDetail | None:
    run = session.exec(
        select(AgentRunRecord).where(AgentRunRecord.run_id == run_id)
    ).first()
    if run is None:
        return None

    steps = session.exec(
        select(AgentStepRecord)
        .where(AgentStepRecord.run_id == run_id)
        .order_by(AgentStepRecord.step_number.asc())
    ).all()
    tool_calls = session.exec(
        select(ToolCallRecord)
        .where(ToolCallRecord.run_id == run_id)
        .order_by(ToolCallRecord.step_number.asc())
    ).all()
    tool_results = session.exec(
        select(ToolResultRecord)
        .where(ToolResultRecord.run_id == run_id)
        .order_by(ToolResultRecord.step_number.asc())
    ).all()
    skill_runs = session.exec(
        select(SkillRunRecord)
        .where(SkillRunRecord.run_id == run_id)
        .order_by(SkillRunRecord.step_number.asc())
    ).all()
    action_proposals = session.exec(
        select(ActionProposalRecord)
        .where(ActionProposalRecord.run_id == run_id)
        .order_by(ActionProposalRecord.created_at.asc())
    ).all()
    action_executions = session.exec(
        select(ActionExecutionRecord)
        .where(ActionExecutionRecord.run_id == run_id)
        .order_by(ActionExecutionRecord.created_at.asc())
    ).all()
    approvals = session.exec(
        select(ApprovalRecord)
        .where(ApprovalRecord.proposal_id.in_([proposal.proposal_id for proposal in action_proposals]))
        .order_by(ApprovalRecord.approved_at.asc())
    ).all()

    return MemoryRunDetail(
        run_id=run.run_id,
        agent_name=run.agent_name,
        input=run.input,
        used_model=run.used_model,
        success=run.success,
        final_answer=run.final_answer,
        started_at=run.started_at,
        finished_at=run.finished_at,
        steps=[
            MemoryStepRead(
                step_number=step.step_number,
                action_type=step.action_type,
                observation=step.observation,
                raw_payload=_load_json_field(step.raw_payload),
                created_at=step.created_at,
            )
            for step in steps
        ],
        tool_calls=[
            MemoryToolCallRead(
                step_number=item.step_number,
                tool_name=item.tool_name,
                arguments=_load_json_field(item.arguments),
                reason=item.reason,
                created_at=item.created_at,
            )
            for item in tool_calls
        ],
        tool_results=[
            MemoryToolResultRead(
                step_number=item.step_number,
                tool_name=item.tool_name,
                success=item.success,
                output=_load_json_field(item.output),
                error=item.error,
                created_at=item.created_at,
            )
            for item in tool_results
        ],
        skill_runs=[
            MemorySkillRunRead(
                step_number=item.step_number,
                skill_name=item.skill_name,
                arguments=_load_json_field(item.arguments),
                reason=item.reason,
                success=item.success,
                output=_load_json_field(item.output),
                error=item.error,
                created_at=item.created_at,
            )
            for item in skill_runs
        ],
        action_proposals=[
            MemoryActionProposalRead(
                proposal_id=item.proposal_id,
                run_id=item.run_id,
                agent_name=item.agent_name,
                action_name=item.action_name,
                arguments=_load_json_field(item.arguments),
                reason=item.reason,
                target=item.target,
                requires_approval=item.requires_approval,
                created_at=item.created_at,
            )
            for item in action_proposals
        ],
        action_executions=[
            MemoryActionExecutionRead(
                proposal_id=item.proposal_id,
                run_id=item.run_id,
                action_name=item.action_name,
                approved=item.approved,
                success=item.success,
                output=_load_json_field(item.output),
                error=item.error,
                created_at=item.created_at,
            )
            for item in action_executions
        ],
        approvals=[
            MemoryApprovalRead(
                proposal_id=item.proposal_id,
                approved_by=item.approved_by,
                approved_at=item.approved_at,
                decision=item.decision,
                comment=item.comment,
            )
            for item in approvals
        ],
    )


def get_incidents(session: Session) -> list[MemoryIncidentRead]:
    incidents = session.exec(
        select(IncidentRecord).order_by(IncidentRecord.created_at.desc())
    ).all()
    result: list[MemoryIncidentRead] = []
    for incident in incidents:
        findings = session.exec(
            select(IncidentFindingRecord)
            .where(IncidentFindingRecord.incident_id == incident.id)
            .order_by(IncidentFindingRecord.id.asc())
        ).all()
        result.append(
            MemoryIncidentRead(
                id=incident.id or 0,
                title=incident.title,
                summary=incident.summary,
                severity=incident.severity,
                status=incident.status,
                related_run_id=incident.related_run_id,
                created_at=incident.created_at,
                updated_at=incident.updated_at,
                findings=[
                    MemoryIncidentFindingRead(
                        source_type=item.source_type,
                        source_ref=item.source_ref,
                        finding_type=item.finding_type,
                        content=item.content,
                        confidence=item.confidence,
                    )
                    for item in findings
                ],
            )
        )
    return result


def get_incident(session: Session, incident_id: int) -> MemoryIncidentRead | None:
    incident = session.get(IncidentRecord, incident_id)
    if incident is None:
        return None
    return next(
        (item for item in get_incidents(session) if item.id == incident_id),
        None,
    )


def get_knowledge_entries(session: Session) -> list[MemoryKnowledgeEntryRead]:
    entries = session.exec(
        select(KnowledgeEntryRecord).order_by(KnowledgeEntryRecord.updated_at.desc())
    ).all()
    return [
        MemoryKnowledgeEntryRead(
            id=item.id or 0,
            title=item.title,
            pattern=item.pattern,
            probable_cause=item.probable_cause,
            recommended_checks=item.recommended_checks,
            recommended_actions=item.recommended_actions,
            confidence=item.confidence,
            confirmed=item.confirmed,
            source=item.source,
            created_at=item.created_at,
            updated_at=item.updated_at,
        )
        for item in entries
    ]


def get_feedback_entries(session: Session) -> list[MemoryFeedbackEntryRead]:
    entries = session.exec(
        select(FeedbackEntryRecord).order_by(FeedbackEntryRecord.created_at.desc())
    ).all()
    return [
        MemoryFeedbackEntryRead(
            id=item.id or 0,
            related_run_id=item.related_run_id,
            related_incident_id=item.related_incident_id,
            verdict=item.verdict,
            comment=item.comment,
            created_by=item.created_by,
            created_at=item.created_at,
        )
        for item in entries
    ]
