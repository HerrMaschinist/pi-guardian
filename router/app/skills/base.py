from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, ClassVar

from pydantic import BaseModel

from app.models.skill_models import SkillResult


class BaseSkill(ABC):
    name: ClassVar[str]
    description: ClassVar[str]
    allowed_tools: ClassVar[list[str]]
    input_schema: ClassVar[type[BaseModel]]
    output_schema: ClassVar[type[BaseModel]]
    read_only: ClassVar[bool] = True
    version: ClassVar[str] = "1.0"

    def validate_arguments(self, arguments: dict[str, Any] | None) -> BaseModel:
        payload = arguments or {}
        return self.input_schema.model_validate(payload)

    @abstractmethod
    def execute(self, validated_input: BaseModel) -> SkillResult:
        raise NotImplementedError
