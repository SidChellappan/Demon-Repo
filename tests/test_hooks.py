import subprocess
from pathlib import Path

from reviewit.hooks import HOOK_MARKER, install_pre_push_hook


def run(args: list[str], cwd: Path) -> None:
    subprocess.run(args, cwd=cwd, check=True, capture_output=True, text=True)


def test_install_pre_push_hook_creates_hook(tmp_path: Path) -> None:
    run(["git", "init"], tmp_path)

    hook = install_pre_push_hook(tmp_path)

    assert hook.exists()
    assert HOOK_MARKER in hook.read_text(encoding="utf-8")
    assert "reviewit --path" in hook.read_text(encoding="utf-8")
    assert "python -m reviewit" in hook.read_text(encoding="utf-8")
