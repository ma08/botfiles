#!/usr/bin/env python3
"""
CLI tool for Codex to send proactive notifications to the developer.

Usage:
    python send.py "Your message here"
    python send.py --title "BLOCKER" "Need credentials to continue"
    echo "Monitoring complete" | python send.py --title "Task Complete"
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


_UTILS_DIR = Path(__file__).resolve().parents[2] / "utils"
if str(_UTILS_DIR) not in sys.path:
    sys.path.insert(0, str(_UTILS_DIR))

from notify_utils import send_notification  # noqa: E402


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Send a message to the developer")
    parser.add_argument("message", nargs="*", help="Message text (or pipe via stdin)")
    parser.add_argument("--title", default="Codex", help="Message title/header")
    return parser.parse_args()


def _resolve_message(parts: list[str]) -> str:
    if parts:
        return " ".join(parts).strip()
    if not sys.stdin.isatty():
        return sys.stdin.read().strip()
    return ""


def main() -> int:
    args = _parse_args()
    message = _resolve_message(args.message)

    if not message:
        print("Error: No message provided", file=sys.stderr)
        return 1

    send_notification(title=args.title, message=message, send_local=False)
    print("Notification attempted")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
