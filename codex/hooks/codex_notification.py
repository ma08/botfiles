"""
Notification hook for Codex CLI.
Expects a JSON payload as argv[1] per Codex config notifications.
"""
from __future__ import annotations

import json
import re
import sys
from typing import Any
from pathlib import Path


_UTILS_DIR = Path(__file__).resolve().parents[2] / "utils"
if str(_UTILS_DIR) not in sys.path:
    sys.path.insert(0, str(_UTILS_DIR))

from notify_utils import _get_agent_session_id, _log, send_notification  # noqa: E402

_SESSION_ID_KEYS = {
    "session_id",
    "thread_id",
    "conversation_id",
    "codex_thread_id",
    "codex_session_id",
    "agent_session_id",
    "claude_session_id",
}


def _load_payload() -> dict:
    if len(sys.argv) > 1:
        raw = sys.argv[1]
        return json.loads(raw)
    if not sys.stdin.isatty():
        return json.load(sys.stdin)
    raise ValueError("No JSON payload provided to codex_notification.py")


def _normalize_key_name(key: str) -> str:
    key_with_snake_case = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", key)
    return key_with_snake_case.replace("-", "_").lower()


def _looks_like_session_id(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    candidate = value.strip()
    if not candidate:
        return False
    if candidate.lower() in {"none", "null", "unknown"}:
        return False
    if len(candidate) < 8 or len(candidate) > 200:
        return False
    if any(char.isspace() for char in candidate):
        return False
    return True


def _extract_session_id_from_payload(value: Any, depth: int = 0) -> str:
    if depth > 6:
        return ""

    if isinstance(value, dict):
        # Prefer direct key hits before recursive descent.
        for raw_key, raw_value in value.items():
            key_name = _normalize_key_name(str(raw_key))
            if key_name in _SESSION_ID_KEYS and _looks_like_session_id(raw_value):
                return str(raw_value).strip()

        for raw_key, raw_value in value.items():
            key_name = _normalize_key_name(str(raw_key))
            if key_name == "last_assistant_message":
                continue
            resolved = _extract_session_id_from_payload(raw_value, depth + 1)
            if resolved:
                return resolved
        return ""

    if isinstance(value, list):
        for item in value[:20]:
            resolved = _extract_session_id_from_payload(item, depth + 1)
            if resolved:
                return resolved
        return ""

    return ""


def _resolve_agent_session_id(input_data: dict) -> str:
    env_session_id = _get_agent_session_id()
    if _looks_like_session_id(env_session_id):
        return env_session_id.strip()
    return _extract_session_id_from_payload(input_data)


def handle_notification(input_data: dict) -> None:
    event_type = input_data.get("type", "")
    if event_type and event_type != "agent-turn-complete":
        return

    agent_session_id = _resolve_agent_session_id(input_data)
    payload_keys = sorted(input_data.keys()) if isinstance(input_data, dict) else []
    _log(
        "Codex notify payload: "
        f"type={event_type or 'unknown'}, "
        f"keys={payload_keys}, "
        f"agent_session_id={agent_session_id or 'none'}"
    )

    last_message = input_data.get("last-assistant-message", "")
    if isinstance(last_message, dict):
        last_message = json.dumps(last_message)

    message_lines = ["Finished Processing"]
    if last_message:
        message_lines.append(str(last_message).strip())

    send_notification(
        title="Codex",
        message="\n".join(message_lines).strip(),
        send_local=False,
        agent_session_id_override=agent_session_id or None,
    )


def main() -> None:
    try:
        input_data = _load_payload()
        handle_notification(input_data)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON input: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
