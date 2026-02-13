"""
Notification hook for Codex CLI.
Expects a JSON payload as argv[1] per Codex config notifications.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


_UTILS_DIR = Path(__file__).resolve().parents[2] / "utils"
if str(_UTILS_DIR) not in sys.path:
    sys.path.insert(0, str(_UTILS_DIR))

from notify_utils import send_notification  # noqa: E402


def _load_payload() -> dict:
    if len(sys.argv) > 1:
        raw = sys.argv[1]
        return json.loads(raw)
    if not sys.stdin.isatty():
        return json.load(sys.stdin)
    raise ValueError("No JSON payload provided to codex_notification.py")


def handle_notification(input_data: dict) -> None:
    event_type = input_data.get("type", "")
    if event_type and event_type != "agent-turn-complete":
        return

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
