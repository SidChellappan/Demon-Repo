from __future__ import annotations

import json
from collections.abc import Iterator

import httpx

from reviewit.config import ProviderSettings
from reviewit.providers import ProviderError


def stream_review(
    *,
    system_prompt: str,
    user_prompt: str,
    settings: ProviderSettings,
) -> Iterator[str]:
    host = (settings.host or "http://localhost:11434").rstrip("/")
    url = f"{host}/api/chat"
    payload = {
        "model": settings.model,
        "stream": True,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "options": {"temperature": 0.1},
    }

    try:
        with (
            httpx.Client(timeout=settings.timeout) as client,
            client.stream("POST", url, json=payload) as response,
        ):
            _raise_for_status(response)
            for line in response.iter_lines():
                if not line:
                    continue
                data = json.loads(line)
                if data.get("done"):
                    break
                content = data.get("message", {}).get("content") or data.get("response")
                if content:
                    yield content
    except httpx.ConnectError as exc:
        raise ProviderError(
            "Could not connect to Ollama. Start it with `ollama serve` or set OLLAMA_HOST."
        ) from exc
    except httpx.HTTPError as exc:
        raise ProviderError(f"Ollama request failed: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ProviderError(f"Ollama returned an unexpected streaming response: {exc}") from exc


def _raise_for_status(response: httpx.Response) -> None:
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        detail = exc.response.text[:500]
        raise ProviderError(f"Ollama returned HTTP {exc.response.status_code}: {detail}") from exc
