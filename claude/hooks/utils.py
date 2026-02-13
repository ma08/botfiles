"""
Shim to shared notification utilities for Claude Code hooks.
"""
from __future__ import annotations

import sys
from pathlib import Path


_UTILS_DIR = Path(__file__).resolve().parents[2] / "utils"
if str(_UTILS_DIR) not in sys.path:
    sys.path.insert(0, str(_UTILS_DIR))

from notify_utils import (  # noqa: E402
    get_config,
    get_latest_message_from_transcript,
    get_system_name,
    load_env,
    send_local_notification,
    send_notification,
    send_whatsapp_message,
)

__all__ = [
    "get_config",
    "get_latest_message_from_transcript",
    "get_system_name",
    "load_env",
    "send_local_notification",
    "send_notification",
    "send_whatsapp_message",
]
