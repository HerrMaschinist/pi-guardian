from fastapi import APIRouter, Depends, Request
from sqlmodel import Session

from app.database import get_session
from app.models.model_registry import ModelCreate, ModelRead, ModelUpdate
from app.router.auth import authorize_protected_request
from app.router.model_registry import (
    create_registered_model,
    delete_registered_model,
    list_model_registry,
    update_registered_model,
)

router = APIRouter(prefix="/models/registry", tags=["model-registry"])


def require_model_registry_access(
    request: Request,
    session: Session = Depends(get_session),
) -> None:
    authorize_protected_request(request, session, "/models/registry")


@router.get("", response_model=list[ModelRead], dependencies=[Depends(require_model_registry_access)])
async def get_model_registry(session: Session = Depends(get_session)) -> list[ModelRead]:
    return list_model_registry(session)


@router.post("", response_model=ModelRead, status_code=201, dependencies=[Depends(require_model_registry_access)])
async def post_model_registry(
    payload: ModelCreate,
    session: Session = Depends(get_session),
) -> ModelRead:
    return create_registered_model(session, payload)


@router.put("/{model_id}", response_model=ModelRead, dependencies=[Depends(require_model_registry_access)])
async def put_model_registry(
    model_id: int,
    payload: ModelUpdate,
    session: Session = Depends(get_session),
) -> ModelRead:
    return update_registered_model(session, model_id, payload)


@router.delete("/{model_id}", status_code=204, dependencies=[Depends(require_model_registry_access)])
async def delete_model_registry(
    model_id: int,
    session: Session = Depends(get_session),
) -> None:
    delete_registered_model(session, model_id)
