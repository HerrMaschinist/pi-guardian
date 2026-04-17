from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlmodel import Session

from app.agents.activity import attach_agent_activity
from app.agents.registry import (
    create_agent,
    delete_agent,
    disable_agent,
    enable_agent,
    get_agent,
    list_agents,
    update_agent,
    update_agent_settings,
)
from app.agents.runtime import run_agent
from app.database import get_session
from app.models.agent_models import (
    AgentCreateRequest,
    AgentDefinition,
    AgentRunRequest,
    AgentRunResponse,
    AgentSettings,
    AgentSettingsUpdate,
    AgentUpdateRequest,
)
from app.router.auth import authorize_protected_request

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agents", tags=["agents"])


def require_agents_access(
    request: Request,
    session: Session = Depends(get_session),
) -> None:
    authorize_protected_request(request, session, "/agents")


def _map_value_error(exc: ValueError) -> HTTPException:
    detail = str(exc)
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    if "existiert bereits" in detail:
        status_code = status.HTTP_409_CONFLICT
    elif "nicht gefunden" in detail:
        status_code = status.HTTP_404_NOT_FOUND
    elif "nicht gelöscht" in detail or "System-Agenten" in detail:
        status_code = status.HTTP_403_FORBIDDEN
    return HTTPException(status_code=status_code, detail=detail)


@router.get("", response_model=list[AgentDefinition], dependencies=[Depends(require_agents_access)])
async def agents_list(session: Session = Depends(get_session)) -> list[AgentDefinition]:
    return attach_agent_activity(list_agents(), session)


@router.get(
    "/{agent_name}",
    response_model=AgentDefinition,
    dependencies=[Depends(require_agents_access)],
)
async def agent_detail(
    agent_name: str,
    session: Session = Depends(get_session),
) -> AgentDefinition:
    agent = get_agent(agent_name)
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent nicht gefunden")
    return attach_agent_activity([agent], session)[0]


@router.get(
    "/{agent_name}/settings",
    response_model=AgentSettings,
    dependencies=[Depends(require_agents_access)],
)
async def agent_settings(agent_name: str) -> AgentSettings:
    agent = get_agent(agent_name)
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent nicht gefunden")
    return agent.settings


@router.post(
    "",
    response_model=AgentDefinition,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_agents_access)],
)
async def agent_create(payload: AgentCreateRequest) -> AgentDefinition:
    try:
        return create_agent(payload)
    except ValueError as exc:
        raise _map_value_error(exc) from exc


@router.put(
    "/{agent_name}",
    response_model=AgentDefinition,
    dependencies=[Depends(require_agents_access)],
)
async def agent_update(agent_name: str, payload: AgentUpdateRequest) -> AgentDefinition:
    try:
        return update_agent(agent_name, payload)
    except ValueError as exc:
        raise _map_value_error(exc) from exc


@router.put(
    "/{agent_name}/settings",
    response_model=AgentDefinition,
    dependencies=[Depends(require_agents_access)],
)
async def agent_update_settings(
    agent_name: str,
    payload: AgentSettingsUpdate,
) -> AgentDefinition:
    try:
        return update_agent_settings(agent_name, payload)
    except ValueError as exc:
        raise _map_value_error(exc) from exc


@router.post(
    "/{agent_name}/enable",
    response_model=AgentDefinition,
    dependencies=[Depends(require_agents_access)],
)
async def agent_enable(agent_name: str) -> AgentDefinition:
    try:
        return enable_agent(agent_name)
    except ValueError as exc:
        raise _map_value_error(exc) from exc


@router.post(
    "/{agent_name}/disable",
    response_model=AgentDefinition,
    dependencies=[Depends(require_agents_access)],
)
async def agent_disable(agent_name: str) -> AgentDefinition:
    try:
        return disable_agent(agent_name)
    except ValueError as exc:
        raise _map_value_error(exc) from exc


@router.delete(
    "/{agent_name}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_agents_access)],
)
async def agent_delete(agent_name: str) -> Response:
    try:
        delete_agent(agent_name)
    except ValueError as exc:
        raise _map_value_error(exc) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/run",
    response_model=AgentRunResponse,
    dependencies=[Depends(require_agents_access)],
)
async def agent_run(payload: AgentRunRequest) -> AgentRunResponse:
    try:
        return await run_agent(payload)
    except Exception as exc:
        logger.exception("agent_run endpoint failed")
        return AgentRunResponse(
            agent_name=payload.agent_name,
            success=False,
            final_answer="",
            errors=[f"Agent-Run fehlgeschlagen: {exc}"],
            used_model=payload.preferred_model,
        )
