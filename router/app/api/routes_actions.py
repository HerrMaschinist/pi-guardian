from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlmodel import Session

from app.actions.executor import executor as action_executor
from app.actions.registry import get_action, list_actions
from app.agents.registry import get_agent
from app.memory.service import (
    record_action_execution,
    record_action_proposal,
    record_approval,
)
from app.database import get_session
from app.models.action_models import (
    ActionDefinition,
    ActionExecuteRequest,
    ActionProposal,
    ActionProposalResponse,
    ActionResult,
    ActionProposalRequest,
    ActionExecutionContext,
)
from app.router.auth import authorize_protected_request

router = APIRouter(prefix="/actions", tags=["actions"])


def require_actions_access(
    request: Request,
    session: Session = Depends(get_session),
) -> None:
    authorize_protected_request(request, session, "/actions")


def _action_definition(action) -> ActionDefinition:
    return ActionDefinition(
        name=action.name,
        description=action.description,
        allowed_targets=list(action.allowed_targets),
        input_schema=action.input_schema.model_json_schema(),
        output_schema=action.output_schema.model_json_schema(),
        read_only=action.read_only,
        requires_approval=action.requires_approval,
        version=action.version,
        enabled=action.enabled,
    )


@router.get("", response_model=list[ActionDefinition], dependencies=[Depends(require_actions_access)])
async def actions_list() -> list[ActionDefinition]:
    return [_action_definition(action) for action in list_actions()]


@router.get(
    "/{action_name}",
    response_model=ActionDefinition,
    dependencies=[Depends(require_actions_access)],
)
async def action_detail(action_name: str) -> ActionDefinition:
    action = get_action(action_name)
    if action is None:
        raise HTTPException(status_code=404, detail="Action nicht gefunden")
    return _action_definition(action)


@router.post(
    "/propose",
    response_model=ActionProposalResponse,
    dependencies=[Depends(require_actions_access)],
)
async def propose_action(payload: ActionProposalRequest) -> ActionProposalResponse:
    agent = get_agent(payload.agent_name)
    if agent is None:
        raise HTTPException(status_code=404, detail=f"Agent nicht gefunden: {payload.agent_name}")
    action = get_action(payload.action_name)
    if action is None:
        raise HTTPException(status_code=404, detail=f"Action nicht gefunden: {payload.action_name}")
    proposal_id = str(uuid.uuid4())
    proposal = ActionProposal(
        action_name=payload.action_name,
        arguments=payload.arguments,
        reason=payload.reason,
        target=payload.target,
        requires_approval=True,
    )
    try:
        validated = action_executor.propose(proposal, policy=agent.settings.policy)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    record_action_proposal(
        proposal_id=proposal_id,
        run_id=None,
        agent_name=agent.name,
        action_name=payload.action_name,
        arguments=payload.arguments,
        reason=payload.reason,
        target=payload.target,
        requires_approval=True,
    )
    return ActionProposalResponse(
        proposal_id=proposal_id,
        agent_name=agent.name,
        proposal=validated,
        action=_action_definition(action),
    )


@router.post(
    "/execute",
    response_model=ActionResult,
    dependencies=[Depends(require_actions_access)],
)
async def execute_action(payload: ActionExecuteRequest) -> ActionResult:
    agent = get_agent(payload.agent_name)
    if agent is None:
        raise HTTPException(status_code=404, detail=f"Agent nicht gefunden: {payload.agent_name}")
    action = get_action(payload.action_name)
    if action is None:
        raise HTTPException(status_code=404, detail=f"Action nicht gefunden: {payload.action_name}")
    proposal_id = payload.proposal_id or str(uuid.uuid4())
    proposal = ActionProposal(
        action_name=payload.action_name,
        arguments=payload.arguments,
        reason=payload.reason,
        target=payload.target,
        requires_approval=True,
    )
    try:
        result = action_executor.execute(
            proposal,
            policy=agent.settings.policy,
            approved=payload.approved,
            context=ActionExecutionContext(
                agent_name=agent.name,
                action_name=payload.action_name,
                request_id=None,
                approved=payload.approved,
                target=payload.target,
            ),
        )
        record_approval(
            proposal_id=proposal_id,
            approved_by=None,
            decision="approved" if payload.approved else "rejected",
            comment=payload.reason,
        )
        record_action_execution(
            proposal_id=proposal_id,
            run_id=None,
            action_name=payload.action_name,
            approved=payload.approved,
            success=result.success,
            output=result.output,
            error=result.error,
        )
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Action konnte nicht ausgeführt werden: {exc}") from exc
