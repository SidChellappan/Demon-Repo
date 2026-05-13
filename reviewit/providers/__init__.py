from __future__ import annotations

from collections.abc import Iterator

from reviewit.config import ProviderSettings


class ProviderError(RuntimeError):
    """Raised when a provider cannot produce a review."""


def stream_review(
    provider: str,
    *,
    system_prompt: str,
    user_prompt: str,
    settings: ProviderSettings,
) -> Iterator[str]:
    if provider == "openai":
        from .openai import stream_review as stream_openai

        yield from stream_openai(system_prompt=system_prompt, user_prompt=user_prompt, settings=settings)
        return
    if provider == "anthropic":
        from .anthropic import stream_review as stream_anthropic

        yield from stream_anthropic(system_prompt=system_prompt, user_prompt=user_prompt, settings=settings)
        return
    if provider == "ollama":
        from .ollama import stream_review as stream_ollama

        yield from stream_ollama(system_prompt=system_prompt, user_prompt=user_prompt, settings=settings)
        return
    raise ProviderError(f"Unsupported provider: {provider}")
