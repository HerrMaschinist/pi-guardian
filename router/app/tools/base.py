from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, ClassVar

from pydantic import BaseModel

from app.models.agent_models import ToolResult


class BaseTool(ABC):
    name: ClassVar[str]
    description: ClassVar[str]
    input_schema: ClassVar[type[BaseModel]]
    read_only: ClassVar[bool] = True
    category: ClassVar[str] = "generic"

    def validate_arguments(self, arguments: dict[str, Any] | None) -> BaseModel:
        payload = arguments or {}
        return self.input_schema.model_validate(payload)

    @abstractmethod
    def execute(self, validated_input: BaseModel) -> ToolResult:
        raise NotImplementedError
