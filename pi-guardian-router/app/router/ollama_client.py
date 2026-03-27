import httpx


OLLAMA_BASE_URL = "http://127.0.0.1:11434"
OLLAMA_GENERATE_ENDPOINT = f"{OLLAMA_BASE_URL}/api/generate"


async def generate_with_ollama(model: str, prompt: str, stream: bool = False) -> dict:
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": stream,
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(OLLAMA_GENERATE_ENDPOINT, json=payload)
        response.raise_for_status()
        return response.json()
