"""
PreToolUse hook for claude code - notifies when AskUserQuestion is used.
https://docs.anthropic.com/en/docs/claude-code/hooks-guide
"""
import json
import sys

from utils import send_notification


def _resolve_working_directory(input_data: dict) -> str | None:
    for key in ("cwd", "working_directory", "workdir"):
        value = input_data.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def handle_pretooluse(input_data: dict) -> None:
    """Handle PreToolUse event by sending notification."""
    tool_name = input_data.get("tool_name", "Unknown")

    # Extract first question if available
    tool_input = input_data.get("tool_input", {})
    questions = tool_input.get("questions", [])

    if questions and len(questions) > 0:
        first_question = questions[0].get("question", "")
        message = f"Question: {first_question[:200]}"
    else:
        message = "Claude is asking a question"

    send_notification(
        title="Claude Code",
        message=f"Awaiting Your Input\n{message}",
        coding_agent_override="claude",
        working_directory_override=_resolve_working_directory(input_data),
    )


def main():
    try:
        input_data = json.load(sys.stdin)
        handle_pretooluse(input_data)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON input: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
