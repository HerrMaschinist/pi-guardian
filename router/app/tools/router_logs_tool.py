from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.agent_models import ToolResult
from app.router.log_reader import read_logs
from app.tools.base import BaseTool


class RouterLogsInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    limit: int = Field(default=20, ge=1, le=50)
    level: Literal["info", "warn", "error"] | None = None
    source_contains: str | None = Field(default=None, max_length=64)
    message_contains: str | None = Field(default=None, max_length=128)

    @field_validator("source_contains", "message_contains")
    @classmethod
    def _strip_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None


class RouterLogsTool(BaseTool):
    name = "router_logs"
    description = (
        "Liest eine begrenzte, sichere Auswahl aktueller Router-Logs aus dem "
        "lokalen router.log."
    )
    input_schema = RouterLogsInput
    read_only = True
    category = "logs"

    def execute(self, validated_input: BaseModel) -> ToolResult:
        limit = getattr(validated_input, "limit", 20)
        level = getattr(validated_input, "level", None)
        source_contains = (getattr(validated_input, "source_contains", None) or "").lower()
        message_contains = (getattr(validated_input, "message_contains", None) or "").lower()

        try:
            raw_entries = read_logs(limit=min(max(limit * 4, limit), 100))
            entries = []
            for entry in raw_entries:
                entry_level = str(entry.get("level", "")).lower()
                source = str(entry.get("source", "")).lower()
                message = str(entry.get("message", "")).lower()

                if level and entry_level != level:
                    continue
                if source_contains and source_contains not in source:
                    continue
                if message_contains and message_contains not in message:
                    continue

                entries.append(entry)
                if len(entries) >= limit:
                    break

            output = {
                "source": "router.log",
                "requested_limit": limit,
                "returned_count": len(entries),
                "filters": {
                    "level": level,
                    "source_contains": getattr(validated_input, "source_contains", None),
                    "message_contains": getattr(validated_input, "message_contains", None),
                },
                "entries": entries,
            }
            return ToolResult(tool_name=self.name, success=True, output=output)
        except Exception as exc:
            return ToolResult(
                tool_name=self.name,
                success=False,
                error=f"Router-Logs konnten nicht gelesen werden: {exc}",
            )
