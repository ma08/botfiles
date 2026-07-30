#!/usr/bin/env python3
"""Run a subscription-gated Claude Fable 5 advisory request.

The script refuses before any model call unless Claude Code reports first-party
claude.ai subscription authentication under a cleaned provider environment.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path


PROVIDER_FALSE_ENV = {
    "CLAUDE_CODE_USE_BEDROCK": "0",
    "CLAUDE_CODE_USE_MANTLE": "0",
    "CLAUDE_CODE_USE_VERTEX": "0",
    "CLAUDE_CODE_USE_FOUNDRY": "0",
    "CLAUDE_CODE_USE_ANTHROPIC_AWS": "0",
}

PROVIDER_REMOVE_ENV = {
    "CLAUDE_CODE_PROVIDER_MANAGED_BY_HOST",
    "CLAUDE_CODE_USE_ANTHROPIC",
    "ANTHROPIC_API_KEY",
    "ANTHROPIC_AUTH_TOKEN",
    "ANTHROPIC_BASE_URL",
    "ANTHROPIC_BEDROCK_BASE_URL",
    "ANTHROPIC_BEDROCK_MANTLE_BASE_URL",
    "ANTHROPIC_VERTEX_BASE_URL",
    "AWS_BEARER_TOKEN_BEDROCK",
}

EFFORT_CHOICES = ("low", "medium", "high", "xhigh", "max")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    prompt_group = parser.add_mutually_exclusive_group()
    prompt_group.add_argument("--prompt", help="Prompt text to send to Fable.")
    prompt_group.add_argument("--prompt-file", type=Path, help="File containing the prompt.")
    parser.add_argument(
        "--file",
        action="append",
        default=[],
        type=Path,
        help="Text file to inline into the prompt. Repeat for multiple files.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Directory for prompt.md, answer.md, stderr.txt, and status.json.",
    )
    parser.add_argument("--cwd", type=Path, default=Path.cwd(), help="Claude process cwd.")
    parser.add_argument("--model", default="fable", help="Claude model alias or ID.")
    parser.add_argument("--effort", default="max", choices=EFFORT_CHOICES)
    parser.add_argument(
        "--max-turns",
        type=int,
        help="Maximum agentic turns. Defaults to 1 without tools and 3 with tools.",
    )
    parser.add_argument(
        "--tools",
        default="",
        help=(
            'Claude --tools allowlist. Default empty string disables all tools. '
            'Use values such as "Read,Bash"; prefer --with-tools for the full '
            "default tool set."
        ),
    )
    parser.add_argument(
        "--with-tools",
        action="store_true",
        help="Enable Claude Code's full default built-in tool set.",
    )
    parser.add_argument(
        "--yolo",
        action="store_true",
        help=(
            "Bypass Claude Code permission checks. Requires --with-tools or a "
            "non-empty --tools allowlist."
        ),
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Run the subscription route gate and write status, but do not call Fable.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run the route gate and render prompt/status files, but do not call Fable.",
    )
    parser.add_argument(
        "--max-file-bytes",
        type=int,
        default=500_000,
        help="Refuse to inline any attached file larger than this size.",
    )
    return parser.parse_args()


def clean_env() -> dict[str, str]:
    env = os.environ.copy()
    for name in PROVIDER_REMOVE_ENV:
        env.pop(name, None)
    for name, value in PROVIDER_FALSE_ENV.items():
        env[name] = value
    return env


def safe_settings(model: str, effort: str) -> str:
    return json.dumps(
        {
            "model": model,
            "effortLevel": effort,
            "env": PROVIDER_FALSE_ENV,
        },
        separators=(",", ":"),
    )


def run_command(
    command: list[str],
    *,
    cwd: Path,
    env: dict[str, str],
    input_text: str | None = None,
    timeout_seconds: int | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=str(cwd),
        env=env,
        input=input_text,
        text=True,
        capture_output=True,
        check=False,
        timeout=timeout_seconds,
    )


def load_prompt(args: argparse.Namespace) -> str:
    if args.prompt is not None:
        return args.prompt
    if args.prompt_file is not None:
        return args.prompt_file.read_text()
    if args.check_only:
        return ""
    raise SystemExit(
        "run_fable_advisor.py: provide --prompt or --prompt-file "
        "unless --check-only is set"
    )


def resolve_file(path: Path, cwd: Path) -> Path:
    candidate = path if path.is_absolute() else cwd / path
    return candidate.resolve()


def inline_files(prompt: str, files: list[Path], cwd: Path, max_file_bytes: int) -> str:
    if not files:
        return prompt

    sections = [prompt.rstrip(), "", "# Attached Files"]
    for raw_path in files:
        path = resolve_file(raw_path, cwd)
        if not path.exists():
            raise SystemExit(f"run_fable_advisor.py: attached file missing: {path}")
        if not path.is_file():
            raise SystemExit(f"run_fable_advisor.py: attached path is not a file: {path}")
        size = path.stat().st_size
        if size > max_file_bytes:
            raise SystemExit(
                "run_fable_advisor.py: attached file exceeds "
                f"--max-file-bytes ({size} > {max_file_bytes}): {path}"
            )
        try:
            display_path = path.relative_to(cwd)
        except ValueError:
            display_path = path
        text = path.read_text(errors="replace")
        sections.extend(
            [
                "",
                f"## {display_path}",
                "",
                "````text",
                text.rstrip(),
                "````",
            ]
        )
    return "\n".join(sections).rstrip() + "\n"


def default_output_dir(cwd: Path) -> Path:
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return cwd / ".fable-advisor-runs" / stamp


def auth_gate(
    claude_bin: str,
    args: argparse.Namespace,
    env: dict[str, str],
) -> tuple[bool, dict[str, object]]:
    command = [
        claude_bin,
        "--setting-sources",
        "user",
        "--settings",
        safe_settings(args.model, args.effort),
        "auth",
        "status",
        "--json",
    ]
    completed = run_command(command, cwd=args.cwd, env=env, timeout_seconds=30)
    try:
        parsed = json.loads(completed.stdout or "{}")
    except json.JSONDecodeError:
        parsed = {}

    safe = {
        "loggedIn": parsed.get("loggedIn"),
        "authMethod": parsed.get("authMethod"),
        "apiProvider": parsed.get("apiProvider"),
        "subscriptionType": parsed.get("subscriptionType"),
        "authStatusExitCode": completed.returncode,
    }
    ok = (
        completed.returncode == 0
        and safe["loggedIn"] is True
        and safe["authMethod"] == "claude.ai"
        and safe["apiProvider"] == "firstParty"
        and bool(safe["subscriptionType"])
    )
    return ok, safe


def write_status(output_dir: Path, status: dict[str, object]) -> None:
    (output_dir / "status.json").write_text(json.dumps(status, indent=2, sort_keys=True) + "\n")


def resolve_tools(args: argparse.Namespace) -> str:
    if args.with_tools and args.tools:
        raise SystemExit(
            "run_fable_advisor.py: use either --with-tools or --tools, not both"
        )
    tools = "default" if args.with_tools else args.tools
    if args.yolo and not tools:
        raise SystemExit(
            "run_fable_advisor.py: --yolo requires --with-tools or a non-empty "
            "--tools allowlist"
        )
    return tools


def main() -> int:
    args = parse_args()
    args.cwd = args.cwd.resolve()
    tools = resolve_tools(args)
    max_turns = args.max_turns if args.max_turns is not None else (3 if tools else 1)
    output_dir = (args.output_dir or default_output_dir(args.cwd)).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    claude_bin = shutil.which("claude")
    if not claude_bin:
        status = {"ok": False, "error": "claude command not found"}
        write_status(output_dir, status)
        print(status["error"], file=sys.stderr)
        return 127

    env = clean_env()
    route_ok, auth_status = auth_gate(claude_bin, args, env)
    status: dict[str, object] = {
        "ok": False,
        "routeGate": auth_status,
        "outputDir": str(output_dir),
        "model": args.model,
        "effort": args.effort,
        "tools": tools or "disabled",
        "yolo": args.yolo,
        "maxTurns": max_turns,
        "checkOnly": args.check_only,
        "dryRun": args.dry_run,
    }

    if not route_ok:
        status["error"] = "Claude Code is not using first-party claude.ai subscription auth"
        write_status(output_dir, status)
        print(status["error"], file=sys.stderr)
        print(json.dumps(auth_status, indent=2, sort_keys=True), file=sys.stderr)
        return 3

    if args.check_only:
        status["ok"] = True
        status["message"] = "Route gate passed; no model request was made."
        write_status(output_dir, status)
        print(status["message"])
        print(json.dumps(auth_status, indent=2, sort_keys=True))
        return 0

    prompt = inline_files(load_prompt(args), args.file, args.cwd, args.max_file_bytes)
    (output_dir / "prompt.md").write_text(prompt)

    command = [
        claude_bin,
        "--setting-sources",
        "user",
        "--settings",
        safe_settings(args.model, args.effort),
        "--model",
        args.model,
        "--effort",
        args.effort,
        "--tools",
        tools,
        "--no-session-persistence",
        "--output-format",
        "text",
        "--max-turns",
        str(max_turns),
        "-p",
        "Respond to the advisory request provided on stdin.",
    ]
    if args.yolo:
        command.insert(command.index("--no-session-persistence"), "--dangerously-skip-permissions")
    status["commandPreview"] = " ".join(shlex.quote(part) for part in command) + " < prompt.md"
    status["promptPath"] = str(output_dir / "prompt.md")
    write_status(output_dir, status)

    if args.dry_run:
        status["ok"] = True
        status["message"] = "Route gate passed; prompt rendered; no model request was made."
        write_status(output_dir, status)
        print(status["message"])
        print(f"Prompt: {output_dir / 'prompt.md'}")
        print(f"Status: {output_dir / 'status.json'}")
        return 0

    completed = run_command(command, cwd=args.cwd, env=env, input_text=prompt)
    (output_dir / "answer.md").write_text(completed.stdout or "")
    (output_dir / "stderr.txt").write_text(completed.stderr or "")

    status["exitCode"] = completed.returncode
    status["ok"] = completed.returncode == 0
    status["answerPath"] = str(output_dir / "answer.md")
    status["stderrPath"] = str(output_dir / "stderr.txt")
    status["promptPath"] = str(output_dir / "prompt.md")
    if completed.returncode != 0:
        status["error"] = "Claude Fable request failed after subscription route gate passed"
    write_status(output_dir, status)

    if completed.stdout:
        print(completed.stdout, end="")
    if completed.stderr:
        print(completed.stderr, end="", file=sys.stderr)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
