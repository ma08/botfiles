#!/usr/bin/env python3
"""
CLI tool to send messages to the developer via WhatsApp.
Used by the message-developer skill.

Usage:
    uv run python send.py "Your message here"
    uv run python send.py --title "Monitoring Update" "Ralph loop finished, 12/12 tasks done"
    echo "Blocker found" | uv run python send.py --title "BLOCKER"
"""
import argparse
import os
import sys

from utils import load_env
from whatsapp import send_whatsapp_message

load_env()


def main():
    parser = argparse.ArgumentParser(description="Send a message to the developer")
    parser.add_argument("message", nargs="*", help="Message text (or pipe via stdin)")
    parser.add_argument("--title", default="Claude Code", help="Message title/header")
    args = parser.parse_args()

    if args.message:
        message = " ".join(args.message)
    elif not sys.stdin.isatty():
        message = sys.stdin.read().strip()
    else:
        print("Error: No message provided", file=sys.stderr)
        sys.exit(1)

    if not message:
        print("Error: Empty message", file=sys.stderr)
        sys.exit(1)

    token = os.getenv("WHATSAPP_TOKEN", "")
    phone_number_id = os.getenv("PHONE_NUMBER_ID", "")
    notify_phone = os.getenv("NOTIFY_PHONE_NUMBER", "")
    system_name = os.getenv("SYSTEM_NAME", "") or "Unknown"

    if not all([token, phone_number_id, notify_phone]):
        print("Error: Missing WhatsApp config in .env", file=sys.stderr)
        sys.exit(1)

    formatted = f"[{system_name}]\n{args.title}\n{message}"
    success = send_whatsapp_message(
        message=formatted,
        to_phone=notify_phone,
        token=token,
        phone_number_id=phone_number_id,
    )

    if success:
        print("Message sent")
    else:
        print("Failed to send message", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
