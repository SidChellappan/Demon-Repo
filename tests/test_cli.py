import subprocess
from pathlib import Path

from typer.testing import CliRunner

from reviewit.cli import app

runner = CliRunner()


def run(args: list[str], cwd: Path) -> None:
    subprocess.run(args, cwd=cwd, check=True, capture_output=True, text=True)


def test_cli_no_diff_exits_cleanly(tmp_path: Path) -> None:
    run(["git", "init"], tmp_path)

    result = runner.invoke(app, ["--path", str(tmp_path)])

    assert result.exit_code == 0
    assert "No changes found" in result.output


def test_init_command_writes_config(tmp_path: Path) -> None:
    config_path = tmp_path / "config.toml"

    result = runner.invoke(
        app,
        [
            "init",
            "--config",
            str(config_path),
            "--model",
            "ollama",
            "--force",
        ],
    )

    assert result.exit_code == 0
    assert 'default_model = "ollama"' in config_path.read_text(encoding="utf-8")
