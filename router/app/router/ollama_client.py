import logging

import httpx

from app.config import settings
from app.router.errors import RouterApiError

logger = logging.getLogger(__name__)


async def generate_with_ollama(
    model: str,
    prompt: str,
    request_id: str,
    stream: bool = False,
) -> dict:
    url = f"{settings.OLLAMA_BASE_URL}/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": stream,
    }

    try:
        async with httpx.AsyncClient(timeout=float(settings.REQUEST_TIMEOUT)) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            return response.json()
    except httpx.TimeoutException as exc:
        logger.warning("Ollama timeout: model=%s path=%s", model, url)
        raise RouterApiError(
            message=f"Ollama hat nicht innerhalb von {settings.REQUEST_TIMEOUT}s geantwortet.",
            status_code=504,
            code="ollama_timeout",
            request_id=request_id,
            model=model,
            retryable=True,
        ) from exc
    except httpx.ConnectError as exc:
        raise RouterApiError(
            message="Ollama ist nicht erreichbar.",
            status_code=502,
            code="ollama_unreachable",
            request_id=request_id,
            model=model,
            retryable=True,
        ) from exc
    except httpx.HTTPStatusError as exc:
        detail = exc.response.text.strip() or exc.response.reason_phrase
        logger.warning(
            "Ollama HTTP error: status=%s model=%s detail=%s",
            exc.response.status_code,
            model,
            detail[:500],
        )
        raise RouterApiError(
            message=f"Ollama hat mit HTTP {exc.response.status_code} geantwortet.",
            status_code=502,
            code="ollama_http_error",
            request_id=request_id,
            model=model,
            retryable=500 <= exc.response.status_code < 600,
        ) from exc
    except Exception as exc:
        logger.warning("Unexpected Ollama error: model=%s error=%s", model, exc)
        raise RouterApiError(
            message="Unerwarteter Fehler bei der Ollama-Anfrage.",
            status_code=500,
            code="ollama_request_failed",
            request_id=request_id,
            model=model,
            retryable=False,
        ) from exc


async def post_to_ollama(
    path: str,
    payload: dict,
    request_id: str,
    model: str,
) -> dict:
    url = f"{settings.OLLAMA_BASE_URL}{path}"

    try:
        async with httpx.AsyncClient(timeout=float(settings.REQUEST_TIMEOUT)) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            return response.json()
    except httpx.TimeoutException as exc:
        logger.warning("Ollama timeout: model=%s path=%s", model, path)
        raise RouterApiError(
            message=f"Ollama hat nicht innerhalb von {settings.REQUEST_TIMEOUT}s geantwortet.",
            status_code=504,
            code="ollama_timeout",
            request_id=request_id,
            model=model,
            retryable=True,
        ) from exc
    except httpx.ConnectError as exc:
        logger.warning("Ollama unreachable: model=%s path=%s", model, path)
        raise RouterApiError(
            message="Ollama ist nicht erreichbar.",
            status_code=502,
            code="ollama_unreachable",
            request_id=request_id,
            model=model,
            retryable=True,
        ) from exc
    except httpx.HTTPStatusError as exc:
        detail = exc.response.text.strip() or exc.response.reason_phrase
        logger.warning(
            "Ollama HTTP error: status=%s model=%s path=%s detail=%s",
            exc.response.status_code,
            model,
            path,
            detail[:500],
        )
        raise RouterApiError(
            message=f"Ollama hat mit HTTP {exc.response.status_code} geantwortet.",
            status_code=502,
            code="ollama_http_error",
            request_id=request_id,
            model=model,
            retryable=500 <= exc.response.status_code < 600,
        ) from exc
    except Exception as exc:
        logger.warning("Unexpected Ollama error: model=%s path=%s error=%s", model, path, exc)
        raise RouterApiError(
            message="Unerwarteter Fehler bei der Ollama-Anfrage.",
            status_code=500,
            code="ollama_request_failed",
            request_id=request_id,
            model=model,
            retryable=False,
        ) from exc


def stream_to_ollama(
    path: str,
    payload: dict,
    request_id: str,
    model: str,
):
    url = f"{settings.OLLAMA_BASE_URL}{path}"

    async def iterator():
        try:
            async with httpx.AsyncClient(timeout=float(settings.REQUEST_TIMEOUT)) as client:
                async with client.stream("POST", url, json=payload) as response:
                    response.raise_for_status()
                    async for chunk in response.aiter_bytes():
                        yield chunk
        except httpx.TimeoutException as exc:
            logger.warning("Ollama stream timeout: model=%s path=%s", model, path)
            raise RouterApiError(
                message=f"Ollama hat nicht innerhalb von {settings.REQUEST_TIMEOUT}s geantwortet.",
                status_code=504,
                code="ollama_timeout",
                request_id=request_id,
                model=model,
                retryable=True,
            ) from exc
        except httpx.ConnectError as exc:
            logger.warning("Ollama stream unreachable: model=%s path=%s", model, path)
            raise RouterApiError(
                message="Ollama ist nicht erreichbar.",
                status_code=502,
                code="ollama_unreachable",
                request_id=request_id,
                model=model,
                retryable=True,
            ) from exc
        except httpx.HTTPStatusError as exc:
            detail = exc.response.text.strip() or exc.response.reason_phrase
            logger.warning(
                "Ollama stream HTTP error: status=%s model=%s path=%s detail=%s",
                exc.response.status_code,
                model,
                path,
                detail[:500],
            )
            raise RouterApiError(
                message=f"Ollama hat mit HTTP {exc.response.status_code} geantwortet.",
                status_code=502,
                code="ollama_http_error",
                request_id=request_id,
                model=model,
                retryable=500 <= exc.response.status_code < 600,
            ) from exc
        except Exception as exc:
            logger.warning("Unexpected Ollama stream error: model=%s path=%s error=%s", model, path, exc)
            raise RouterApiError(
                message="Unerwarteter Fehler bei der Ollama-Anfrage.",
                status_code=500,
                code="ollama_request_failed",
                request_id=request_id,
                model=model,
                retryable=False,
            ) from exc

    return iterator()
