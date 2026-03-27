import logging

import httpx
from fastapi import HTTPException

from app.config import settings

logger = logging.getLogger(__name__)


async def fetch_models() -> list[dict]:
    url = f"{settings.OLLAMA_BASE_URL}/api/tags"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
    except Exception as exc:
        logger.warning("ollama_models: Ollama nicht erreichbar: %s", exc)
        raise HTTPException(status_code=502, detail="Ollama nicht erreichbar")

    models = []
    for m in data.get("models", []):
        size_bytes = m.get("size", 0)
        size_str = f"{size_bytes / (1024 ** 2):.0f} MB" if size_bytes else "–"
        models.append({
            "name": m.get("name", ""),
            "size": size_str,
            "modified_at": m.get("modified_at", ""),
            "digest": m.get("digest", ""),
        })
    return models
