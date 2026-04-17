from __future__ import annotations

import subprocess
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.models.agent_models import ToolResult
from app.router.system_status import get_service_status
from app.tools.base import BaseTool


SAFE_SERVICE_NAMES = ("pi-guardian-router", "ollama", "docker")


class ServiceStatusInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    service_name: Literal["pi-guardian-router", "ollama", "docker"] = Field(
        ...,
        description="Sicherer, vordefinierter Service-Name",
    )


def _inspect_service(service_name: str) -> dict[str, object]:
    result = subprocess.run(
        [
            "systemctl",
            "show",
            service_name,
            "--property=ActiveState,SubState,MainPID,UnitFileState,FragmentPath,Description",
        ],
        capture_output=True,
        text=True,
        timeout=8,
        check=True,
    )
    properties: dict[str, str] = {}
    for line in result.stdout.splitlines():
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        properties[key.strip()] = value.strip()

    main_pid = properties.get("MainPID", "0")
    try:
        parsed_pid = int(main_pid)
    except ValueError:
        parsed_pid = 0

    return {
        "service_name": service_name,
        "active_state": properties.get("ActiveState", "unknown"),
        "sub_state": properties.get("SubState", "unknown"),
        "main_pid": parsed_pid if parsed_pid > 0 else None,
        "unit_file_state": properties.get("UnitFileState", "unknown"),
        "fragment_path": properties.get("FragmentPath", ""),
        "description": properties.get("Description", ""),
    }


class ServiceStatusTool(BaseTool):
    name = "service_status"
    description = "Prüft den Status eines sicheren, vordefinierten systemd-Dienstes."
    input_schema = ServiceStatusInput
    read_only = True
    category = "services"

    def execute(self, validated_input: BaseModel) -> ToolResult:
        service_name = getattr(validated_input, "service_name")
        if service_name == "pi-guardian-router":
            base = get_service_status()
            try:
                details = _inspect_service(service_name)
            except FileNotFoundError:
                return ToolResult(
                    tool_name=self.name,
                    success=False,
                    error="systemctl nicht gefunden.",
                )
            except subprocess.CalledProcessError as exc:
                detail = (exc.stderr or exc.stdout or "").strip()
                return ToolResult(
                    tool_name=self.name,
                    success=False,
                    error=f"Service-Status konnte nicht gelesen werden: {detail or exc}",
                )
            except Exception as exc:
                return ToolResult(
                    tool_name=self.name,
                    success=False,
                    error=f"Service-Status konnte nicht gelesen werden: {exc}",
                )
            output = {**details, **base}
            return ToolResult(tool_name=self.name, success=True, output=output)

        try:
            output = _inspect_service(service_name)
            output["active"] = output.get("active_state") == "active"
            return ToolResult(tool_name=self.name, success=True, output=output)
        except FileNotFoundError:
            return ToolResult(
                tool_name=self.name,
                success=False,
                error="systemctl nicht gefunden.",
            )
        except subprocess.CalledProcessError as exc:
            detail = (exc.stderr or exc.stdout or "").strip()
            return ToolResult(
                tool_name=self.name,
                success=False,
                error=f"Service-Status konnte nicht gelesen werden: {detail or exc}",
            )
        except Exception as exc:
            return ToolResult(
                tool_name=self.name,
                success=False,
                error=f"Service-Status konnte nicht gelesen werden: {exc}",
            )
