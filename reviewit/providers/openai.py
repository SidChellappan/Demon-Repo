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
    if not settings.api_key:
        raise ProviderError("Missing OpenAI API key. Run `reviewit init` or set OPENAI_API_KEY.")

    url = f"{(settings.base_url or 'https://api.openai.com/v1').rstrip('/')}/chat/completions"
    payload = {
        "model": settings.model,
        "stream": True,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.1,
    }
    headers = {
        "Authorization": f"Bearer {settings.api_key}",
        "Content-Type": "application/json",
    }

    try:
        with (
            httpx.Client(timeout=settings.timeout) as client,
            client.stream("POST", url, json=payload, headers=headers) as response,
        ):
            _raise_for_status(response)
            for line in response.iter_lines():
                if not line.startswith("data: "):
                    continue
                data = line.removeprefix("data: ").strip()
                if data == "[DONE]":
                    break
                chunk = json.loads(data)
                content = chunk.get("choices", [{}])[0].get("delta", {}).get("content")
                if content:
                    yield content
    except httpx.HTTPError as exc:
        raise ProviderError(f"OpenAI request failed: {exc}") from exc
    except (KeyError, IndexError, json.JSONDecodeError) as exc:
        raise ProviderError(f"OpenAI returned an unexpected streaming response: {exc}") from exc


def _raise_for_status(response: httpx.Response) -> None:
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        detail = exc.response.text[:500]
        raise ProviderError(f"OpenAI returned HTTP {exc.response.status_code}: {detail}") from exc
