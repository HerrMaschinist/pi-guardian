from __future__ import annotations

import subprocess
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.actions.base import BaseAction
from app.actions.registry import register_action
from app.models.action_models import ActionResult
from app.router.system_status import get_service_status
from app.tools.system_status_tool import SystemStatusTool


class RestartServiceInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    service_name: Literal["pi-guardian-router", "ollama", "docker"]


class RestartServiceOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    service_name: str
    restarted: bool
    message: str


class RestartServiceAction(BaseAction):
    name = "restart_service"
    description = "Startet einen freigegebenen systemd-Dienst neu."
    allowed_targets = ["pi-guardian-router", "ollama", "docker"]
    input_schema = RestartServiceInput
    output_schema = RestartServiceOutput
    read_only = False
    requires_approval = True
    version = "1.0"
    enabled = True

    def execute(self, validated_input: BaseModel) -> ActionResult:
        service_name = getattr(validated_input, "service_name")
        try:
            subprocess.run(
                ["systemctl", "restart", service_name],
                capture_output=True,
                text=True,
                timeout=20,
                check=True,
            )
            output = RestartServiceOutput(
                service_name=service_name,
                restarted=True,
                message=f"Dienst {service_name} wurde neu gestartet.",
            )
            return ActionResult(action_name=self.name, success=True, output=output.model_dump(mode="json"))
        except FileNotFoundError:
            return ActionResult(action_name=self.name, success=False, error="systemctl nicht gefunden.")
        except subprocess.CalledProcessError as exc:
            detail = (exc.stderr or exc.stdout or "").strip()
            return ActionResult(action_name=self.name, success=False, error=f"Dienst konnte nicht neu gestartet werden: {detail or exc}")
        except Exception as exc:
            return ActionResult(action_name=self.name, success=False, error=f"Dienst-Neustart fehlgeschlagen: {exc}")


class RestartContainerInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    container_name: str = Field(default="", min_length=1, max_length=128)


class RestartContainerOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    container_name: str
    restarted: bool
    message: str


class RestartContainerAction(BaseAction):
    name = "restart_container"
    description = "Vorbereitete Container-Aktion, derzeit bewusst deaktiviert."
    allowed_targets = []
    input_schema = RestartContainerInput
    output_schema = RestartContainerOutput
    read_only = False
    requires_approval = True
    version = "1.0"
    enabled = False

    def execute(self, validated_input: BaseModel) -> ActionResult:
        del validated_input
        return ActionResult(
            action_name=self.name,
            success=False,
            error="restart_container ist vorbereitet, aber derzeit deaktiviert.",
        )


class RerunHealthCheckInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scope: Literal["router", "system", "combined"] = "combined"


class RerunHealthCheckOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scope: str
    router: dict[str, Any]
    system: dict[str, Any]
    healthy: bool


class RerunHealthCheckAction(BaseAction):
    name = "rerun_health_check"
    description = "Führt eine erneute interne Gesundheitsprüfung aus."
    allowed_targets = ["router", "system", "combined"]
    input_schema = RerunHealthCheckInput
    output_schema = RerunHealthCheckOutput
    read_only = False
    requires_approval = True
    version = "1.0"
    enabled = True

    def execute(self, validated_input: BaseModel) -> ActionResult:
        scope = getattr(validated_input, "scope")
        router_state = get_service_status()
        system_state = SystemStatusTool().execute(SystemStatusTool.input_schema.model_validate({}))
        healthy = bool(router_state.get("active")) and system_state.success
        output = RerunHealthCheckOutput(
            scope=scope,
            router=router_state,
            system=system_state.output or {},
            healthy=healthy,
        )
        return ActionResult(action_name=self.name, success=True, output=output.model_dump(mode="json"))


def register_standard_actions() -> None:
    for action in (
        RestartServiceAction(),
        RestartContainerAction(),
        RerunHealthCheckAction(),
    ):
        register_action(action)


register_standard_actions()
