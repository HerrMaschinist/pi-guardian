from __future__ import annotations

from dataclasses import dataclass

from app.router.decision.models import RequestClassification, RequestDecision


@dataclass(frozen=True)
class ClientPolicyContext:
    can_use_llm: bool = True
    can_use_tools: bool = False
    can_use_internet: bool = False


def apply_client_policy(
    decision: RequestDecision,
    policy: ClientPolicyContext | None,
) -> RequestDecision:
    if policy is None or decision.blocked:
        return decision

    if (
        decision.classification is RequestClassification.LLM_ONLY
        and not policy.can_use_llm
    ):
        return RequestDecision(
            classification=RequestClassification.BLOCKED,
            selected_model=None,
            blocked=True,
            reasons=[
                *decision.reasons,
                "Client-Policy erlaubt keine reine LLM-Nutzung",
            ],
        )

    if (
        decision.classification is RequestClassification.TOOL_REQUIRED
        and not policy.can_use_tools
    ):
        return RequestDecision(
            classification=RequestClassification.BLOCKED,
            selected_model=None,
            blocked=True,
            reasons=[
                *decision.reasons,
                "Client-Policy erlaubt keine Tool-Nutzung",
            ],
            tool_hints=decision.tool_hints,
        )

    if (
        decision.classification is RequestClassification.INTERNET_REQUIRED
        and not policy.can_use_internet
    ):
        return RequestDecision(
            classification=RequestClassification.BLOCKED,
            selected_model=None,
            blocked=True,
            reasons=[
                *decision.reasons,
                "Client-Policy erlaubt keinen Internet-Zugriff",
            ],
            internet_hints=decision.internet_hints,
        )

    return decision
