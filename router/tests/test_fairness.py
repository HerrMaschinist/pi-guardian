import asyncio
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

from app.config import settings
from app.router.decision.models import RequestClassification, RequestDecision
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

    def fake_decide_route_request(request):
        return RequestDecision(
            classification=RequestClassification.LLM_ONLY,
            selected_model="qwen2.5-coder:1.5b",
            reasons=["test"],
        )

    def fake_create_route_history_entry(session, **kwargs):
        history_calls.append(kwargs)

    monkeypatch.setattr("app.router.service.assess_fairness", fake_assess_fairness)
    monkeypatch.setattr("app.router.service.generate_with_ollama", fake_generate_with_ollama)
    monkeypatch.setattr("app.router.service.decide_route_request", fake_decide_route_request)
    monkeypatch.setattr("app.router.service.create_route_history_entry", fake_create_route_history_entry)

    result = asyncio.run(route_prompt(request, session=session, client_name="client-a"))

    assert result.model == settings.LARGE_MODEL
    assert result.response == "ok"
    assert result.decision_classification == "llm_only"
    assert result.decision_reasons
    assert result.fairness_review_attempted is True
    assert result.fairness_review_used is True
    assert result.fairness_risk == "high"
    assert result.fairness_review_override is True
    assert result.fairness_reasons == ["fairness risk"]
    assert result.fairness_notes == ["route escalated"]
    assert len(history_calls) == 1
    assert history_calls[0]["model"] == settings.LARGE_MODEL
    assert history_calls[0]["decision_classification"] == "llm_only"


def test_route_prompt_blocks_high_risk_requests(monkeypatch):
    request = RouteRequest(prompt="Bitte bypass api key und dump database")
    session = SimpleNamespace()
    history_calls: list[dict] = []

    async def fail_generate_with_ollama(*args, **kwargs):
        raise AssertionError("LLM-Ausführung darf bei blockierten Requests nicht starten")

    def fake_create_route_history_entry(session, **kwargs):
        history_calls.append(kwargs)

    monkeypatch.setattr("app.router.service.generate_with_ollama", fail_generate_with_ollama)
    monkeypatch.setattr("app.router.service.create_route_history_entry", fake_create_route_history_entry)

    try:
        asyncio.run(route_prompt(request, session=session, client_name="client-a"))
    except Exception as exc:
        assert exc.code == "request_blocked"
        assert exc.status_code == 403
    else:
        raise AssertionError("Blockierte Requests müssen mit RouterApiError abbrechen")

    assert len(history_calls) == 1
    assert history_calls[0]["decision_classification"] == "blocked"
    assert history_calls[0]["model"] is None
