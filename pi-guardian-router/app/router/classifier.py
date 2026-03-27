from app.schemas.request_models import RouteRequest


DEFAULT_MODEL = "qwen2.5-coder:1.5b"
LARGE_MODEL = "qwen2.5-coder:3b"


def select_model(request: RouteRequest) -> str:
    if request.preferred_model:
        return request.preferred_model

    prompt_lower = request.prompt.lower()

    if any(keyword in prompt_lower for keyword in ["architektur", "refactor", "analyse", "debug", "komplex"]):
        return LARGE_MODEL

    return DEFAULT_MODEL
