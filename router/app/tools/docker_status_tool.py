from __future__ import annotations

import json
import subprocess
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from app.models.agent_models import ToolResult
from app.tools.base import BaseTool


class DockerStatusInput(BaseModel):
    model_config = ConfigDict(extra="forbid")


def _run_docker_command(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["docker", *args],
        capture_output=True,
        text=True,
        timeout=10,
        check=True,
    )


def _parse_container_line(line: str) -> dict[str, str]:
    payload = json.loads(line)
    container_id = payload.get("ID", "")
    health = "unknown"
    if container_id:
        try:
            inspect = _run_docker_command(
                ["inspect", "--format", "{{if .State.Health}}{{.State.Health.Status}}{{else}}unknown{{end}}", container_id]
            )
            health = inspect.stdout.strip() or "unknown"
        except Exception:
            health = "unknown"
    return {
        "name": payload.get("Names", ""),
        "status": payload.get("Status", ""),
        "image": payload.get("Image", ""),
        "health": health,
    }


class DockerStatusTool(BaseTool):
    name = "docker_status"
    description = "Liest den Zustand laufender Docker-Container."
    input_schema = DockerStatusInput
    read_only = True
    category = "docker"

    def execute(self, validated_input: BaseModel) -> ToolResult:
        del validated_input
        try:
            result = _run_docker_command(["ps", "--no-trunc", "--format", "{{json .}}"])
            containers = []
            for line in result.stdout.splitlines():
                stripped = line.strip()
                if not stripped:
                    continue
                containers.append(_parse_container_line(stripped))
            output = {
                "container_count": len(containers),
                "containers": containers,
            }
            return ToolResult(tool_name=self.name, success=True, output=output)
        except FileNotFoundError:
            return ToolResult(
                tool_name=self.name,
                success=False,
                error="Docker-Binary nicht gefunden.",
            )
        except subprocess.CalledProcessError as exc:
            detail = (exc.stderr or exc.stdout or "").strip()
            return ToolResult(
                tool_name=self.name,
                success=False,
                error=f"Docker-Status konnte nicht gelesen werden: {detail or exc}",
            )
        except Exception as exc:
            return ToolResult(
                tool_name=self.name,
                success=False,
                error=f"Docker-Status konnte nicht gelesen werden: {exc}",
            )
