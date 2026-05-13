from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from reviewit.config import CONFIG_PATH, load_config, render_config, write_config
from reviewit.diff import DiffError, get_diff
from reviewit.formatter import print_error, print_intro, print_no_diff, stream_plain
from reviewit.hooks import HookError, install_pre_push_hook
from reviewit.prompt import SYSTEM_PROMPT, build_user_prompt, load_rules
from reviewit.providers import ProviderError, stream_review

app = typer.Typer(
    add_completion=False,
    context_settings={"help_option_names": ["-h", "--help"]},
    help="AI code review in your terminal, before you push.",
)


@app.callback(invoke_without_command=True)
def review(
    ctx: typer.Context,
    model: Annotated[
        str | None,
        typer.Option("--model", "-m", help="Provider alias: gpt, claude, or ollama."),
    ] = None,
    style: Annotated[
        str | None,
        typer.Option("--style", "-s", help="Review style: concise or detailed."),
    ] = None,
    path: Annotated[
        Path,
        typer.Option("--path", "-p", exists=True, file_okay=False, dir_okay=True, help="Git repo path."),
    ] = Path("."),
    staged: Annotated[
        bool,
        typer.Option("--staged", help="Review only staged changes with `git diff --staged`."),
    ] = False,
    base: Annotated[
        str,
        typer.Option("--base", help="Base ref for `git diff <base>` when not using --staged."),
    ] = "HEAD",
    profile: Annotated[
        str | None,
        typer.Option("--profile", help="Review profile: security, performance, or junior."),
    ] = None,
    rules: Annotated[
        Path | None,
        typer.Option("--rules", help="Rules file to append to the review prompt."),
    ] = None,
    max_chars: Annotated[
        int,
        typer.Option("--max-chars", min=1000, help="Maximum diff characters to send."),
    ] = 200_000,
) -> None:
    """Run an AI review for the selected git diff."""
    if ctx.invoked_subcommand is not None:
        return

    try:
        config = load_config()
        review_style = style or config.default_style
        provider = config.provider_name(model)
        settings = config.settings_for(model)
        diff = get_diff(path, staged=staged, base=base, max_chars=max_chars)
        if not diff.text:
            print_no_diff()
            raise typer.Exit(0)

        prompt = build_user_prompt(
            diff=diff.text,
            style=review_style,
            profile=profile,
            rules=load_rules(diff.repo_root, rules),
            truncated=diff.truncated,
        )

        print_intro(provider=provider, model=settings.model, style=review_style, profile=profile)
        stream_plain(
            stream_review(
                provider,
                system_prompt=SYSTEM_PROMPT,
                user_prompt=prompt,
                settings=settings,
            )
        )
    except (DiffError, ProviderError, HookError, ValueError) as exc:
        print_error(str(exc))
        raise typer.Exit(2) from exc


@app.command()
def init(
    config_path: Annotated[
        Path,
        typer.Option("--config", help="Config file to write."),
    ] = CONFIG_PATH,
    default_model: Annotated[
        str,
        typer.Option("--model", "-m", help="Default provider alias: gpt, claude, or ollama."),
    ] = "gpt",
    default_style: Annotated[
        str,
        typer.Option("--style", "-s", help="Default review style: concise or detailed."),
    ] = "concise",
    openai_key: Annotated[
        str,
        typer.Option("--openai-key", hide_input=True, help="OpenAI API key."),
    ] = "",
    anthropic_key: Annotated[
        str,
        typer.Option("--anthropic-key", hide_input=True, help="Anthropic API key."),
    ] = "",
    ollama_host: Annotated[
        str,
        typer.Option("--ollama-host", help="Ollama host URL."),
    ] = "http://localhost:11434",
    force: Annotated[
        bool,
        typer.Option("--force", help="Overwrite an existing config without prompting."),
    ] = False,
) -> None:
    """Create ~/.reviewit.toml."""
    if config_path.exists() and not force:
        overwrite = typer.confirm(f"{config_path} already exists. Overwrite?", default=False)
        if not overwrite:
            typer.echo("Config unchanged.")
            raise typer.Exit(0)

    contents = render_config(
        default_model=default_model,
        default_style=default_style,
        openai_api_key=openai_key,
        anthropic_api_key=anthropic_key,
        ollama_host=ollama_host,
    )
    write_config(config_path, contents)
    typer.secho(f"Wrote {config_path}", fg=typer.colors.GREEN)


@app.command("install-hook")
def install_hook(
    path: Annotated[
        Path,
        typer.Option("--path", "-p", exists=True, file_okay=False, dir_okay=True, help="Git repo path."),
    ] = Path("."),
    force: Annotated[
        bool,
        typer.Option("--force", help="Replace an existing pre-push hook instead of backing it up."),
    ] = False,
) -> None:
    """Install reviewit as the repository pre-push hook."""
    try:
        hook_path = install_pre_push_hook(path, force=force)
    except HookError as exc:
        print_error(str(exc))
        raise typer.Exit(2) from exc
    typer.secho(f"Installed pre-push hook at {hook_path}", fg=typer.colors.GREEN)


def main() -> None:
    app()
