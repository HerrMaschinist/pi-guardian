from app.router.classifier import select_model
from app.router.ollama_client import generate_with_ollama
from app.schemas.request_models import RouteRequest
from app.schemas.response_models import RouteResponse


async def route_prompt(request: RouteRequest) -> RouteResponse:
    selected_model = select_model(request)

    result = await generate_with_ollama(
        model=selected_model,
        prompt=request.prompt,
        stream=request.stream,
    )

    return RouteResponse(
        model=result.get("model", selected_model),
        response=result.get("response", ""),
        done=result.get("done", False),
        done_reason=result.get("done_reason"),
    )
