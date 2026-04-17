from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

from pydantic import ValidationError

from app.models.skill_models import SkillExecutionContext, SkillResult
from app.skills.registry import get_skill

logger = logging.getLogger(__name__)


class SkillExecutor:
    def __init__(self, timeout_seconds: float = 10.0) -> None:
        self.timeout_seconds = timeout_seconds

    async def execute(
        self,
        skill_name: str,
        arguments: dict[str, Any] | None,
        *,
        allowed_skills: list[str],
        context: SkillExecutionContext,
    ) -> SkillResult:
        start = time.perf_counter()
        logger.info(
            "skill_call_start agent=%s step=%s skill=%s",
            context.agent_name,
            context.step_number,
            skill_name,
        )

        if skill_name not in allowed_skills:
            error = f"Skill nicht für Agent freigegeben: {skill_name}"
            logger.warning(
                "skill_call_denied agent=%s step=%s skill=%s",
                context.agent_name,
                context.step_number,
                skill_name,
            )
            return SkillResult(skill_name=skill_name, success=False, error=error)

        skill = get_skill(skill_name)
        if skill is None:
            error = f"Unbekannter Skill: {skill_name}"
            logger.warning(
                "skill_call_unknown agent=%s step=%s skill=%s",
                context.agent_name,
                context.step_number,
                skill_name,
            )
            return SkillResult(skill_name=skill_name, success=False, error=error)

        try:
            validated_input = skill.validate_arguments(arguments)
        except ValidationError as exc:
            error = f"Ungültige Skill-Argumente für {skill_name}: {exc.errors()}"
            logger.warning(
                "skill_call_validation_failed agent=%s step=%s skill=%s error=%s",
                context.agent_name,
                context.step_number,
                skill_name,
                error,
            )
            return SkillResult(skill_name=skill_name, success=False, error=error)
        except Exception as exc:
            error = f"Skill-Argumente konnten nicht validiert werden: {exc}"
            logger.warning(
                "skill_call_validation_error agent=%s step=%s skill=%s error=%s",
                context.agent_name,
                context.step_number,
                skill_name,
                exc,
            )
            return SkillResult(skill_name=skill_name, success=False, error=error)

        try:
            result = await asyncio.wait_for(
                asyncio.to_thread(skill.execute, validated_input),
                timeout=self.timeout_seconds,
            )
        except asyncio.TimeoutError:
            error = f"Skill-Timeout nach {self.timeout_seconds:.1f}s: {skill_name}"
            logger.warning(
                "skill_call_timeout agent=%s step=%s skill=%s",
                context.agent_name,
                context.step_number,
                skill_name,
            )
            return SkillResult(skill_name=skill_name, success=False, error=error)
        except Exception as exc:
            error = f"Skill-Ausführung fehlgeschlagen: {exc}"
            logger.exception(
                "skill_call_failed agent=%s step=%s skill=%s",
                context.agent_name,
                context.step_number,
                skill_name,
            )
            return SkillResult(skill_name=skill_name, success=False, error=error)

        duration_ms = int((time.perf_counter() - start) * 1000)
        logger.info(
            "skill_call_end agent=%s step=%s skill=%s success=%s duration_ms=%s",
            context.agent_name,
            context.step_number,
            skill_name,
            result.success,
            duration_ms,
        )
        return result


executor = SkillExecutor()
