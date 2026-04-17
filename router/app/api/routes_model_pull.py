from fastapi import APIRouter, Depends, Query, Request
from sqlmodel import Session

from app.database import get_session
from app.models.model_pull import ModelPullCreate, ModelPullRead
from app.router.auth import authorize_protected_request
from app.router.model_pull import create_model_pull_job, get_model_pull_job, list_model_pull_jobs

router = APIRouter(prefix="/models/pull", tags=["model-pull"])


def require_model_pull_access(
    request: Request,
    session: Session = Depends(get_session),
) -> None:
    authorize_protected_request(request, session, "/models/pull")


@router.get("", response_model=list[ModelPullRead], dependencies=[Depends(require_model_pull_access)])
async def get_pull_jobs(
    limit: int = Query(default=10, ge=1, le=50),
    session: Session = Depends(get_session),
) -> list[ModelPullRead]:
    return list_model_pull_jobs(session, limit=limit)


@router.get("/{job_id}", response_model=ModelPullRead, dependencies=[Depends(require_model_pull_access)])
async def get_pull_job(
    job_id: int,
    session: Session = Depends(get_session),
) -> ModelPullRead:
    return get_model_pull_job(session, job_id)


@router.post("", response_model=ModelPullRead, status_code=201, dependencies=[Depends(require_model_pull_access)])
async def post_pull_job(
    payload: ModelPullCreate,
    request: Request,
    session: Session = Depends(get_session),
) -> ModelPullRead:
    requested_by = authorize_protected_request(request, session, "/models/pull")
    return create_model_pull_job(session, payload, requested_by=requested_by)
