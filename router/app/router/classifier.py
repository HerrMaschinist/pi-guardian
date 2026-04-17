from app.config import settings
from app.schemas.request_models import RouteRequest


def select_model_for_prompt(prompt: str) -> str:
    prompt_lower = prompt.lower()
    if any(keyword in prompt_lower for keyword in ["architektur", "refactor", "analyse", "debug", "komplex"]):
        return settings.LARGE_MODEL

    return settings.DEFAULT_MODEL


def select_model(request: RouteRequest) -> str:
    if request.preferred_model:
        return request.preferred_model
    return select_model_for_prompt(request.prompt)
