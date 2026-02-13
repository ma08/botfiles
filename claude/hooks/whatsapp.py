"""
Shim to shared WhatsApp notification utilities.
"""
from __future__ import annotations

import sys
from pathlib import Path


_UTILS_DIR = Path(__file__).resolve().parents[2] / "utils"
if str(_UTILS_DIR) not in sys.path:
    sys.path.insert(0, str(_UTILS_DIR))

from notify_utils import send_whatsapp_message  # noqa: E402

__all__ = ["send_whatsapp_message"]
