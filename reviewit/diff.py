from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path


class DiffError(RuntimeError):
    """Raised when reviewit cannot read a git diff."""


@dataclass(frozen=True)
class DiffResult:
    text: str
    repo_root: Path
    truncated: bool = False


def get_diff(
    repo_path: Path,
    *,
    staged: bool = False,
    base: str = "HEAD",
    max_chars: int = 200_000,
) -> DiffResult:
    root = git_root(repo_path)
    args = ["git", "diff", "--staged"] if staged else _unstaged_args(root, base)
    raw = _run_git(args, root)
    truncated = len(raw) > max_chars
    if truncated:
        raw = raw[:max_chars] + "\n\n[reviewit: diff truncated at max_chars]\n"
    return DiffResult(text=raw.strip(), repo_root=root, truncated=truncated)


def git_root(path: Path) -> Path:
    output = _run_git(["git", "rev-parse", "--show-toplevel"], path)
    return Path(output.strip()).resolve()


def _unstaged_args(root: Path, base: str) -> list[str]:
    if base == "HEAD" and not _has_head(root):
        return ["git", "diff", "--staged"]
    return ["git", "diff", base]


def _has_head(root: Path) -> bool:
    result = subprocess.run(
        ["git", "rev-parse", "--verify", "HEAD"],
        cwd=root,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        text=True,
        check=False,
    )
    return result.returncode == 0


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
        message = (result.stderr or result.stdout or "unknown git error").strip()
        raise DiffError(message)
    return result.stdout
