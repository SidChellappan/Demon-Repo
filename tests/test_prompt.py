from pathlib import Path

import pytest

from reviewit.prompt import build_user_prompt, load_rules


def test_build_user_prompt_includes_profile_and_rules() -> None:
    prompt = build_user_prompt(
        diff="+print('hello')",
        style="detailed",
        profile="security",
        rules="always check error handling",
    )

    assert "Review style: detailed" in prompt
    assert "Review profile: security" in prompt
    assert "always check error handling" in prompt
    assert "```diff" in prompt


def test_build_user_prompt_rejects_unknown_style() -> None:
    with pytest.raises(ValueError):
        build_user_prompt(diff="+x", style="verbose")


def test_load_rules_reads_default_file(tmp_path: Path) -> None:
    rules = tmp_path / ".reviewit.rules"
    rules.write_text('always_check = ["no print debugging"]\n', encoding="utf-8")

    assert load_rules(tmp_path) == 'always_check = ["no print debugging"]'
