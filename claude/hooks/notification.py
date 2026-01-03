"""
Notification hook for claude code
https://docs.anthropic.com/en/docs/claude-code/hooks-guide
"""
import json
import sys

from utils import send_notification


def handle_notification(input_data: dict) -> None:
    """Handle notification event by sending notification with the message."""
    message = input_data.get("message", "")
    send_notification(
        title="Claude Code",
        message=f"Awaiting Your Input\n{message}",
    )

def main():
    try:
        input_data = json.load(sys.stdin)
        handle_notification(input_data)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON input: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
