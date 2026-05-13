import subprocess
from pathlib import Path

from reviewit.diff import get_diff, git_root


def run(args: list[str], cwd: Path) -> None:
    subprocess.run(args, cwd=cwd, check=True, capture_output=True, text=True)


def test_get_diff_reads_changes_against_head(tmp_path: Path) -> None:
    run(["git", "init"], tmp_path)
    run(["git", "config", "user.email", "test@example.com"], tmp_path)
    run(["git", "config", "user.name", "Test User"], tmp_path)
    file_path = tmp_path / "app.py"
    file_path.write_text("print('old')\n", encoding="utf-8")
    run(["git", "add", "app.py"], tmp_path)
    run(["git", "commit", "-m", "init"], tmp_path)

    file_path.write_text("print('new')\n", encoding="utf-8")
    result = get_diff(tmp_path)

    assert result.repo_root == git_root(tmp_path)
    assert "-print('old')" in result.text
    assert "+print('new')" in result.text


def test_get_diff_can_truncate(tmp_path: Path) -> None:
    run(["git", "init"], tmp_path)
    run(["git", "config", "user.email", "test@example.com"], tmp_path)
    run(["git", "config", "user.name", "Test User"], tmp_path)
    file_path = tmp_path / "app.py"
    file_path.write_text("x = 1\n", encoding="utf-8")
    run(["git", "add", "app.py"], tmp_path)
    run(["git", "commit", "-m", "init"], tmp_path)
    file_path.write_text("x = '" + ("a" * 5000) + "'\n", encoding="utf-8")

    result = get_diff(tmp_path, max_chars=1200)

    assert result.truncated is True
    assert "[reviewit: diff truncated" in result.text
