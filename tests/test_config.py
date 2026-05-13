from pathlib import Path

from reviewit.config import load_config, render_config


def test_load_config_reads_file_and_env_override(tmp_path: Path, monkeypatch) -> None:
    config_path = tmp_path / "reviewit.toml"
    config_path.write_text(
        render_config(
            default_model="ollama",
            default_style="detailed",
            openai_api_key="from-file",
            anthropic_api_key="",
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("OPENAI_API_KEY", "from-env")

    config = load_config(config_path)

    assert config.default_model == "ollama"
    assert config.default_style == "detailed"
    assert config.openai.api_key == "from-env"
    assert config.settings_for("gpt").name == "openai"


def test_load_config_uses_env_when_file_key_missing(tmp_path: Path, monkeypatch) -> None:
    config_path = tmp_path / "reviewit.toml"
    config_path.write_text(
        render_config(default_model="gpt", default_style="concise"),
        encoding="utf-8",
    )
    monkeypatch.setenv("OPENAI_API_KEY", "from-env")

    config = load_config(config_path)

    assert config.openai.api_key == "from-env"
