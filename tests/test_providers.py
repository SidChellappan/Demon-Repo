import pytest

from reviewit.config import ProviderSettings
from reviewit.providers import ProviderError, anthropic, ollama, openai


class FakeResponse:
    text = ""
    status_code = 200

    def __init__(self, lines: list[str]) -> None:
        self._lines = lines

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def iter_lines(self):
        return iter(self._lines)

    def raise_for_status(self) -> None:
        return None


class FakeClient:
    def __init__(self, *, lines: list[str]) -> None:
        self._lines = lines

    def __enter__(self) -> "FakeClient":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def stream(self, *args: object, **kwargs: object) -> FakeResponse:
        return FakeResponse(self._lines)


def test_openai_stream_parser(monkeypatch: pytest.MonkeyPatch) -> None:
    lines = [
        'data: {"choices":[{"delta":{"content":"Hi"}}]}',
        'data: {"choices":[{"delta":{"content":"!"}}]}',
        "data: [DONE]",
    ]
    monkeypatch.setattr(openai.httpx, "Client", lambda **kwargs: FakeClient(lines=lines))

    output = "".join(
        openai.stream_review(
            system_prompt="system",
            user_prompt="user",
            settings=ProviderSettings(name="openai", model="gpt-4o", api_key="key"),
        )
    )

    assert output == "Hi!"


def test_openai_requires_api_key() -> None:
    with pytest.raises(ProviderError, match="Missing OpenAI"):
        list(
            openai.stream_review(
                system_prompt="system",
                user_prompt="user",
                settings=ProviderSettings(name="openai", model="gpt-4o"),
            )
        )


def test_anthropic_stream_parser(monkeypatch: pytest.MonkeyPatch) -> None:
    lines = [
        "event: content_block_delta",
        'data: {"delta":{"text":"Ship"}}',
        "event: content_block_delta",
        'data: {"delta":{"text":" it"}}',
        "event: message_stop",
        "data: {}",
    ]
    monkeypatch.setattr(anthropic.httpx, "Client", lambda **kwargs: FakeClient(lines=lines))

    output = "".join(
        anthropic.stream_review(
            system_prompt="system",
            user_prompt="user",
            settings=ProviderSettings(name="anthropic", model="claude", api_key="key"),
        )
    )

    assert output == "Ship it"


def test_ollama_stream_parser(monkeypatch: pytest.MonkeyPatch) -> None:
    lines = [
        '{"message":{"content":"Local"}}',
        '{"message":{"content":" review"}}',
        '{"done":true}',
    ]
    monkeypatch.setattr(ollama.httpx, "Client", lambda **kwargs: FakeClient(lines=lines))

    output = "".join(
        ollama.stream_review(
            system_prompt="system",
            user_prompt="user",
            settings=ProviderSettings(name="ollama", model="llama3.1"),
        )
    )

    assert output == "Local review"
