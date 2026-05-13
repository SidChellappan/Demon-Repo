from __future__ import annotations

import os
import subprocess
from datetime import datetime
from pathlib import Path

HOOK_MARKER = "# reviewit managed pre-push hook"


class HookError(RuntimeError):
    """Raised when a git hook cannot be installed."""


def install_pre_push_hook(repo_path: Path, *, force: bool = False) -> Path:
    root = _git_root(repo_path)
    hook_rel = _run_git(["git", "rev-parse", "--git-path", "hooks/pre-push"], root).strip()
    hook_path = (root / hook_rel).resolve() if not Path(hook_rel).is_absolute() else Path(hook_rel)
    hook_path.parent.mkdir(parents=True, exist_ok=True)

    if hook_path.exists():
        existing = hook_path.read_text(encoding="utf-8", errors="replace")
        if HOOK_MARKER not in existing:
            if force:
                hook_path.unlink()
            else:
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                backup = hook_path.with_name(f"pre-push.reviewit-backup-{timestamp}")
                hook_path.replace(backup)

    hook_path.write_text(_hook_script(), encoding="utf-8", newline="\n")
    try:
        current_mode = hook_path.stat().st_mode
        os.chmod(hook_path, current_mode | 0o111)
    except OSError:
        pass
    return hook_path


def _hook_script() -> str:
    return f"""#!/bin/sh
{HOOK_MARKER}
set -eu

repo_root="$(git rev-parse --show-toplevel)"
upstream="$(git rev-parse --abbrev-ref --symbolic-full-name @{{u}} 2>/dev/null || true)"

if [ -n "$upstream" ]; then
  base="$upstream"
else
  base="HEAD"
fi

if command -v reviewit >/dev/null 2>&1; then
  reviewit --path "$repo_root" --base "$base"
elif command -v python >/dev/null 2>&1; then
  python -m reviewit --path "$repo_root" --base "$base"
elif command -v python3 >/dev/null 2>&1; then
  python3 -m reviewit --path "$repo_root" --base "$base"
else
  echo "reviewit: could not find reviewit, python, or python3 on PATH" >&2
  exit 127
fi
"""


def _git_root(path: Path) -> Path:
    return Path(_run_git(["git", "rev-parse", "--show-toplevel"], path).strip()).resolve()


def _run_git(args: list[str], cwd: Path) -> str:
    result = subprocess.run(
        args,
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if result.returncode != 0:
        raise HookError((result.stderr or result.stdout or "unknown git error").strip())
    return result.stdout
