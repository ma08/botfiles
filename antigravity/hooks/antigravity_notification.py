"""
Notification hook for Google Antigravity (`~/.gemini/config/hooks.json`).

Handles:
- `Stop`: notifies when a turn finishes (or terminates with an error),
  extracting the latest assistant response from Antigravity's JSONL transcript.
- `PreToolUse` (matched on `ask_question`): notifies when Antigravity is
  waiting on user input.

Always emits valid Antigravity hook JSON on stdout (`{"decision": "allow"}`
for `PreToolUse`, `{}` for `Stop`) and dispatches notification delivery in a
detached background process by default so synchronous hooks never stall the
agent loop.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any


_UTILS_DIR = Path(__file__).resolve().parents[2] / "utils"
if str(_UTILS_DIR) not in sys.path:
    sys.path.insert(0, str(_UTILS_DIR))

from notify_utils import _log, send_notification  # noqa: E402


_DISPATCH_ENV_KEY = "_AGY_NOTIFY_SPEC"
_MAX_MESSAGE_CHARS = 3000
_MAX_QUESTION_CHARS = 200


def get_latest_antigravity_message(transcript_path: str) -> str:
    """Return the latest non-empty PLANNER_RESPONSE content from an Antigravity transcript."""
    if not transcript_path:
        return ""

    path = Path(transcript_path).expanduser()
    if not path.is_file():
        return ""

    latest = ""
    try:
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            for raw_line in handle:
                line = raw_line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if not isinstance(entry, dict):
                    continue
                if entry.get("type") != "PLANNER_RESPONSE":
                    continue
                content = entry.get("content")
                if isinstance(content, str) and content.strip():
                    latest = content.strip()
    except OSError as exc:
        _log(f"Antigravity transcript read failed ({path}): {exc}")
        return ""

    if len(latest) > _MAX_MESSAGE_CHARS:
        latest = latest[: _MAX_MESSAGE_CHARS - 1].rstrip() + "…"
    return latest


def resolve_working_directory(payload: dict[str, Any]) -> str | None:
    """Resolve the workspace/working directory from an Antigravity hook payload."""
    for key in ("cwd", "working_directory", "workdir"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()

    workspace_paths = payload.get("workspacePaths")
    if isinstance(workspace_paths, list):
        for item in workspace_paths:
            if isinstance(item, str) and item.strip():
                return item.strip()
    return None


def resolve_conversation_id(payload: dict[str, Any]) -> str | None:
    """Resolve the Antigravity conversation ID for notification session tracking."""
    for key in ("conversationId", "conversation_id", "sessionId", "session_id"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def hook_response_for_event(hook_event: str) -> dict[str, Any]:
    """Return the non-blocking JSON response required by Antigravity for this hook event."""
    if hook_event == "PreToolUse":
        return {"decision": "allow"}
    return {}


def build_notification_spec(payload: dict[str, Any]) -> dict[str, Any] | None:
    """Build kwargs for `send_notification`, or return None when no alert should be sent."""
    if not isinstance(payload, dict):
        return None

    hook_event = str(payload.get("hookEventName", "")).strip()
    working_dir = resolve_working_directory(payload)
    session_id = resolve_conversation_id(payload)

    if hook_event == "PreToolUse":
        tool_call = payload.get("toolCall")
        if not isinstance(tool_call, dict):
            return None
        tool_name = str(tool_call.get("name", "")).strip()
        if tool_name and tool_name != "ask_question":
            return None

        args = tool_call.get("args")
        questions = args.get("questions", []) if isinstance(args, dict) else []
        first_question = ""
        if isinstance(questions, list) and questions:
            first_item = questions[0]
            if isinstance(first_item, dict):
                first_question = str(first_item.get("question", "")).strip()

        detail = (
            f"Question: {first_question[:_MAX_QUESTION_CHARS]}"
            if first_question
            else "Antigravity is asking a question"
        )
        return {
            "title": "Antigravity",
            "message": f"Awaiting Your Input\n{detail}",
            "agent_session_id_override": session_id,
            "coding_agent_override": "antigravity",
            "working_directory_override": working_dir,
        }

    if hook_event == "Stop":
        reason = str(payload.get("terminationReason", "")).strip()
        if reason == "USER_CANCELED":
            return None

        # When background tasks/subagents are still running and the turn ended
        # cleanly only to await them, defer alerting until the conversation is idle.
        if payload.get("fullyIdle") is False and reason in ("", "NO_TOOL_CALL"):
            return None

        transcript_path = str(payload.get("transcriptPath", "")).strip()
        latest_message = get_latest_antigravity_message(transcript_path)
        error_text = str(payload.get("error", "")).strip()

        if reason == "ERROR" or error_text:
            header = f"Stopped ({reason or 'ERROR'})"
            body = error_text or latest_message
        else:
            header = "Finished Processing"
            body = latest_message

        message = f"{header}\n{body}".strip() if body else header
        return {
            "title": "Antigravity",
            "message": message,
            "agent_session_id_override": session_id,
            "coding_agent_override": "antigravity",
            "working_directory_override": working_dir,
        }

    return None


def dispatch_notification_async(spec: dict[str, Any]) -> None:
    """Spawn a detached child process to send the notification without blocking Antigravity."""
    env = os.environ.copy()
    env[_DISPATCH_ENV_KEY] = json.dumps(spec)
    subprocess.Popen(
        [sys.executable, str(Path(__file__).resolve()), "--dispatch"],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
        close_fds=True,
        env=env,
    )


def handle_hook_payload(payload: dict[str, Any], *, sync: bool = False) -> dict[str, Any]:
    """Process a hook payload, trigger notification if applicable, and return hook response JSON."""
    hook_event = str(payload.get("hookEventName", "")).strip() if isinstance(payload, dict) else ""
    response = hook_response_for_event(hook_event)

    try:
        spec = build_notification_spec(payload)
        if spec is not None:
            _log(
                "Antigravity notify: "
                f"event={hook_event or 'unknown'}, "
                f"conversation_id={spec.get('agent_session_id_override') or 'none'}"
            )
            if sync:
                send_notification(**spec)
            else:
                dispatch_notification_async(spec)
    except Exception as exc:
        _log(f"Antigravity notify hook error: {exc}")

    return response


def _run_dispatch_mode() -> int:
    raw_spec = os.environ.get(_DISPATCH_ENV_KEY, "")
    if not raw_spec:
        return 0
    try:
        spec = json.loads(raw_spec)
        if isinstance(spec, dict):
            send_notification(**spec)
    except Exception as exc:
        _log(f"Antigravity async dispatch failed: {exc}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Antigravity notification hook")
    parser.add_argument(
        "--sync",
        action="store_true",
        help="Send notification synchronously instead of spawning a detached worker.",
    )
    parser.add_argument(
        "--dispatch",
        action="store_true",
        help=argparse.SUPPRESS,
    )
    args = parser.parse_args(argv)

    if args.dispatch:
        return _run_dispatch_mode()

    payload: dict[str, Any] = {}
    try:
        raw_input = sys.stdin.read()
        if raw_input.strip():
            parsed = json.loads(raw_input)
            if isinstance(parsed, dict):
                payload = parsed
    except Exception as exc:
        _log(f"Antigravity hook received invalid JSON: {exc}")

    response = handle_hook_payload(payload, sync=args.sync)
    print(json.dumps(response))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
