from __future__ import annotations

import os
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:  # pragma: no cover - Python 3.11+ path
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10 path
    import tomli as tomllib


CONFIG_PATH = Path.home() / ".reviewit.toml"

PROVIDER_ALIASES = {
    "gpt": "openai",
    "openai": "openai",
    "claude": "anthropic",
    "anthropic": "anthropic",
    "ollama": "ollama",
    "local": "ollama",
}


@dataclass(frozen=True)
class ProviderSettings:
    name: str
    model: str
    api_key: str | None = None
    base_url: str | None = None
    host: str | None = None
    timeout: float = 120.0


@dataclass(frozen=True)
class ReviewitConfig:
    default_model: str = "gpt"
    default_style: str = "concise"
    openai: ProviderSettings = ProviderSettings(
        name="openai",
        model="gpt-4o",
        base_url="https://api.openai.com/v1",
    )
    anthropic: ProviderSettings = ProviderSettings(
        name="anthropic",
        model="claude-3-5-sonnet-latest",
        base_url="https://api.anthropic.com",
    )
    ollama: ProviderSettings = ProviderSettings(
        name="ollama",
        model="llama3.1",
        host="http://localhost:11434",
    )

    def provider_name(self, alias: str | None = None) -> str:
        requested = (alias or self.default_model).strip().lower()
        try:
            return PROVIDER_ALIASES[requested]
        except KeyError as exc:
            allowed = ", ".join(sorted(PROVIDER_ALIASES))
            raise ValueError(f"Unknown model/provider '{requested}'. Use one of: {allowed}.") from exc

    def settings_for(self, alias: str | None = None) -> ProviderSettings:
        provider = self.provider_name(alias)
        return getattr(self, provider)


def load_config(path: Path | None = None) -> ReviewitConfig:
    config_path = path or CONFIG_PATH
    data: dict[str, Any] = {}
    if config_path.exists():
        with config_path.open("rb") as handle:
            data = tomllib.load(handle)

    openai_data = _section(data, "openai")
    anthropic_data = _section(data, "anthropic")
    ollama_data = _section(data, "ollama")

    return ReviewitConfig(
        default_model=str(data.get("default_model", "gpt")),
        default_style=str(data.get("default_style", "concise")),
        openai=ProviderSettings(
            name="openai",
            model=str(openai_data.get("model", "gpt-4o")),
            api_key=_first_present(os.getenv("OPENAI_API_KEY"), openai_data.get("api_key")),
            base_url=str(openai_data.get("base_url", "https://api.openai.com/v1")),
            timeout=float(openai_data.get("timeout", 120.0)),
        ),
        anthropic=ProviderSettings(
            name="anthropic",
            model=str(anthropic_data.get("model", "claude-3-5-sonnet-latest")),
            api_key=_first_present(os.getenv("ANTHROPIC_API_KEY"), anthropic_data.get("api_key")),
            base_url=str(anthropic_data.get("base_url", "https://api.anthropic.com")),
            timeout=float(anthropic_data.get("timeout", 120.0)),
        ),
        ollama=ProviderSettings(
            name="ollama",
            model=str(ollama_data.get("model", "llama3.1")),
            host=str(
                _first_present(os.getenv("OLLAMA_HOST"), ollama_data.get("host"), "http://localhost:11434")
            ),
            timeout=float(ollama_data.get("timeout", 120.0)),
        ),
    )


def render_config(
    *,
    default_model: str,
    default_style: str,
    openai_api_key: str = "",
    anthropic_api_key: str = "",
    ollama_host: str = "http://localhost:11434",
    openai_model: str = "gpt-4o",
    anthropic_model: str = "claude-3-5-sonnet-latest",
    ollama_model: str = "llama3.1",
) -> str:
    return f"""default_model = "{_toml_string(default_model)}"
default_style = "{_toml_string(default_style)}"

[openai]
api_key = "{_toml_string(openai_api_key)}"
model = "{_toml_string(openai_model)}"
base_url = "https://api.openai.com/v1"

[anthropic]
api_key = "{_toml_string(anthropic_api_key)}"
model = "{_toml_string(anthropic_model)}"
base_url = "https://api.anthropic.com"

[ollama]
host = "{_toml_string(ollama_host)}"
model = "{_toml_string(ollama_model)}"
"""


def write_config(path: Path, contents: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(contents, encoding="utf-8")
    with suppress(OSError):
        os.chmod(path, 0o600)


def _section(data: dict[str, Any], name: str) -> dict[str, Any]:
    section = data.get(name, {})
    return section if isinstance(section, dict) else {}


def _first_present(*values: Any) -> Any:
    for value in values:
        if value not in (None, ""):
            return value
    return None


def _toml_string(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')
