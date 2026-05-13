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
        raise ProviderError("Missing Anthropic API key. Run `reviewit init` or set ANTHROPIC_API_KEY.")

    url = f"{(settings.base_url or 'https://api.anthropic.com').rstrip('/')}/v1/messages"
    payload = {
        "model": settings.model,
        "system": system_prompt,
        "max_tokens": 1600,
        "temperature": 0.1,
        "stream": True,
        "messages": [{"role": "user", "content": user_prompt}],
    }
    headers = {
        "x-api-key": settings.api_key,
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json",
    }

    try:
        with (
            httpx.Client(timeout=settings.timeout) as client,
            client.stream("POST", url, json=payload, headers=headers) as response,
        ):
            _raise_for_status(response)
            event = ""
            for line in response.iter_lines():
                if line.startswith("event: "):
                    event = line.removeprefix("event: ").strip()
                    continue
                if not line.startswith("data: "):
                    continue
                data = json.loads(line.removeprefix("data: ").strip())
                if event == "content_block_delta":
                    text = data.get("delta", {}).get("text")
                    if text:
                        yield text
                elif event == "message_stop":
                    break
    except httpx.HTTPError as exc:
        raise ProviderError(f"Anthropic request failed: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ProviderError(f"Anthropic returned an unexpected streaming response: {exc}") from exc


def _raise_for_status(response: httpx.Response) -> None:
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        detail = exc.response.text[:500]
        raise ProviderError(f"Anthropic returned HTTP {exc.response.status_code}: {detail}") from exc
