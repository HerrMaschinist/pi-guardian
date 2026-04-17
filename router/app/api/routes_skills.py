from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlmodel import Session

from app.agents.registry import get_agent
from app.database import get_session
from app.models.skill_models import SkillDefinition
from app.skills.registry import get_skill, list_skills
from app.router.auth import authorize_protected_request

router = APIRouter(prefix="/skills", tags=["skills"])


def require_skills_access(
    request: Request,
    session: Session = Depends(get_session),
) -> None:
    authorize_protected_request(request, session, "/skills")


def _skill_definition(skill) -> SkillDefinition:
    return SkillDefinition(
        name=skill.name,
        description=skill.description,
        allowed_tools=list(skill.allowed_tools),
        input_schema=skill.input_schema.model_json_schema(),
        output_schema=skill.output_schema.model_json_schema(),
        read_only=skill.read_only,
        version=skill.version,
        enabled=True,
    )


@router.get("", response_model=list[SkillDefinition], dependencies=[Depends(require_skills_access)])
async def skills_list() -> list[SkillDefinition]:
    return [_skill_definition(skill) for skill in list_skills()]


@router.get(
    "/{skill_name}",
    response_model=SkillDefinition,
    dependencies=[Depends(require_skills_access)],
)
async def skill_detail(skill_name: str) -> SkillDefinition:
    skill = get_skill(skill_name)
    if skill is None:
        raise HTTPException(status_code=404, detail="Skill nicht gefunden")
    return _skill_definition(skill)
