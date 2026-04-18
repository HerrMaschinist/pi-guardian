from __future__ import annotations

from app.router.decision.classifier import classify_request
from app.router.decision.models import RequestDecision
from app.schemas.request_models import RouteRequest


def decide_route_request(request: RouteRequest) -> RequestDecision:
    return classify_request(request)
