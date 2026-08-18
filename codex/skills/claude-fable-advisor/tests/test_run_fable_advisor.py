"""Regression tests for the Fable advisor's tool isolation controls."""

from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path

import pytest

SCRIPT_PATH = Path(__file__).parents[1] / "scripts" / "run_fable_advisor.py"
SPEC = importlib.util.spec_from_file_location("run_fable_advisor", SCRIPT_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def _args(
    *,
    yolo: bool = False,
    read_only_review: bool = False,
    with_tools: bool = False,
    tools: str = "",
    inherit_credentials: bool = False,
    max_turns: int | None = None,
) -> argparse.Namespace:
    return argparse.Namespace(
        cwd=Path.cwd(),
        model="fable",
        effort="max",
        yolo=yolo,
        read_only_review=read_only_review,
        with_tools=with_tools,
        tools=tools,
        inherit_credentials=inherit_credentials,
        max_turns=max_turns,
    )


def test_tool_environment_strips_ambient_credentials() -> None:
    env = MODULE.clean_env(
        strip_ambient_credentials=True,
        source_env={
            "PATH": "/usr/bin",
            "CLAUDE_CODE_OAUTH_TOKEN": "subscription-token",
            "AWS_ACCESS_KEY_ID": "aws-secret",
            "GOOGLE_APPLICATION_CREDENTIALS": "/secret/google.json",
            "GITHUB_TOKEN": "github-secret",
            "LINEAR_API_KEY": "linear-secret",
            "NPM_TOKEN": "npm-secret",
            "ANTHROPIC_API_KEY": "api-billing-secret",
        },
    )

    assert env["PATH"] == "/usr/bin"
    assert env["CLAUDE_CODE_OAUTH_TOKEN"] == "subscription-token"
    assert "AWS_ACCESS_KEY_ID" not in env
    assert "GOOGLE_APPLICATION_CREDENTIALS" not in env
    assert "GITHUB_TOKEN" not in env
    assert "LINEAR_API_KEY" not in env
    assert "NPM_TOKEN" not in env
    assert "ANTHROPIC_API_KEY" not in env


def test_tool_command_uses_safe_mode_and_empty_strict_mcp() -> None:
    command = MODULE.build_fable_command("claude", _args(), "Read,Bash", 3)

    assert "--safe-mode" in command
    assert "--strict-mcp-config" in command
    assert command[command.index("--mcp-config") + 1] == '{"mcpServers":{}}'
    assert "--setting-sources" not in command
    assert "--dangerously-skip-permissions" not in command


def test_yolo_command_keeps_isolation_controls() -> None:
    command = MODULE.build_fable_command("claude", _args(yolo=True), "default", 3)

    assert "--safe-mode" in command
    assert "--strict-mcp-config" in command
    assert "--dangerously-skip-permissions" in command


def test_read_only_review_command_is_bounded_without_bypass() -> None:
    args = _args(read_only_review=True)
    tools = MODULE.resolve_tools(args)
    command = MODULE.build_fable_command(
        "claude", args, tools, MODULE.resolve_max_turns(args, tools)
    )

    assert tools == "Read,Glob,Grep,Bash"
    assert command[command.index("--permission-mode") + 1] == "dontAsk"
    allowed = command[command.index("--allowedTools") + 1].split(",")
    assert set(allowed) == set(MODULE.READ_ONLY_REVIEW_ALLOWED_TOOLS)
    assert "Edit" not in tools
    assert "Write" not in tools
    assert "--dangerously-skip-permissions" not in command
    assert "--max-turns" in command
    assert command[command.index("--max-turns") + 1] == "12"


@pytest.mark.parametrize(
    "conflict",
    [
        {"yolo": True},
        {"with_tools": True},
        {"tools": "Read"},
        {"inherit_credentials": True},
    ],
)
def test_read_only_review_rejects_broader_authority(
    conflict: dict[str, object],
) -> None:
    args = _args(read_only_review=True, **conflict)

    with pytest.raises(SystemExit, match="--read-only-review cannot be combined"):
        MODULE.resolve_tools(args)


def test_read_only_review_boundary_is_added_to_prompt() -> None:
    prompt = MODULE.apply_read_only_review_boundary("Review this repository.\n", True)

    assert prompt.startswith("# Mandatory read-only review boundary")
    assert "Do not create, edit, rename, or delete files" in prompt
    assert prompt.endswith("Review this repository.\n")


def test_explicit_max_turns_overrides_read_only_default() -> None:
    args = _args(read_only_review=True, max_turns=18)
    tools = MODULE.resolve_tools(args)

    assert MODULE.resolve_max_turns(args, tools) == 18


def test_runner_loads_private_oauth_token_file(tmp_path: Path) -> None:
    token_file = tmp_path / "oauth-token"
    token_file.write_text("subscription-oauth-token\n")
    token_file.chmod(0o600)

    env, source = MODULE.configure_subscription_oauth(
        {"PATH": "/usr/bin"},
        explicit_token_file=token_file,
    )

    assert env["CLAUDE_CODE_OAUTH_TOKEN"] == "subscription-oauth-token"
    assert source == "token-file"


def test_environment_oauth_token_takes_precedence(tmp_path: Path) -> None:
    token_file = tmp_path / "oauth-token"
    token_file.write_text("file-token\n")
    token_file.chmod(0o600)

    env, source = MODULE.configure_subscription_oauth(
        {"CLAUDE_CODE_OAUTH_TOKEN": "environment-token"},
        explicit_token_file=token_file,
    )

    assert env["CLAUDE_CODE_OAUTH_TOKEN"] == "environment-token"
    assert source == "environment"


def test_oauth_token_file_rejects_broad_permissions(tmp_path: Path) -> None:
    token_file = tmp_path / "oauth-token"
    token_file.write_text("subscription-oauth-token\n")
    token_file.chmod(0o644)

    with pytest.raises(SystemExit, match="permissions are too broad"):
        MODULE.configure_subscription_oauth(
            {},
            explicit_token_file=token_file,
        )


def test_missing_default_oauth_token_uses_stored_login(tmp_path: Path) -> None:
    env, source = MODULE.configure_subscription_oauth(
        {"PATH": "/usr/bin"},
        default_token_file=tmp_path / "missing-token",
    )

    assert "CLAUDE_CODE_OAUTH_TOKEN" not in env
    assert source == "stored-login"


def test_long_lived_oauth_metadata_is_accepted_only_for_token_source(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    completed = MODULE.subprocess.CompletedProcess(
        args=["claude"],
        returncode=0,
        stdout=(
            '{"loggedIn":true,"authMethod":"oauth_token",'
            '"apiProvider":"firstParty","subscriptionType":null}'
        ),
        stderr="",
    )
    monkeypatch.setattr(MODULE, "run_command", lambda *args, **kwargs: completed)

    accepted, _ = MODULE.auth_gate(
        "claude",
        _args(),
        {"CLAUDE_CODE_OAUTH_TOKEN": "token"},
        "token-file",
    )
    rejected, _ = MODULE.auth_gate(
        "claude",
        _args(),
        {},
        "stored-login",
    )

    assert accepted is True
    assert rejected is False
