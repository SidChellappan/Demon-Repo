from __future__ import annotations

from pathlib import Path

SYSTEM_PROMPT = """You are an expert code reviewer. Review the following git diff and return ONLY structured feedback in this format:

## Summary
One sentence: what changed and the verdict.

## 🔴 Critical (must fix before merging)
- [file:line] Issue description

## 🟡 Suggestions (nice to have)
- [file:line] Suggestion

## 🟢 Looks Good
- What was done well

Be specific. Reference file names and line numbers when possible. Be concise. No fluff."""

STYLE_GUIDANCE = {
    "concise": "Keep the review short. Prefer the highest-signal findings over exhaustive commentary.",
    "detailed": "Be thorough. Include rationale, edge cases, and concrete fixes for each finding.",
}

PROFILE_GUIDANCE = {
    "security": "Focus especially on security, auth, secrets, injection, unsafe I/O, and dependency risks.",
    "performance": "Focus especially on algorithmic cost, I/O, rendering, caching, and resource usage.",
    "junior": "Explain issues in approachable language while staying direct and practical.",
}


def build_user_prompt(
    *,
    diff: str,
    style: str,
    profile: str | None = None,
    rules: str | None = None,
    truncated: bool = False,
) -> str:
    if style not in STYLE_GUIDANCE:
        allowed = ", ".join(sorted(STYLE_GUIDANCE))
        raise ValueError(f"Unknown style '{style}'. Use one of: {allowed}.")

    sections = [
        f"Review style: {style}",
        STYLE_GUIDANCE[style],
    ]

    if profile:
        if profile not in PROFILE_GUIDANCE:
            allowed = ", ".join(sorted(PROFILE_GUIDANCE))
            raise ValueError(f"Unknown profile '{profile}'. Use one of: {allowed}.")
        sections.extend([f"Review profile: {profile}", PROFILE_GUIDANCE[profile]])

    if rules:
        sections.extend(
            [
                "Repository-specific rules:",
                rules.strip(),
            ]
        )

    if truncated:
        sections.append(
            "The diff was truncated before being sent. Prioritize the visible changed code and mention that the review is partial."
        )

    sections.extend(
        [
            "Git diff:",
            "```diff",
            diff,
            "```",
        ]
    )
    return "\n\n".join(sections)


def load_rules(repo_root: Path, explicit_rules: Path | None = None) -> str | None:
    candidates = [explicit_rules] if explicit_rules else [repo_root / ".reviewit.rules"]
    for candidate in candidates:
        if candidate and candidate.exists():
            return candidate.read_text(encoding="utf-8").strip()
    return None
