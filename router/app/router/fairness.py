import json
import logging
from dataclasses import dataclass

from app.config import settings
from app.router.ollama_client import generate_with_ollama

logger = logging.getLogger(__name__)


@dataclass
class FairnessReviewResult:
    attempted: bool
    used: bool
    risk: str
    override_to_large: bool
    threshold: str
    reasons: list[str]
    notes: list[str]


async def assess_fairness(
    prompt: str,
    selected_model: str,
    request_id: str,
) -> FairnessReviewResult:
    fairness_prompt = _build_fairness_prompt(prompt, selected_model)

    try:
        result = await generate_with_ollama(
            model=settings.LARGE_MODEL,
            prompt=fairness_prompt,
            request_id=request_id,
            stream=False,
        )
        parsed = _parse_fairness_response(result.get("response", ""))
    except Exception as exc:
        logger.warning("[%s] Fairness review failed: %s", request_id, exc)
        return FairnessReviewResult(
            attempted=True,
            used=False,
            risk="unknown",
            override_to_large=False,
            threshold=_normalize_threshold(settings.ESCALATION_THRESHOLD),
            reasons=[],
            notes=["Fairness review failed, default routing used"],
        )

    threshold = _normalize_threshold(settings.ESCALATION_THRESHOLD)
    override = parsed["override_to_large"] or _risk_at_or_above_threshold(
        parsed["risk"], threshold
    )

    return FairnessReviewResult(
        attempted=True,
        used=True,
        risk=parsed["risk"],
        override_to_large=override,
        threshold=threshold,
        reasons=parsed["reasons"],
        notes=parsed["notes"],
    )


def _build_fairness_prompt(prompt: str, selected_model: str) -> str:
    return "\n".join(
        [
            "You are a fairness and bias reviewer before inference.",
            "Assess the request before the final model call.",
            "Answer only with JSON.",
            "Schema:",
            '{"fairness_risk":"low|medium|high", "override_to_large":true|false, "reasons":["..."], "notes":["..."]}',
            f"selected_model={selected_model}",
            f"escalation_threshold={settings.ESCALATION_THRESHOLD}",
            f"prompt={prompt}",
            (
                "Goal: detect one-sided, discriminatory, personal-data, or otherwise "
                "fairness-sensitive requests early. If risk is present, set override_to_large=true."
            ),
        ]
    )


def _parse_fairness_response(raw: str) -> dict[str, object]:
    if not raw or not raw.strip():
        raise ValueError("Empty fairness response")

    data = json.loads(raw.strip())
    if not isinstance(data, dict):
        raise ValueError("Fairness response must be a JSON object")

    risk = str(data.get("fairness_risk", "unknown")).lower()
    if risk not in {"low", "medium", "high"}:
        risk = "unknown"

    return {
        "risk": risk,
        "override_to_large": bool(data.get("override_to_large", False)),
        "reasons": _string_list(data.get("reasons")),
        "notes": _string_list(data.get("notes")),
    }


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item.strip() for item in value if isinstance(item, str) and item.strip()]


def _normalize_threshold(value: str) -> str:
    normalized = value.strip().lower()
    return normalized if normalized in {"low", "medium", "high"} else "medium"


def _risk_at_or_above_threshold(risk: str, threshold: str) -> bool:
    levels = {"low": 1, "medium": 2, "high": 3}
    if risk not in levels or threshold not in levels:
        return False
    return levels[risk] >= levels[threshold]
