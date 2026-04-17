from __future__ import annotations

import json
from collections.abc import Iterable
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.actions.registry import get_action
from app.models.action_models import ActionProposal
from app.models.agent_models import ToolCall
from app.models.skill_models import SkillCall
from app.skills.registry import get_skill
from app.tools.registry import get_tool


class CallParseResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    call_type: Literal["tool", "skill", "action"] | None = None
    tool_call: ToolCall | None = None
    skill_call: SkillCall | None = None
    action_proposal: ActionProposal | None = None
    error: str | None = None
    raw_payload: dict[str, Any] | None = None


class ToolCallEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tool_name: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    reason: str


class SkillCallEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid")

    skill_name: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    reason: str


class ActionProposalEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action_name: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    reason: str
    target: str | None = None
    requires_approval: bool = True


def _strip_code_fences(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if len(lines) >= 2 and lines[-1].strip().startswith("```"):
            return "\n".join(lines[1:-1]).strip()
    return stripped


def _extract_json_candidate(text: str) -> dict[str, Any] | None:
    candidate = _strip_code_fences(text)
    if not candidate:
        return None

    decoder = json.JSONDecoder()
    start = candidate.find("{")
    if start < 0:
        return None
    try:
        obj, _ = decoder.raw_decode(candidate[start:])
    except json.JSONDecodeError:
        return None
    if isinstance(obj, dict):
        return obj
    return None


def _validate_registered_name(name: str, *, names: Iterable[str], kind: str) -> str | None:
    normalized = name.strip()
    if not normalized:
        return f"{kind} darf nicht leer sein"
    if normalized not in names:
        return f"Unbekanntes {kind}: {normalized}"
    return None


def parse_tool_call(text: str, *, allowed_tools: Iterable[str]) -> CallParseResult:
    candidate = _extract_json_candidate(text)
    if candidate is None or "tool_name" not in candidate:
        return CallParseResult()

    try:
        envelope = ToolCallEnvelope.model_validate(candidate)
    except ValidationError as exc:
        return CallParseResult(
            error=f"Ungültiges Tool-Call-Format: {exc.errors()}",
            raw_payload=candidate,
        )

    tool_name = envelope.tool_name.strip()
    if tool_name not in allowed_tools:
        return CallParseResult(
            error=f"Tool nicht für diesen Agenten erlaubt: {tool_name}",
            raw_payload=candidate,
        )

    if get_tool(tool_name) is None:
        return CallParseResult(
            error=f"Unregistriertes Tool: {tool_name}",
            raw_payload=candidate,
        )

    try:
        tool_call = ToolCall(
            tool_name=tool_name,
            arguments=envelope.arguments or {},
            reason=envelope.reason,
        )
    except ValidationError as exc:
        return CallParseResult(
            error=f"Tool-Call konnte nicht validiert werden: {exc.errors()}",
            raw_payload=candidate,
        )

    return CallParseResult(call_type="tool", tool_call=tool_call, raw_payload=candidate)


def parse_skill_call(text: str, *, allowed_skills: Iterable[str]) -> CallParseResult:
    candidate = _extract_json_candidate(text)
    if candidate is None or "skill_name" not in candidate:
        return CallParseResult()

    try:
        envelope = SkillCallEnvelope.model_validate(candidate)
    except ValidationError as exc:
        return CallParseResult(
            error=f"Ungültiges Skill-Call-Format: {exc.errors()}",
            raw_payload=candidate,
        )

    skill_name = envelope.skill_name.strip()
    if skill_name not in allowed_skills:
        return CallParseResult(
            error=f"Skill nicht für diesen Agenten erlaubt: {skill_name}",
            raw_payload=candidate,
        )
    if get_skill(skill_name) is None:
        return CallParseResult(
            error=f"Unregistrierter Skill: {skill_name}",
            raw_payload=candidate,
        )

    try:
        skill_call = SkillCall(
            skill_name=skill_name,
            arguments=envelope.arguments or {},
            reason=envelope.reason,
        )
    except ValidationError as exc:
        return CallParseResult(
            error=f"Skill-Call konnte nicht validiert werden: {exc.errors()}",
            raw_payload=candidate,
        )

    return CallParseResult(call_type="skill", skill_call=skill_call, raw_payload=candidate)


def parse_action_proposal(text: str, *, allowed_actions: Iterable[str]) -> CallParseResult:
    candidate = _extract_json_candidate(text)
    if candidate is None or "action_name" not in candidate:
        return CallParseResult()

    try:
        envelope = ActionProposalEnvelope.model_validate(candidate)
    except ValidationError as exc:
        return CallParseResult(
            error=f"Ungültiges Action-Format: {exc.errors()}",
            raw_payload=candidate,
        )

    action_name = envelope.action_name.strip()
    if action_name not in allowed_actions:
        return CallParseResult(
            error=f"Action nicht für diesen Agenten erlaubt: {action_name}",
            raw_payload=candidate,
        )
    if get_action(action_name) is None:
        return CallParseResult(
            error=f"Unregistrierte Action: {action_name}",
            raw_payload=candidate,
        )

    try:
        action_proposal = ActionProposal(
            action_name=action_name,
            arguments=envelope.arguments or {},
            reason=envelope.reason,
            target=envelope.target,
            requires_approval=envelope.requires_approval,
        )
    except ValidationError as exc:
        return CallParseResult(
            error=f"Action-Proposal konnte nicht validiert werden: {exc.errors()}",
            raw_payload=candidate,
        )

    return CallParseResult(call_type="action", action_proposal=action_proposal, raw_payload=candidate)
