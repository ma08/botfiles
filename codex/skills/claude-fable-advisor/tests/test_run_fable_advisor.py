"""Regression tests for the Fable advisor's tool isolation controls."""

from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path

SCRIPT_PATH = Path(__file__).parents[1] / "scripts" / "run_fable_advisor.py"
SPEC = importlib.util.spec_from_file_location("run_fable_advisor", SCRIPT_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def _args(*, yolo: bool = False) -> argparse.Namespace:
    return argparse.Namespace(model="fable", effort="max", yolo=yolo)


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
