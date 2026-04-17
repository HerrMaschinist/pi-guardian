from __future__ import annotations

import logging
import time
from typing import Any

from pydantic import ValidationError

from app.actions.registry import get_action
from app.models.action_models import ActionExecutionContext, ActionProposal, ActionResult
from app.models.agent_models import AgentPolicySettings

logger = logging.getLogger(__name__)


class ActionExecutor:
    def __init__(self, timeout_seconds: float = 20.0) -> None:
        self.timeout_seconds = timeout_seconds

    def _policy_denies_action(self, action_name: str, policy: AgentPolicySettings) -> str | None:
        if not policy.allowed_actions:
            return f"Action nicht für Agent freigegeben: {action_name}"
        if action_name not in policy.allowed_actions:
            return f"Action nicht für Agent freigegeben: {action_name}"
        return None

    @staticmethod
    def _validate_target(action_name: str, target: str | None, allowed_targets: list[str]) -> str | None:
        if target is None:
            return None
        if allowed_targets and target not in allowed_targets:
            return f"Ziel ist für diese Action nicht erlaubt: {target}"
        return None

    def propose(self, proposal: ActionProposal, *, policy: AgentPolicySettings) -> ActionProposal:
        if not policy.can_propose_actions:
            raise ValueError("Agent darf keine Actions vorschlagen")
        if proposal.action_name not in policy.allowed_actions:
            raise ValueError(f"Action nicht für Agent freigegeben: {proposal.action_name}")
        action = get_action(proposal.action_name)
        if action is None:
            raise ValueError(f"Unbekannte Action: {proposal.action_name}")
        if not action.enabled:
            raise ValueError(f"Action ist derzeit deaktiviert: {proposal.action_name}")
        if not action.requires_approval:
            raise ValueError(
                f"Action benötigt keine Freigabe und darf nicht über diesen Pfad vorgeschlagen werden: {proposal.action_name}"
            )
        target_error = self._validate_target(proposal.action_name, proposal.target, list(action.allowed_targets))
        if target_error is not None:
            raise ValueError(target_error)
        return proposal.model_copy(update={"requires_approval": True})

    def execute(
        self,
        proposal: ActionProposal,
        *,
        policy: AgentPolicySettings,
        approved: bool,
        context: ActionExecutionContext,
    ) -> ActionResult:
        start = time.perf_counter()
        logger.info(
            "action_call_start agent=%s action=%s approved=%s target=%s",
            context.agent_name,
            proposal.action_name,
            approved,
            proposal.target,
        )

        if not approved:
            error = "Action wurde nicht freigegeben."
            logger.warning(
                "action_call_rejected agent=%s action=%s",
                context.agent_name,
                proposal.action_name,
            )
            return ActionResult(action_name=proposal.action_name, success=False, error=error)

        policy_error = self._policy_denies_action(proposal.action_name, policy)
        if policy_error is not None:
            logger.warning(
                "action_call_policy_denied agent=%s action=%s",
                context.agent_name,
                proposal.action_name,
            )
            return ActionResult(action_name=proposal.action_name, success=False, error=policy_error)

        action = get_action(proposal.action_name)
        if action is None:
            error = f"Unbekannte Action: {proposal.action_name}"
            return ActionResult(action_name=proposal.action_name, success=False, error=error)
        if not action.enabled:
            error = f"Action ist derzeit deaktiviert: {proposal.action_name}"
            return ActionResult(action_name=proposal.action_name, success=False, error=error)
        if not action.requires_approval:
            error = f"Action benötigt keine Freigabe und darf nicht über diesen Pfad ausgeführt werden: {proposal.action_name}"
            return ActionResult(action_name=proposal.action_name, success=False, error=error)
        target_error = self._validate_target(proposal.action_name, proposal.target, list(action.allowed_targets))
        if target_error is not None:
            return ActionResult(action_name=proposal.action_name, success=False, error=target_error)

        try:
            validated_input = action.validate_arguments(proposal.arguments)
        except ValidationError as exc:
            error = f"Ungültige Action-Argumente für {proposal.action_name}: {exc.errors()}"
            return ActionResult(action_name=proposal.action_name, success=False, error=error)
        except Exception as exc:
            return ActionResult(action_name=proposal.action_name, success=False, error=f"Action-Argumente konnten nicht validiert werden: {exc}")

        try:
            result = action.execute(validated_input)
        except Exception as exc:
            logger.exception("action_call_failed agent=%s action=%s", context.agent_name, proposal.action_name)
            return ActionResult(action_name=proposal.action_name, success=False, error=f"Action-Ausführung fehlgeschlagen: {exc}")

        duration_ms = int((time.perf_counter() - start) * 1000)
        logger.info(
            "action_call_end agent=%s action=%s success=%s duration_ms=%s",
            context.agent_name,
            proposal.action_name,
            result.success,
            duration_ms,
        )
        return result


executor = ActionExecutor()
