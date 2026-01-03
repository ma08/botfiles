"""
This is the stop hook for claude code
https://docs.anthropic.com/en/docs/claude-code/hooks-guide
"""
import json
import sys

from utils import get_latest_message_from_transcript, send_notification


def handle_stop(input_data: dict) -> None:
    """Handle stop event by sending notification with latest message."""
    transcript_path = input_data.get("transcript_path", "")
    latest_message = get_latest_message_from_transcript(transcript_path) if transcript_path else ""

    send_notification(
        title="Claude Code",
        message=f"Finished Processing\n{latest_message}",
    )



def main():
    try:
        input_data = json.load(sys.stdin)
        handle_stop(input_data)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON input: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()