# CLAUDE.md

This repo is a Python CLI package named `reviewit`.

## Commands

- Install for development: `python -m pip install -e ".[dev]"`
- Run tests: `pytest`
- Lint: `ruff check .`
- Run locally: `reviewit --help`

## Architecture

- `reviewit/cli.py` owns Typer command parsing and user-facing exit behavior.
- `reviewit/diff.py` shells out to Git and returns the selected diff.
- `reviewit/prompt.py` builds the model prompts and loads `.reviewit.rules`.
- `reviewit/providers/` contains isolated streaming adapters for OpenAI, Anthropic, and Ollama.
- `reviewit/hooks.py` installs the pre-push hook.
- `reviewit/formatter.py` owns terminal rendering.

## Guardrails

- Keep provider SDK dependencies out of the core package; adapters call HTTP APIs directly with `httpx`.
- Never log API keys or config secrets.
- Preserve the structured review output contract in `reviewit/prompt.py`.
- Add tests for every CLI behavior change.
