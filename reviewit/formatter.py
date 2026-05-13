from __future__ import annotations

from collections.abc import Iterable

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

console = Console()


def print_intro(*, provider: str, model: str, style: str, profile: str | None = None) -> None:
    profile_part = f" | profile: {profile}" if profile else ""
    console.print(
        Panel.fit(
            f"[bold]reviewit[/bold] is reviewing your diff\n"
            f"provider: [cyan]{provider}[/cyan] | model: [cyan]{model}[/cyan] | "
            f"style: [cyan]{style}[/cyan]{profile_part}",
            border_style="cyan",
        )
    )


def print_no_diff() -> None:
    console.print("[yellow]No changes found in the selected git diff.[/yellow]")


def print_error(message: str) -> None:
    console.print(f"[red]reviewit error:[/red] {message}")


def stream_plain(chunks: Iterable[str]) -> str:
    collected: list[str] = []
    for chunk in chunks:
        collected.append(chunk)
        console.print(chunk, end="", markup=False, highlight=False)
    console.print()
    return "".join(collected)


def print_markdown(text: str) -> None:
    console.print(Markdown(text))
