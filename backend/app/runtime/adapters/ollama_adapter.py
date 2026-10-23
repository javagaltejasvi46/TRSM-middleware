"""Adapter for local model inference via Ollama."""

from typing import Optional
import httpx
from ...config import settings


class OllamaAdapter:
    """Client for querying local Ollama instances."""

    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or settings.OLLAMA_BASE_URL

    async def generate(self, model: str, prompt: str, system: Optional[str] = None) -> str:
        """Call Ollama generate endpoint."""
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "system": system or "",
                    "stream": False,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("response", "")
