import asyncio
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

from app.config import settings
from app.router.fairness import FairnessReviewResult, assess_fairness
from app.router.service import route_prompt
from app.schemas.request_models import RouteRequest


def test_assess_fairness_parses_risk_and_override(monkeypatch):
    async def fake_generate_with_ollama(model, prompt, request_id, stream=False):
        return {
            "response": json.dumps(
                {
                    "fairness_risk": "high",
                    "override_to_large": True,
                    "reasons": ["sensible Anfrage"],
                    "notes": ["Large-Modell erzwingen"],
                }
            )
        }

    monkeypatch.setattr("app.router.fairness.generate_with_ollama", fake_generate_with_ollama)

    result = asyncio.run(
        assess_fairness(
            prompt="Bitte prüfe Fairness",
            selected_model="qwen2.5-coder:1.5b",
            request_id="req-1",
        )
    )

    assert result.attempted is True
    assert result.used is True
    assert result.risk == "high"
    assert result.override_to_large is True
    assert result.threshold in {"low", "medium", "high"}
    assert result.reasons == ["sensible Anfrage"]
    assert result.notes == ["Large-Modell erzwingen"]


def test_route_prompt_uses_fairness_override(monkeypatch):
    request = RouteRequest(prompt="Bitte antworte kurz")
    session = SimpleNamespace()
    history_calls: list[dict] = []

    async def fake_assess_fairness(prompt, selected_model, request_id):
        return FairnessReviewResult(
            attempted=True,
            used=True,
            risk="high",
            override_to_large=True,
            threshold="medium",
            reasons=["fairness risk"],
            notes=["route escalated"],
        )

    async def fake_generate_with_ollama(model, prompt, request_id, stream=False):
        return {
            "model": model,
            "response": "ok",
            "done": True,
            "done_reason": "stop",
        }

    def fake_select_model(request):
        return "qwen2.5-coder:1.5b"

    def fake_create_route_history_entry(session, **kwargs):
        history_calls.append(kwargs)

    monkeypatch.setattr("app.router.service.assess_fairness", fake_assess_fairness)
    monkeypatch.setattr("app.router.service.generate_with_ollama", fake_generate_with_ollama)
    monkeypatch.setattr("app.router.service.select_model", fake_select_model)
    monkeypatch.setattr("app.router.service.create_route_history_entry", fake_create_route_history_entry)

    result = asyncio.run(route_prompt(request, session=session, client_name="client-a"))

    assert result.model == settings.LARGE_MODEL
    assert result.response == "ok"
    assert result.fairness_review_attempted is True
    assert result.fairness_review_used is True
    assert result.fairness_risk == "high"
    assert result.fairness_review_override is True
    assert result.fairness_reasons == ["fairness risk"]
    assert result.fairness_notes == ["route escalated"]
    assert len(history_calls) == 1
    assert history_calls[0]["model"] == settings.LARGE_MODEL
